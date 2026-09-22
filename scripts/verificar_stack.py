#!/usr/bin/env python3
"""GS08 - Verificacion del stack en marcha (lo corre @qa y tambien el CI).

Comprueba contra los contenedores levantados:
  1. nginx responde en /healthz y sirve el SPA.
  2. /health del API responde y confirma conexion a PostgreSQL.
  3. /metrics expone http_requests_total.
  4. nginx reparte la carga entre las dos instancias del API (round-robin).
  5. Prometheus tiene todos los targets en 'up'.
  6. Cada consulta del dashboard de Grafana devuelve datos.

Uso:  python scripts/verificar_stack.py          (desde la raiz del repo)
      python scripts/verificar_stack.py --sin-obs  (sin Prometheus/Grafana)
Salida: reporte por consola y codigo de salida 0 si todo esta OK.
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

WEB = os.getenv("WEB_URL", "http://localhost:8080")
API = os.getenv("API_URL", "http://localhost:8000")
PROM = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
GRAF = os.getenv("GRAFANA_URL", "http://localhost:3000")
GRAF_USER = os.getenv("GRAFANA_ADMIN_USER", "admin")
GRAF_PASS = os.getenv("GRAFANA_ADMIN_PASSWORD", "gs08_grafana")
DASHBOARD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "infra", "grafana", "dashboards", "gs08-matriculas.json")
# Endpoint que se usa para comprobar el balanceo (debe existir en el API)
RR_PATH = os.getenv("RR_PATH", "/api/v1/estudiantes")

fallas: list[str] = []
ok: list[str] = []


def http(url: str, auth: str | None = None, timeout: int = 15) -> tuple[int, str]:
    req = urllib.request.Request(url)
    if auth:
        req.add_header("Authorization", f"Basic {auth}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def check(nombre: str, condicion: bool, detalle: str) -> None:
    (ok if condicion else fallas).append(f"{nombre}: {detalle}")


# 1. nginx + SPA
codigo, cuerpo = http(f"{WEB}/healthz")
check("nginx /healthz", codigo == 200 and "ok" in cuerpo, f"HTTP {codigo} -> {cuerpo.strip()[:40]!r}")
codigo, cuerpo = http(f"{WEB}/")
check("SPA en /", codigo == 200 and "<html" in cuerpo.lower(), f"HTTP {codigo}, {len(cuerpo)} bytes")

# 2. API + PostgreSQL
for etiqueta, base in (("API directa", API), ("via nginx", f"{WEB}/api/v1")):
    codigo, cuerpo = http(f"{base}/health")
    es_ok = codigo == 200 and '"status":"ok"' in cuerpo.replace(" ", "")
    check(f"/health {etiqueta}", es_ok, f"HTTP {codigo} -> {cuerpo.strip()[:120]}")

# 3. metricas
codigo, cuerpo = http(f"{API}/metrics")
check("/metrics", codigo == 200 and "http_requests_total" in cuerpo,
      "expone http_requests_total" if codigo == 200 else f"HTTP {codigo}")

# 4. round-robin de nginx (se usa la cabecera X-Upstream-Addr)
upstreams: dict[str, int] = {}
for _ in range(12):
    req = urllib.request.Request(f"{WEB}{RR_PATH}")
    with urllib.request.urlopen(req, timeout=15) as r:
        addr = r.headers.get("X-Upstream-Addr", "-")
    upstreams[addr] = upstreams.get(addr, 0) + 1
check("balanceo nginx", len(upstreams) >= 2, f"reparto entre {len(upstreams)} instancias: {upstreams}")

# 5 y 6. observabilidad
if "--sin-obs" not in sys.argv:
    auth = base64.b64encode(f"{GRAF_USER}:{GRAF_PASS}".encode()).decode()
    try:
        d = json.loads(http(f"{PROM}/api/v1/targets")[1])["data"]["activeTargets"]
        caidos = [f"{t['labels'].get('job')}/{t['labels'].get('instancia', '-')}" for t in d if t["health"] != "up"]
        check("targets Prometheus", not caidos, f"{len(d)} targets, caidos: {caidos or 'ninguno'}")
    except Exception as e:  # noqa: BLE001
        check("targets Prometheus", False, f"no se pudo consultar: {e}")

    try:
        dash = json.load(open(DASHBOARD, encoding="utf-8"))
        sin_datos = []
        for panel in dash["panels"]:
            if panel.get("type") in ("row", "text"):
                continue
            for t in panel.get("targets", []):
                expr = t["expr"].replace("$instancia", ".*").replace("$__rate_interval", "5m")
                q = urllib.parse.urlencode({"query": expr})
                res = json.loads(http(f"{PROM}/api/v1/query?{q}")[1]).get("data", {}).get("result", [])
                if not res:
                    sin_datos.append(panel["title"])
        check("paneles Grafana con datos", not sin_datos,
              f"{len([p for p in dash['panels'] if p.get('type') not in ('row', 'text')])} paneles revisados, sin datos: {sin_datos or 'ninguno'}")
        codigo, cuerpo = http(f"{GRAF}/api/dashboards/uid/{dash['uid']}", auth)
        check("dashboard provisionado", codigo == 200 and dash["uid"] in cuerpo, f"HTTP {codigo} en {GRAF}/d/{dash['uid']}")
    except Exception as e:  # noqa: BLE001
        check("Grafana", False, f"no se pudo verificar: {e}")

print("=" * 72)
for linea in ok:
    print(f"OK    {linea}")
for linea in fallas:
    print(f"FALLA {linea}")
print("=" * 72)
print(f"{len(ok)} comprobaciones OK, {len(fallas)} fallas")
raise SystemExit(1 if fallas else 0)
