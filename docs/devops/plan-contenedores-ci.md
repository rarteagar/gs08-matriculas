# GS08 - Matriculas y Notas | Sprint 0: plan de contenedores, CI/CD y observabilidad

**Autor:** @devops · **Fecha:** 21/09/2026 · **Repo:** `D:\dev\equipo\gs08-matriculas`
**Estado:** infraestructura entregada y **probada corriendo** en esta maquina.

---

## 0. Correccion de un supuesto de partida

El encargo decia "hoy no hay Docker instalado (en tramite)". **Ya esta instalado y el demonio
esta corriendo.** Verificado:

```
$ docker --version            -> Docker version 29.8.0, build 88096ef
$ docker compose version      -> Docker Compose version v5.5.1
$ docker info --format '{{.ServerVersion}} | {{.OSType}} | {{.Driver}} | Mem={{.MemTotal}}'
                              -> 29.8.0 | linux | overlayfs | Mem=12223930368
$ kubectl version --client    -> Client Version: v1.36.1
```

Conclusion: **todo el plan se pudo ejecutar de verdad**, salvo lo que depende de un cluster de
Kubernetes (no hay kubeconfig: `kubectl config current-context` -> `error: current-context is not set`)
y del repositorio de GitHub (no hay remoto configurado). Nada de lo que sigue es simulado.

---

## 1. Archivos entregados

| Archivo | Rol |
|---|---|
| `backend/Dockerfile` + `backend/.dockerignore` | Imagen del API (2 etapas, usuario `app` uid 10001, HEALTHCHECK en `/health`) |
| `frontend/Dockerfile` + `frontend/.dockerignore` | Imagen del SPA (build Node 22 -> nginx 1.31, usuario `nginx`, escucha en 8080) |
| `frontend/nginx/default.conf.template` | nginx: SPA + proxy inverso `/api/` + balanceo + cabeceras de seguridad |
| `docker-compose.yml` | db + api + api-b + web; perfil `obs` con Prometheus y Grafana |
| `.env.example` | Variables con valores por defecto (compose funciona sin `.env`) |
| `db/init/README.md` | Contrato de los scripts de @analista (`01-schema.sql`, `02-view.sql`, `03-seed.sql`) |
| `infra/prometheus/prometheus.yml` | Scrape cada 15 s de las 2 instancias del API |
| `infra/grafana/provisioning/*` | Datasource Prometheus + provider de dashboards (automatico) |
| `infra/grafana/dashboards/gs08-matriculas.json` | Dashboard "API RED" con 9 paneles con datos |
| `k8s/*.yaml` + `k8s/kustomization.yaml` | Namespace, ConfigMap, Secret (plantilla), PostgreSQL, Job de migraciones, API, Web, Ingress |
| `.github/workflows/ci.yml` | Validacion de infra, hadolint, ruff+pytest, eslint+vitest+build, build de imagenes + smoke |
| `.github/workflows/cd.yml` | Publica en GHCR tras CI verde y despliega en k8s (guardado por `DEPLOY_ENABLED`) |
| `scripts/validar_infra.py` | Valida YAML, dashboard, Dockerfile y versiones fijadas sin necesidad de Docker |
| `scripts/verificar_stack.py` | Verifica el stack en marcha (lo usa @qa) |
| `docs/devops/COMANDOS.md` | Runbook: levantar, logs, observabilidad, k8s, problemas frecuentes |

Todas las imagenes estan **fijadas por version** (nada de `:latest`), comprobado por
`scripts/validar_infra.py`: `postgres:16.15-alpine3.24`, `python:3.12.14-slim-bookworm`,
`node:22.23.2-alpine`, `nginx:1.31.6-alpine`, `prom/prometheus:v3.13.3`, `grafana/grafana:12.4.11`.

---

## 2. Arquitectura de contenedores

