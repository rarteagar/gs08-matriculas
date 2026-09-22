#!/usr/bin/env python3
"""GS08 - Verificacion del stack en marcha (lo corre @qa y tambien el CI).

Comprueba contra los contenedores levantados:
  1. nginx responde en /healthz, sirve el SPA y NO confunde /health y /metrics con el SPA.
  2. /health del API responde y confirma conexion a PostgreSQL (directo y por el proxy).
  3. /metrics expone http_requests_total.
  4. nginx reparte la carga entre las dos instancias del API (round-robin).
  5. Prometheus tiene todos los targets en 'up'.
  6. Cada consulta del dashboard de Grafana queda en estado conocido.

Regla de resultado (BUG-01 / D-19):
  * FALLA         -> algo que debe funcionar y no funciona (health, SPA, metricas, targets,
                     balanceo, o una consulta del dashboard que Prometheus RECHAZA).
  * ADVERTENCIA   -> panel sin serie todavia (p. ej. 5xx en 0 durante una demo limpia). NO
                     rompe el criterio: los paneles 1 y 2 (disponibilidad y trafico) si son
                     obligatorios, porque cualquier peticion al API los alimenta.
  * El script sale con 0 si no hay FALLAS, aunque haya advertencias.

Uso:  python scripts/verificar_stack.py          (desde la raiz del repo)
      python scripts/verificar_stack.py --sin-obs  (sin Prometheus/Grafana)
Variables: WEB_URL, API_URL, PROMETHEUS_URL, GRAFANA_URL, GRAFANA_ADMIN_USER,
           GRAFANA_ADMIN_PASSWORD, RR_PATH
"""
from __future__ import annotations

import base64
import json
import os
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
# Endpoint que se usa para comprobar el balanceo y los headers del proxy
# (publico, sin token: es el mismo que usa el criterio C-35)
RR_PATH = os.getenv("RR_PATH", "/api/v1/health")
# Paneles que NO pueden quedarse sin datos: disponibilidad y trafico
PANELES_OBLIGATORIOS = {1, 2}

fallas: list[str] = []
advertencias: list[str] = []
ok: list[str] = []


def http(url: str, auth: str | None = None, timeout: int = 15) -> tuple[int, str, dict]:
    req = urllib.request.Request(url)
    if auth:
        req.add_header("Authorization", f"Basic {auth}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace"), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), dict(e.headers)


def check(nombre: str, condicion: bool, detalle: str) -> None:
    (ok if condicion else fallas).append(f"{nombre}: {detalle}")


def advertir(nombre: str, detalle: str) -> None:
    advertencias.append(f"{nombre}: {detalle}")


# 1. nginx + SPA
codigo, cuerpo, _ = http(f"{WEB}/healthz")
check("nginx /healthz", codigo == 200 and "ok" in cuerpo, f"HTTP {codigo} -> {cuerpo.strip()[:40]!r}")
codigo, cuerpo, _ = http(f"{WEB}/")
check("SPA en /", codigo == 200 and "<html" in cuerpo.lower(), f"HTTP {codigo}, {len(cuerpo)} bytes")

# 1b. las rutas de monitoreo no deben devolver el SPA (D-17 / BUG-05 / TC-03):
#     el SPA cae en el try_files y responde 200 con index.html, asi que el
#     discriminador es el codigo: 404 = nginx no las enruta al SPA.
for ruta in ("/health", "/metrics"):
    codigo, cuerpo, headers = http(f"{WEB}{ruta}")
    check(f"{ruta} por el proxy", codigo == 404,
          f"HTTP {codigo} ({headers.get('Content-Type', '-')}, {len(cuerpo)} bytes) -> se espera 404")

# 2. API + PostgreSQL
for etiqueta, base in (("API directa", API), ("via nginx", f"{WEB}/api/v1")):
    codigo, cuerpo, _ = http(f"{base}/health")
    es_ok = codigo == 200 and '"status":"ok"' in cuerpo.replace(" ", "")
    check(f"/health {etiqueta}", es_ok, f"HTTP {codigo} -> {cuerpo.strip()[:120]}")

# 2b. headers de seguridad en las respuestas del API (BUG-06 / TC-02)
codigo, cuerpo, headers = http(f"{WEB}/api/v1/health")
faltan = [h for h in ("X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy", "X-Upstream-Addr")
          if h.lower() not in {k.lower() for k in headers}]
check("headers de /api/", not faltan, f"HTTP {codigo}, headers presentes, faltan: {faltan or 'ninguno'}")

# 3. metricas (directo del API: por el balanceador se mezclarian las 2 instancias)
codigo, cuerpo, _ = http(f"{API}/metrics")
check("/metrics en el API", codigo == 200 and "http_requests_total" in cuerpo,
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
        evaluados = sin_serie = rechazados = 0
        detalle_sin_serie: list[str] = []
        detalle_rechazado: list[str] = []
        obligatorio_vacio: list[str] = []
        for panel in dash["panels"]:
            if panel.get("type") in ("row", "text"):
                continue
            evaluados += 1
            for t in panel.get("targets", []):
                expr = t["expr"].replace("$instancia", ".*").replace("$__rate_interval", "5m")
                q = urllib.parse.urlencode({"query": expr})
                resp = json.loads(http(f"{PROM}/api/v1/query?{q}")[1])
                if resp.get("status") != "success":
                    rechazados += 1
                    detalle_rechazado.append(f"{panel['title']} ({resp.get('error', 'error')[:60]})")
                    continue
                if not resp.get("data", {}).get("result"):
                    sin_serie += 1
                    if panel.get("id") in PANELES_OBLIGATORIOS:
                        obligatorio_vacio.append(panel["title"])
                    else:
                        detalle_sin_serie.append(panel["title"])

        check("consultas de Grafana validas", rechazados == 0,
              f"{evaluados} paneles, rechazadas: {detalle_rechazado or 'ninguna'}")
        check("paneles obligatorios con datos", not obligatorio_vacio,
              f"vacios: {obligatorio_vacio or 'ninguno'} (ids {sorted(PANELES_OBLIGATORIOS)})")
        if detalle_sin_serie:
            advertir("paneles sin serie todavia",
                     f"{len(detalle_sin_serie)} de {evaluados} (no rompen el criterio, D-19): {detalle_sin_serie}")
        else:
            ok.append(f"paneles Grafana: {evaluados} evaluados, todos con datos")
        codigo, cuerpo, _ = http(f"{GRAF}/api/dashboards/uid/{dash['uid']}", auth)
        check("dashboard provisionado", codigo == 200 and dash["uid"] in cuerpo, f"HTTP {codigo} en {GRAF}/d/{dash['uid']}")
    except Exception as e:  # noqa: BLE001
        check("Grafana", False, f"no se pudo verificar: {e}")

print("=" * 72)
for linea in ok:
    print(f"OK          {linea}")
for linea in advertencias:
    print(f"ADVERTENCIA {linea}")
for linea in fallas:
    print(f"FALLA       {linea}")
print("=" * 72)
print(f"{len(ok)} comprobaciones OK, {len(advertencias)} advertencias, {len(fallas)} fallas")
raise SystemExit(1 if fallas else 0)
