# GS08 - Matriculas y Notas | Evidencia real del Sprint 0 (infraestructura)

**Autor:** @devops · **Fecha de ejecucion:** 21/09/2026 · **Maquina:** ASUS M1502YA (Windows 11, Docker Desktop)
**Uso:** este archivo es la fuente citable para `docs/manual-tecnico.md`, `docs/arquitectura.md` y
`docs/actas/acta-sprint-0.md`. Cada fila trae el **comando exacto** y la **salida real** (recortada,
sin inventar nada). El analisis y las decisiones estan en `docs/devops/plan-contenedores-ci.md`;
el runbook operativo, en `docs/devops/COMANDOS.md`.

> Nota metodologica: el stack se probo con un stub minimo de API y SPA
> (`D:\dev\_tmp\gs08-smoke`, copia del `docker-compose.yml`, los `Dockerfile` y la config del repo)
> para validar la infraestructura antes de que exista el codigo de @dev. Toda salida de este archivo
> es de contenedores reales corriendo en esta maquina.

---

## 1. Entorno (contra el supuesto de que no habia Docker)

| Comando | Salida real |
|---|---|
| `docker --version` | `Docker version 29.8.0, build 88096ef` |
| `docker compose version` | `Docker Compose version v5.5.1` |
| `docker info --format '{{.ServerVersion}} \| {{.OSType}} \| {{.Driver}} \| Mem={{.MemTotal}}'` | `29.8.0 \| linux \| overlayfs \| Mem=12223930368` |
| `kubectl version --client` | `Client Version: v1.36.1`, `Kustomize Version: v5.8.1` |
| `kubectl config current-context` | `error: current-context is not set` (no hay cluster) |
| `which minikube kind k3d k3s` | ninguno instalado |
| `git --version` / `git log --oneline -3` | `2.54.0.windows.1` / `c946d81`, `8d9b3bd`, `9ef7c26` (rama `main`) |

## 2. El stack completo levanta y queda sano

| Comando | Salida real |
|---|---|
| `docker compose config -q && docker compose config --services` | `db`, `api`, `api-b`, `web` (con `--profile obs` se suman `prometheus`, `grafana`) |
| `docker compose --profile obs ps` | 6 contenedores: `gs08-web` (healthy, 0.0.0.0:8080->8080), `gs08-api` (healthy, 8000), `gs08-api-b` (healthy), `gs08-db` (healthy, 5432), `gs08-prometheus` (9090), `gs08-grafana` (3000) |
| `curl -i http://localhost:8080/healthz` | `HTTP/1.1 200 OK` … cuerpo `ok` |
| `curl http://localhost:8000/health` | `{"status":"ok","motor":"PostgreSQL 16.15 on x86_64-pc-linux-musl","instancia":"ca662ba8ec69"}` |
| `curl http://localhost:8080/api/v1/estudiantes` | `{"total_mostrado":3,"estudiantes":[{"codigo":"E20260001",...}]}` (consulta a PostgreSQL pasando por nginx) |

Evidencia automatizada: `python scripts/verificar_stack.py`

```
OK    nginx /healthz: HTTP 200 -> 'ok'
OK    SPA en /: HTTP 200, 371 bytes
OK    /health API directa: HTTP 200 -> {"status":"ok","motor":"PostgreSQL 16.15 ..."}
OK    /health via nginx: HTTP 200 -> {"status":"ok","motor":"PostgreSQL 16.15 ..."}
OK    /metrics: expone http_requests_total
OK    balanceo nginx: reparto entre 2 instancias: {'172.18.0.6:8000': 6, '172.18.0.5:8000': 6}
OK    targets Prometheus: 3 targets, caidos: ninguno
OK    paneles Grafana con datos: 9 paneles revisados, sin datos: ninguno
OK    dashboard provisionado: HTTP 200 en http://localhost:3000/d/gs08-matriculas
9 comprobaciones OK, 0 fallas
```

## 3. Balanceo de carga y failover (nginx con 2 instancias)

```
$ for i in $(seq 1 12); do curl -s -o /dev/null -D - http://localhost:8080/api/v1/estudiantes | grep -i x-upstream-addr; done
X-Upstream-Addr: 172.18.0.5:8000     <- gs08-api
X-Upstream-Addr: 172.18.0.6:8000     <- gs08-api-b
(alterna 1 a 1 las 12 peticiones)

$ docker stop gs08-api-b && curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/api/v1/estudiantes
200
X-Upstream-Addr: 172.18.0.6:8000, 172.18.0.5:8000    <- intento fallido en api-b y reintento en api
```

## 4. Observabilidad (Prometheus + Grafana)