```
                        host (Windows + Docker Desktop)
   QA / navegador            8080              8000           5432       9090      3000
        |                      |                 |              |          |         |
        v                      v                 v              v          v         v
 +--------------+      +-----------------+   +---------+   +---------+  +-----------+ +---------+
 |  gs08-web    |      |                 |   |         |   |         |  | gs08-     | | gs08-   |
 | nginx (SPA)  |----->| upstream gs08_api (round-robin) |-->|  gs08-  |  | prometheus| | grafana |
 | usuario      | /api/|  server api:8000|   | gs08-api|   |  db     |  | scrape    | | dashboard
 | nginx, :8080 |      |  server api-b   |   | gs08-api-b| | postgres|  | 15 s      | | RED     |
 +--------------+      +-----------------+   +---------+   +---------+  +-----------+ +---------+
        red docker: gs08-net          volumenes: pgdata, prometheus_data, grafana_data
```

- **Un solo comando** levanta la aplicacion: `docker compose up -d --build` (db + api + api-b + web).
- **Dos instancias del API** a proposito: es lo que permite demostrar el balanceo de nginx y la
  tolerancia a la caida de una instancia (requisito del curso).
- **Perfil `obs`** aparte (`docker compose --profile obs up -d`) para Prometheus + Grafana: el
  arranque normal de la app no arrastra 1.5 GB de imagenes de observabilidad.

---

## 3. Contrato con @dev (lo que el codigo debe cumplir para que esto funcione)

| Punto | Requisito |
|---|---|
| Ruta del API | `GET /health` -> 200 `{"status":"ok"}` comprobando PostgreSQL; `GET /api/v1/health` -> lo mismo (para entrar por nginx) |
| Metricas | `GET /metrics` en formato Prometheus via `prometheus-fastapi-instrumentator==8.1.0` |
| Puerto | uvicorn en `0.0.0.0:8000` (el CMD de la imagen ya lo hace) |
| Variables | `DATABASE_URL` (ya la inyecta compose), `SECRET_KEY`, `ENVIRONMENT`, `LOG_LEVEL` |
| Dependencias | `backend/requirements.txt` con versiones fijadas. Verificadas contra PyPI el 21/09/2026: `fastapi==0.141.1`, `uvicorn==0.53.0`, `SQLAlchemy==2.0.54`, `psycopg[binary]==3.3.6`, `prometheus-fastapi-instrumentator==8.1.0`, `pydantic-settings==2.15.0`, `alembic==1.20.0` |
| Frontend | `frontend/package.json` con `build` que genere `dist/`, y **`package-lock.json` commiteado** (`npm ci` lo exige) |
| Dev deps | `requirements-dev.txt` con `ruff`, `pytest`, `pytest-cov`; scripts npm `lint` y `test:unit` |
| Rutas de trabajo | `backend/app/main.py` (el Dockerfile hace `uvicorn app.main:app`) |
| Migraciones | Alembic en `backend/alembic/`; en el cluster corre el Job `gs08-migraciones` |

Ojo con la primera migracion: `db/init/*.sql` corre **una sola vez** al crear el volumen
(DDL traducido del legacy MySQL). En el cluster el DDL inicial lo aplica Alembic, no `db/init/`.

---

## 4. Evidencia de ejecucion real

### 4.1 El stack levanta y responde (smoke test completo)

Se corrio el `docker-compose.yml` **entregado** con un stub minimo (API FastAPI de 3 endpoints +
SPA de 1 archivo) para probar la infraestructura antes de que exista el codigo real.
Arnes: `D:\dev\_tmp\gs08-smoke` (copia del compose, Dockerfiles y config tal como estan en el repo).

```
$ docker compose --profile obs ps
gs08-api         Up (healthy)   0.0.0.0:8000->8000/tcp
gs08-api-b       Up (healthy)   8000/tcp
gs08-db          Up (healthy)   0.0.0.0:5432->5432/tcp
gs08-grafana     Up             0.0.0.0:3000->3000/tcp
gs08-prometheus  Up             0.0.0.0:9090->9090/tcp
gs08-web         Up (healthy)   0.0.0.0:8080->8080/tcp

$ curl -i http://localhost:8080/healthz            -> HTTP/1.1 200 OK  "ok"
$ curl http://localhost:8000/health                -> {"status":"ok","motor":"PostgreSQL 16.15 on x86_64-pc-linux-musl","instancia":"ca662ba8ec69"}
$ curl http://localhost:8080/api/v1/estudiantes    -> {"total_mostrado":3,"estudiantes":[...]}   (consulta real a PostgreSQL, pasando por nginx)
```

