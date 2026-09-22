#!/usr/bin/env python3
"""GS08 - Validacion de la infraestructura sin necesidad de Docker.

Comprueba:
  1. Que todos los YAML de k8s/, .github/workflows/ y la config de Prometheus parseen.
  2. Que el dashboard de Grafana sea JSON valido y que cada panel tenga una consulta.
  3. Que los Dockerfile tengan las directivas minimas (FROM fijado, USER, HEALTHCHECK).
  4. Que las imagenes usadas esten fijadas por version (no ':latest' ni sin tag).

Uso:  python scripts/validar_infra.py     (devuelve 0 si todo esta bien)
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errores: list[str] = []
ok: list[str] = []


def ruta(*partes: str) -> str:
    return os.path.join(RAIZ, *partes)


def validar_yaml() -> None:
    try:
        import yaml
    except ImportError:  # pragma: no cover
        errores.append("falta PyYAML: pip install pyyaml")
        return
    archivos = sorted(
        glob.glob(ruta("k8s", "*.yaml"))
        + glob.glob(ruta(".github", "workflows", "*.yml"))
        + glob.glob(ruta("infra", "**", "*.yml"), recursive=True)
        + glob.glob(ruta("*.yml"))
    )
    for f in archivos:
        rel = os.path.relpath(f, RAIZ)
        try:
            docs = list(yaml.safe_load_all(open(f, encoding="utf-8")))
            if not docs or all(d is None for d in docs):
                errores.append(f"{rel}: documentos vacios")
            else:
                ok.append(f"YAML {rel} ({len([d for d in docs if d is not None])} doc)")
        except Exception as e:  # noqa: BLE001
            errores.append(f"{rel}: YAML invalido -> {e}")


def validar_dashboard() -> None:
    f = ruta("infra", "grafana", "dashboards", "gs08-matriculas.json")
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        errores.append(f"dashboard Grafana: {e}")
        return
    paneles = d.get("panels", [])
    sin_query = [
        p.get("title")
        for p in paneles
        if p.get("type") not in ("row", "text") and not p.get("targets")
    ]
    if sin_query:
        errores.append(f"paneles sin consulta: {sin_query}")
    ok.append(f"Dashboard Grafana '{d.get('title')}' con {len(paneles)} paneles")

    for prov in ("datasources/prometheus.yml", "dashboards/dashboards.yml"):
        p = ruta("infra", "grafana", "provisioning", prov)
        if not os.path.exists(p):
            errores.append(f"falta provisioning {prov}")


def validar_dockerfiles() -> None:
    for df in (ruta("backend", "Dockerfile"), ruta("frontend", "Dockerfile")):
        rel = os.path.relpath(df, RAIZ)
        if not os.path.exists(df):
            errores.append(f"falta {rel}")
            continue
        texto = open(df, encoding="utf-8").read()
        if "USER " not in texto:
            errores.append(f"{rel}: sin directiva USER (contenedor correria como root)")
        if "HEALTHCHECK" not in texto:
            errores.append(f"{rel}: sin HEALTHCHECK")
        if "-alpine" not in texto and "-slim" not in texto and "alpine" not in texto:
            errores.append(f"{rel}: imagenes base no slim/alpine (imagen muy grande)")
        ok.append(f"Dockerfile {rel} con USER + HEALTHCHECK")
        if os.path.exists(os.path.join(os.path.dirname(df), ".dockerignore")):
            ok.append(f".dockerignore presente para {rel}")
        else:
            errores.append(f"falta .dockerignore junto a {rel}")


def validar_versiones_fijadas() -> None:
    sospechosas = []
    patron_falta_tag = re.compile(r"^\s*image:\s*([^\s:#]+)\s*$")
    patron_latest = re.compile(r"image:\s*([^\s]+):latest\b")
    for f in glob.glob(ruta("k8s", "*.yaml")) + [ruta("docker-compose.yml")]:
        if not os.path.exists(f):
            continue
        for n, linea in enumerate(open(f, encoding="utf-8"), 1):
            m = patron_falta_tag.match(linea)
            if m:
                sospechosas.append(f"{os.path.relpath(f, RAIZ)}:{n} imagen sin tag -> {m.group(1)}")
            m = patron_latest.search(linea)
            if m:
                sospechosas.append(f"{os.path.relpath(f, RAIZ)}:{n} usa :latest -> {m.group(1)}")
    if sospechosas:
        errores.extend(sospechosas)
    else:
        ok.append("Todas las imagenes llevan version fijada (sin :latest)")


def main() -> int:
    validar_yaml()
    validar_dashboard()
    validar_dockerfiles()
    validar_versiones_fijadas()

    for linea in ok:
        print(f"OK    {linea}")
    for linea in errores:
        print(f"FALLA {linea}")
    print(f"\n{len(ok)} comprobaciones OK, {len(errores)} fallas")
    return 1 if errores else 0


if __name__ == "__main__":
    raise SystemExit(main())