```
$ curl -X POST http://localhost:9090/-/reload            -> HTTP 200
targets:  gs08-api/instancia=api -> up | gs08-api/instancia=api-b -> up | prometheus -> up
consultas de los paneles con trafico real (20 OK, 4 errores 500 forzados, 6 peticiones 404):
  req/s total           -> 0.517
  errores 5xx %         -> 3.12
  errores 4xx %         -> 8.13
  latencia p95          -> 0.095 s
  trafico por instancia -> 2 series
  top 5 endpoints       -> 5 series
  p95 por endpoint      -> 5 series
Grafana 12.4.11: health ok | datasource Prometheus (default) | dashboard "GS08 - Matriculas y Notas | API RED"
(uid=gs08-matriculas, carpeta "GS08 Matriculas", 9 paneles con datos)
Prueba de provisioning: al cambiar el titulo en infra/grafana/dashboards/gs08-matriculas.json,
Grafana lo reflejo en 30 s (version 2 -> 3): el archivo ES la fuente del dashboard.
```

Que mide cada panel: `docs/devops/plan-contenedores-ci.md` seccion 5 (y panel 10 del propio dashboard).

## 5. Kubernetes (manifiestos entregados, sin cluster para aplicarlos)

```
$ kubectl kustomize k8s/
11 objetos: Namespace gs08 | ConfigMap gs08-config | PVC gs08-pgdata | Job gs08-migraciones
            Deployment gs08-db, gs08-api, gs08-web | Service gs08-db, gs08-api, gs08-web | Ingress gs08
```

Pendiente y sin evidencia a proposito: `kubectl get pods`, Ingress con `gs08.local` y despliegue
desde CD. Los comandos estan listos en `docs/devops/COMANDOS.md` seccion 5.

## 6. Validacion de infra sin Docker (lo que corre el CI)

```
$ python scripts/validar_infra.py
OK    YAML .github/workflows/cd.yml (1 doc)  ... 15 archivos YAML ...
OK    Dashboard Grafana 'GS08 - Matriculas y Notas | API RED' con 11 paneles
OK    Dockerfile backend/Dockerfile con USER + HEALTHCHECK
OK    Dockerfile frontend/Dockerfile con USER + HEALTHCHECK
OK    Todas las imagenes llevan version fijada (sin :latest)
21 comprobaciones OK, 0 fallas
```

Imagenes fijadas: `postgres:16.15-alpine3.24`, `python:3.12.14-slim-bookworm`, `node:22.23.2-alpine`,
`nginx:1.31.6-alpine`, `prom/prometheus:v3.13.3`, `grafana/grafana:12.4.11`.

## 7. Integracion: imagen del API (@devops) contra el esquema de @analista

Comando (ejecutado el 21/09/2026, usa la base desechable de @analista, sin tocar datos):

```
docker run --rm -e DATABASE_URL="postgresql+psycopg://gs08:***@172.17.0.2:5432/gs08_matriculas" \
  -v "D:/dev/_tmp/gs08-integracion.py:/verif.py:ro" gs08-api:local python /verif.py
```

```
servidor: PostgreSQL 16.15 on x86_64-pc-linux-musl
tablas visibles para el API: ['cursos', 'estudiantes', 'matriculas', 'usuarios']
vistas visibles para el API: ['v_matriculas_detalle']
  filas en cursos: 7 | filas en estudiantes: 12 | filas en matriculas: 24 | filas en usuarios: 1
muestra de v_matriculas_detalle: "Ramirez Torres, Carlos Alberto | Matematica Basica | 2026-02 | activa"
  (los acentos salen correctos en UTF-8)
pruebas de reglas (todas rechazadas por la base, como debe ser):
  matricula duplicada  -> UniqueViolation: uq_matriculas_estudiante_curso_periodo
  dni de 3 digitos     -> CheckViolation: ck_estudiantes_dni
  creditos = 99        -> CheckViolation: ck_cursos_creditos
  periodo '2026/02'    -> CheckViolation: ck_matriculas_periodo
```

Conclusion: la imagen del API del `backend/Dockerfile` conecta con el esquema traducido de
`db/init/*.sql` y las 4 reglas de negocio estan vivas **en la base** (no solo en el codigo).

## 8. Correcciones hechas a partir de las pruebas (importantes para la retrospectiva)

| Hallazgo | Evidencia | Correccion |
|---|---|---|
| Round-robin desparejo (todo a una instancia) | 6 peticiones seguidas con la misma `X-Upstream-Addr` | `zone gs08_api 64k;` en el upstream de `frontend/nginx/default.conf.template` |
| Sin reintento al caer una instancia | `X-Upstream-Addr: .6, .5` con codigo 200 | `max_fails=3 fail_timeout=10s` + `proxy_next_upstream error timeout` |
| `http_requests_inprogress` no existe en prometheus-fastapi-instrumentator 8.1.0 | `dir(metrics)` en el contenedor: `['combined_size','default','latency','request_size','response_size','requests',...]` | Panel 4 del dashboard reemplazado por "Errores 4xx (%)" |
| Job de Prometheus hacia nginx en `down` | `lastError: expected value after metric, got "\n" ("INVALID")` | Job eliminado; nginx necesita su exporter (Sprint 1) |
| `frontend/Dockerfile` dejaba nginx como root | `scripts/validar_infra.py` lo marcaba como FALLA | `USER nginx` + escucha en 8080 + directorios escribibles |
| `kubectl apply --dry-run=client` no valida sin cluster | `failed to download openapi` | La validacion offline es `kubectl kustomize k8s/` |