Verificacion automatizada (`scripts/verificar_stack.py`, corriendo ahora mismo):

```
$ python scripts/verificar_stack.py
OK    nginx /healthz: HTTP 200 -> 'ok'
OK    SPA en /: HTTP 200, 371 bytes
OK    /health API directa: HTTP 200 -> {"status":"ok","motor":"PostgreSQL 16.15 ..."}
OK    /health via nginx: HTTP 200 -> {"status":"ok","motor":"PostgreSQL 16.15 ..."}
OK    /metrics: expone http_requests_total
OK    balanceo nginx: reparto entre 2 instancias: {'172.18.0.6:8000': 6, '172.18.0.5:8000': 6}
OK    targets Prometheus: 3 targets, caidos: ninguno
OK    paneles Grafana con datos: 9 paneles revisados, sin datos: ninguno
OK    dashboard provisionado: HTTP 200 en http://localhost:3000/d/gs08-matriculas
9 comprobaciones OK, 0 fallas   (exit 0)
```

### 4.2 Balanceo de carga con nginx (12 peticiones consecutivas)

```
$ for i in $(seq 1 12); do curl -s -o /dev/null -D - http://localhost:8080/api/v1/estudiantes | grep -i x-upstream-addr; done
X-Upstream-Addr: 172.18.0.5:8000      (gs08-api)
X-Upstream-Addr: 172.18.0.6:8000      (gs08-api-b)
X-Upstream-Addr: 172.18.0.5:8000
X-Upstream-Addr: 172.18.0.6:8000
   ... alterna 1 a 1 las 12 veces ...
```

### 4.3 Tolerancia a la caida de una instancia (failover real)

```
$ docker stop gs08-api-b
$ curl -o /dev/null -w '%{http_code}' http://localhost:8080/api/v1/estudiantes   -> 200
X-Upstream-Addr: 172.18.0.6:8000, 172.18.0.5:8000     <- intento en api-b, fallo, reintento en api
$ docker start gs08-api-b   -> el reparto 1 a 1 se recupera solo
```

### 4.4 Observabilidad

```
$ curl -X POST http://localhost:9090/-/reload     -> HTTP 200
targets: gs08-api/instancia=api -> up | gs08-api/instancia=api-b -> up | prometheus -> up
consultas de los paneles (trafico real generado: 20 OK, 4 errores 500 y 6 peticiones 404):
  req/s total                -> 0.517
  errores 5xx %              -> 3.12     (los 500 forzados aparecen)
  errores 4xx %              -> 8.13     (los 404 aparecen)
  latencia p95               -> 0.095 s
  trafico por instancia      -> 2 series (api y api-b con carga parecida)
  top 5 endpoints            -> 5 series
  p95 por endpoint           -> 5 series
Grafana 12.4.11: health ok, datasource Prometheus por defecto, dashboard cargado
  "GS08 - Matriculas y Notas | API RED" (uid=gs08-matriculas, carpeta "GS08 Matriculas"), 9 paneles con datos
```

El dashboard **se provisiona solo desde el archivo** (no hay que importarlo): se cambio el titulo
en el JSON del host y Grafana lo reflejo en 30 s subiendo la version a 3 -> el archivo manda.

### 4.5 Kubernetes (sin cluster instalado)

```
$ kubectl config current-context    -> error: current-context is not set
$ which minikube kind k3d k3s       -> ninguno instalado (solo el cliente kubectl v1.36.1)
$ kubectl kustomize k8s/            -> 11 objetos generados:
   Namespace gs08 | ConfigMap gs08-config | PVC gs08-pgdata | Job gs08-migraciones
   Deployment gs08-db, gs08-api, gs08-web | Service gs08-db, gs08-api, gs08-web | Ingress gs08
```

Los manifiestos estan escritos y el render de kustomize valida. **Aplicarlos de verdad queda
pendiente de instalar minikube o k3s** (los comandos exactos estan en `docs/devops/COMANDOS.md`,
seccion 5). No voy a reportar `kubectl get pods` hasta que exista un cluster.

### 4.6 CI/CD

Los workflows estan escritos con acciones fijadas por version (checkout v7.0.1, setup-python v7.0.0,
setup-node v7.0.0, build-push-action v7.4.0, login-action v4.6.0, hadolint-action v3.5.0,
upload-artifact v7.0.1, trivy-action v0.36.0). **No pueden correr todavia**: el repo no tiene remoto
de GitHub ni credenciales. Lo que si se corrio, localmente, es el equivalente:

```
$ python scripts/validar_infra.py      -> 21 comprobaciones OK, 0 fallas   (YAML, JSON del dashboard,
                                          USER+HEALTHCHECK en los Dockerfile, versiones fijadas)
$ docker compose config -q             -> OK (sintaxis y sustitucion de variables)
```

Diseno de los pipelines:

| CI (`ci.yml`) | Detalle |
|---|---|
| `infra` | Corre **siempre**: valida YAML/dashboard/Dockerfile, `docker compose config`, hadolint |
| `backend` | ruff + pytest con cobertura minima 60% contra un contenedor PostgreSQL 16 |
| `frontend` | eslint + vitest + build de produccion (publica `dist` como artefacto) |
| `imagenes` | `docker compose build` + `up` + healthchecks + trivy (informativo) |
| `ci-ok` | Puerta unica para la proteccion de rama |
Los jobs de app se saltan con `skipped` mientras `backend/requirements.txt` y `frontend/package.json`
no existan, asi **el CI ya queda verde en el Sprint 0** (solo infraestructura).

| CD (`cd.yml`) | Detalle |
|---|---|
| Disparo | Cuando CI termina en verde sobre `main` (o a mano) |
| `publicar` | Buildx + push a GHCR con tag `sha` y `main`, con SBOM y provenance |
| `desplegar` | `kubectl apply -k k8s/`, `set image` con el tag nuevo, `rollout status`, smoke contra el Ingress y `rollout undo` si falla |
| Guarda | Solo corre con `vars.DEPLOY_ENABLED == 'true'` (hoy no existe -> se salta, el pipeline no se rompe) |

---

## 5. Observabilidad: que mide cada panel

Dashboard **"GS08 - Matriculas y Notas | API RED"** (metodo RED: Rate, Errors, Duration) en
http://localhost:3000/d/gs08-matriculas — la tabla completa tambien esta dentro del dashboard (panel 10).

| # | Panel | Que mide | Como se lee |
|---|---|---|---|
| 1 | Disponibilidad del API (up) | Si Prometheus puede leer `/metrics` de cada instancia | Todo OK = 2/2 vivas; un CAIDO con trafico en el otro demuestra que nginx y el servicio sobreviven |
| 2 | Peticiones/segundo | Carga total atendida | Base para dimensionar replicas |
| 3 | Errores 5xx (%) | Calidad del servicio | Debe ser 0; cualquier valor es bug del API o de la BD |
| 4 | Errores 4xx (%) | Rechazos por validacion/negocio (401, 404, 409) | Alto con 5xx en 0 = las reglas de negocio funcionan |
| 5 | Trafico por instancia | Balanceo de nginx | Las 2 series se mueven parejo (round-robin) |
| 6 | Latencia p50/p95/p99 | Experiencia de usuario | Criterio del MVP: p95 < 0.5 s (hoy 0.095 s con el stub) |
| 7 | Respuestas por estado | 2xx vs 4xx vs 5xx | Detecta picos de error por codigo |
| 8 | Top 5 endpoints | Uso por recurso | Prioriza indices y paginacion |
| 9 | Latencia p95 por endpoint | Endpoint mas lento | Primer candidato a optimizar |

**No hay paneles de PostgreSQL ni de nginx**: ninguno de los dos expone metricas Prometheus sin un
exporter propio. Si el tiempo alcanza, en el Sprint 1 se agregan `postgres-exporter` y
`nginx-prometheus-exporter` al perfil `obs`.

---

## 6. Puertos y URLs para @qa

| Que probar | URL |
|---|---|
| Aplicacion (SPA) | http://localhost:8080 |
| API a traves del proxy | http://localhost:8080/api/v1/... |
| Health por el proxy | http://localhost:8080/api/v1/health |
| API directa / Swagger | http://localhost:8000 , http://localhost:8000/docs |
| Metricas crudas | http://localhost:8000/metrics |
| Prometheus (targets) | http://localhost:9090/targets |
| Grafana | http://localhost:3000 (usuario `admin`, clave `gs08_grafana`) |
| PostgreSQL | `localhost:5432`, base `gs08_matriculas`, usuario `gs08`, clave `gs08_dev_pwd` |

Credenciales y puertos salen de `.env` (`.env.example` como plantilla). **Son de desarrollo local**:
antes de cualquier entrega se cambian `POSTGRES_PASSWORD` y `SECRET_KEY`.

Prueba de balanceo que @qa puede repetir en un comando (debe alternar dos IPs):

```bash
for i in $(seq 1 6); do curl -s -o /dev/null -D - http://localhost:8080/api/v1/health | grep -i x-upstream-addr; done
```

---

## 7. Cosas que encontre probando (y arregle)

| Hallazgo | Correccion |
|---|---|
| El round-robin de nginx era **desparejo** (todo iba a una instancia): sin `zone`, cada worker de nginx lleva su propio contador | `zone gs08_api 64k;` en el upstream -> reparto 1 a 1 verificado 12/12 |
| Al arrancar, si `api-b` aun no acepta conexiones, nginx la penalizaba y todo el trafico caia en `api` | `max_fails=3 fail_timeout=10s` + `proxy_next_upstream error timeout` -> peticiones 200 con reintento en la otra instancia |
| `http_requests_inprogress` **no existe** en prometheus-fastapi-instrumentator 8.1.0 (`metrics` solo trae: default, latency, request_size, response_size, combined_size, requests) | El panel 4 se reemplazo por "Errores 4xx (%)", que si tiene datos |
| El job de Prometheus hacia nginx fallaba (`ok\n` no es formato Prometheus), target en `down` | Job eliminado + nota en `prometheus.yml`: nginx necesita su exporter |
| El primer `frontend/Dockerfile` dejaba nginx como root | `USER nginx` + escucha en 8080 + directorios escribibles; `scripts/validar_infra.py` ahora lo verifica |
| `kubectl apply --dry-run=client` no valida sin cluster | La validacion offline es `kubectl kustomize k8s/` (11 objetos) |

---

## 8. Riesgos y supuestos

1. **Disco**: la unidad `C:` esta al 94% (19 GB libres) y Docker Desktop guarda imagenes/volumenes
   ahi. El stack completo (6 imagenes) ocupa ~2.5 GB. Si aprieta: Settings > Resources de Docker
   Desktop para mover el disco a `D:` (187 GB libres).
2. **Supuesto**: el API real conservara `backend/app/main.py` como punto de entrada y expondra
   `/health` y `/metrics`. Si @dev cambia la estructura, se ajusta el `CMD` del Dockerfile.
3. **Supuesto**: dos instancias del API contra una sola base PostgreSQL es aceptable para la
   sustentacion (no hay sesiones en memoria; el estado vive en la BD).
4. **Kubernetes**: sin cluster no hay evidencia de `kubectl get pods`. Alternativa si no se puede
   instalar minikube/k3s en la maquina: desplegar el mismo compose en un host Linux con Docker y
   dejar los manifiestos k8s como entregable validado con `kustomize`.
5. `db/init/` solo corre con el volumen nuevo: recrear la base es `docker compose down -v`
   (**destructivo**: lo ejecuto solo con aprobacion explicita).

---

## 9. Siguiente paso por sprint

- **Sprint 1**: @dev entrega `backend/` y `frontend/`; yo reemplazo el stub, dejo el CI corriendo
  en verde en un pull request real (el workflow se prueba ahi antes de darlo por listo) y agrego
  `postgres-exporter` + dashboard de base de datos.
- **Sprint 2**: cluster local (minikube/k3s), aplicar `k8s/`, evidencia de `kubectl get pods`,
  Ingress con `gs08.local` y despliegue desde CD con `DEPLOY_ENABLED=true`.
- **Sprint 3**: repo publico en GitHub, primer push, CI en `main` y acta con la salida real de
  cada comando para el informe.
