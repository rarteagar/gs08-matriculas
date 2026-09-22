# GS08 · Matrículas y Notas

**Repositorio:** `D:\dev\equipo\gs08-matriculas` · **Rama:** `main` (`git branch --show-current`) · **Fecha de este README:** 21/09/2026
**Entregable:** TD-01 de `docs/backlog-sprints.md` · **Redacta:** @documentador

Reimplementación del sistema administrativo **PHP + MySQL** del curso Web III (`legacy/`) sobre un stack
moderno: **API FastAPI + PostgreSQL 16 + SPA Vue 3**, en contenedores, con CI/CD, Kubernetes local y
observabilidad. El legacy **no se migra**: se traduce su modelo de datos y su UX, y se le agregan las
**notas**, que el sistema original no tenía.

> **Alcance cerrado:** **39** criterios de aceptación con ID único `C-01`…`C-39` en `docs/alcance-mvp.md`
> §4 (decisión D-18). Ese es el único denominador de «100 % de cobertura». Lo que **no** entra a la v1 está
> en §5 del mismo documento: fue decisión, no olvido.

## Índice

1. [Estado real del proyecto](#1-estado-real-del-proyecto)
2. [Stack y versiones](#2-stack-y-versiones)
3. [Mapa de carpetas](#3-mapa-de-carpetas)
4. [Arranque en 5 minutos](#4-arranque-en-5-minutos)
5. [URLs y credenciales locales](#5-urls-y-credenciales-locales)
6. [Documentación del proyecto](#6-documentación-del-proyecto)
7. [Cómo se comprueba que el entorno está sano](#7-cómo-se-comprueba-que-el-entorno-está-sano)
8. [Problemas conocidos](#8-problemas-conocidos)

---

## 1. Estado real del proyecto

**Sprint 0 cerrado (21/09/2026)** — infraestructura ejecutada y verificada. La aplicación (API y SPA)
todavía no existe: es T1.1/T2.4.

| Sprint | Alcance | Estado hoy |
|---|---|---|
| **Sprint 0** | Alcance, modelo de datos, contenedores/CI/k8s, plan de pruebas | ✅ **Cerrado.** Todo con evidencia pegada (`docs/backlog-sprints.md` §Sprint 0) |
| **Sprint 1** | API núcleo (`/api/v1/auth/login`, estudiantes, cursos, dashboard) + cluster local | ⬜ **No empezado.** `backend/` solo tiene `Dockerfile`; `POST /api/v1/auth/login` responde **404** (medido por @qa) |
| **Sprint 2** | Matrículas, usuarios y SPA Vue | ⬜ Pendiente |
| **Sprint 3** | Notas y boleta | ⬜ Pendiente |
| **Sprint 4** | Cierre, Kubernetes real y entregables | ⬜ Pendiente |

**Lo que el Sprint 0 deja expresamente sin hacer, y por qué** (dicho sin adornos, `docs/backlog-sprints.md` línea 37):

- **Kubernetes real no existe todavía.** `kubectl config current-context` → `error: current-context is not set`
  y `minikube`/`kind`/`k3s` **no están instalados**. Los 11 manifiestos de `k8s/` validan con `kubectl kustomize`,
  pero eso **no** es un cluster. Instalar minikube es software nuevo en la máquina: espera el OK del dueño (A-02).
- **El push al repositorio público no se hizo** (el repo no tiene remoto), así que los workflows de CI/CD están
  escritos y validados offline, pero no han corrido nunca en GitHub.
- **La API y el SPA no existen.** El stack que hoy está arriba corriendo en la máquina de desarrollo es el
  **arnés de humo** (`D:\dev\_tmp\gs08-smoke`, copia del compose + un stub mínimo de API y SPA), **que no es
  parte de este repositorio**: se usó para validar la infraestructura antes de que exista el código.

---

## 2. Stack y versiones

### 2.1 Herramientas de la máquina de desarrollo (verificado el 21/09/2026)

| Herramienta | Versión real | Comando |
|---|---|---|
| Docker Engine | `29.8.0, build 88096ef` | `docker --version` |
| Docker Compose | `v5.5.1` | `docker compose version` |
| kubectl / kustomize | `v1.36.1` / `v5.8.1` | `kubectl version --client` |
| Python (scripts de validación) | `3.11.16` | `python --version` |
| Node (solo si se corre el frontend fuera de Docker) | `v26.1.0` | `node --version` |
| git | `2.54.0.windows.1` | `git --version` |

Docker Desktop corre con `29.8.0 | linux | overlayfs | Mem=12 GB` (`docs/devops/evidencia-sprint0.md` §1).

### 2.2 Imágenes (todas fijadas por versión, sin `:latest`)

| Imagen | Versión | Dónde se declara |
|---|---|---|
| PostgreSQL | `postgres:16.15-alpine3.24` | `docker-compose.yml`, `k8s/10-postgres.yaml` |
| Python (API) | `python:3.12.14-slim-bookworm` | `backend/Dockerfile` |
| Node (build del SPA) | `node:22.23.2-alpine` | `frontend/Dockerfile` |
| nginx (SPA + proxy) | `nginx:1.31.6-alpine` | `frontend/Dockerfile` |
| Prometheus | `prom/prometheus:v3.13.3` | `docker-compose.yml` |
| Grafana | `grafana/grafana:12.4.11` | `docker-compose.yml` |

`python scripts/validar_infra.py` **verifica que ninguna imagen quede en `:latest`** (21 comprobaciones, 0 fallas).

### 2.3 Backend y frontend: contrato y estado

Las versiones de las dependencias del API están **contratadas y verificadas contra PyPI**, pero **todavía no
instaladas**: `backend/requirements.txt` no existe (es T1.1). Fuente: `docs/devops/plan-contenedores-ci.md` §3.

| Componente | Versión contratada | Estado |
|---|---|---|
| FastAPI | `fastapi==0.141.1` | ⬜ pendiente T1.1 |
| uvicorn | `uvicorn==0.53.0` | ⬜ pendiente T1.1 |
| SQLAlchemy | `SQLAlchemy==2.0.54` | ⬜ pendiente T1.1 |
| psycopg | `psycopg[binary]==3.3.6` | ⬜ pendiente T1.1 |
| Instrumentación Prometheus | `prometheus-fastapi-instrumentator==8.1.0` | ⬜ pendiente T1.1 |
| Configuración | `pydantic-settings==2.15.0` | ⬜ pendiente T1.1 |
| Migraciones | `alembic==1.20.0` | ⬜ pendiente T1.1 |
| Frontend | Vue 3 + Vite + Tailwind (`frontend/package.json`) | ⬜ pendiente T2.4 |

---

## 3. Mapa de carpetas

```
gs08-matriculas/
├── README.md                    este archivo
├── docker-compose.yml           db + api + api-b + web; perfil `obs` con Prometheus y Grafana
├── .env.example                 variables con valores por defecto (compose funciona sin .env)
├── .github/workflows/           ci.yml (PR/push) y cd.yml (GHCR + despliegue guardado)
├── backend/                     API FastAPI  -> hoy solo Dockerfile (código: T1.1)
├── frontend/                    SPA Vue + nginx -> hoy solo Dockerfile y la config de nginx
│   └── nginx/default.conf.template   SPA, proxy /api/, balanceo, cabeceras de seguridad
├── db/
│   ├── init/                    scripts que PostgreSQL ejecuta UNA vez al crear el volumen
│   │   ├── 01-schema.sql        4 tablas + 16 CHECK, 6 UNIQUE, 2 FK, 7 índices
│   │   ├── 02-view.sql          v_matriculas_detalle
│   │   └── 03-seed.sql          1 admin, 12 estudiantes, 7 cursos, 24 matrículas
│   └── verificacion/            49 comprobaciones automáticas del modelo (exit 0)
├── infra/
│   ├── prometheus/prometheus.yml              scrape cada 15 s de las 2 instancias del API
│   └── grafana/{provisioning,dashboards}/     datasource + dashboard «API RED» (9 paneles)
├── k8s/                         Namespace, ConfigMap, Secret (plantilla), PostgreSQL, Job de
│                                migraciones, API, Web, Ingress + kustomization.yaml (11 objetos)
├── scripts/
│   ├── validar_infra.py         valida YAML, dashboard, Dockerfile y versiones fijadas sin Docker
│   ├── verificar_stack.py       verifica el stack en marcha (9 comprobaciones)
│   └── smoke_api.sh             humo de API: 27 comprobaciones, 4 códigos de salida (@qa)
├── legacy/                      sistema PHP + MySQL original (Web III) — material de referencia, no se toca
└── docs/                        ver §6
```

---

## 4. Arranque en 5 minutos

> ⚠️ **Hoy este arranque todavía no funciona desde el repositorio, y está comprobado.** `docker compose build api`
> **falla** en `COPY requirements.txt`: el código del API es **T1.1** y aún no existe. Evidencia:
> `docs/qa/plan-pruebas.md` §8 («Compose del repo → `docker compose build api` → falla: `COPY requirements.txt`
> → not found»). **Criterio de terminado de este README (TD-01):** «seguido solo el README, el stack queda
> arriba y `verificar_stack.py` da exit 0» → **pendiente — bloqueado por T1.1**. Se completa ese día, no antes.

Los pasos que sí están verificados hoy son los de la derecha de la tabla (infraestructura), y se ejecutan
sobre el stack que ya está levantado. Cuando T1.1 cierre, la columna izquierda es literal:

| Paso | Comando | Estado |
|---|---|---|
| 1 | `cp .env.example .env` (opcional: compose trae valores por defecto) | ✅ |
| 2 | `docker compose up -d --build` | ⛔ bloqueado por T1.1 |
| 3 | `docker compose ps` → 4 contenedores en `healthy` | ⛔ ídem |
| 4 | `docker compose --profile obs up -d` → +Prometheus +Grafana (6 en total) | ✅ verificado |
| 5 | `python scripts/verificar_stack.py` → `9 comprobaciones OK, 0 fallas`, exit 0 | ✅ verificado (ver §7) |

Comandos del día a día (logs, consola SQL, reconstruir una sola imagen, borrar el volumen) y el runbook
completo de Kubernetes están en **`docs/devops/COMANDOS.md`**.

> **Ojo con `docker compose down -v`**: borra los volúmenes y con ellos los datos locales. Es **destructivo**
> y es también la única forma de que `db/init/*.sql` se vuelva a ejecutar (el entrypoint de `postgres` los
> corre una sola vez, al crear el volumen).

---

## 5. URLs y credenciales locales

| Qué | URL / valor | Fuente |
|---|---|---|
| SPA (todo entra por acá) | http://localhost:8080 | `docker-compose.yml` |
| API por el proxy | http://localhost:8080/api/v1/... | `frontend/nginx/default.conf.template` |
| Salud por el proxy | http://localhost:8080/api/v1/health | D-17 |
| API directa (Swagger en `/docs`) | http://localhost:8000 | `docker-compose.yml` |
| Métricas (crudas, directas del API) | http://localhost:8000/metrics | D-17 |
| Prometheus (targets) | http://localhost:9090/targets | perfil `obs` |
| Grafana | http://localhost:3000 — `admin` / `gs08_grafana` | `.env.example` |
| PostgreSQL | `localhost:5432`, base `gs08_matriculas`, usuario `gs08` | `.env.example` |
| Login de demo del seed | `admin` / `Admin123!` (o `admin@horizonte.edu.pe`) | `docs/analisis/datos-seed.md` |

**Son credenciales de desarrollo local.** Antes de cualquier entrega se cambian `POSTGRES_PASSWORD` y
`SECRET_KEY` (`docs/devops/plan-contenedores-ci.md` §6). El puerto 4000 también queda expuesto solo en local.

**Decisión D-17 (por qué `/metrics` no va por el proxy):** leer `/metrics` a través del balanceador mezclaría
las métricas de las dos instancias del API. Prometheus scrapea `api:8000` y `api-b:8000` por separado.
Además nginx debe responder **404** —no el `index.html` del SPA— en `/health` y `/metrics`, para que ningún
chequeo de código HTTP dé por bueno un `/metrics` que no trae métricas (BUG-05 de @qa).

---

## 6. Documentación del proyecto

| Documento | Qué contiene |
|---|---|
| `docs/alcance-mvp.md` | alcance (39 criterios `C-01`…`C-39`), lo que NO se hace, riesgos, caso de uso principal §3 |
| `docs/backlog-sprints.md` | reparto por sprints, criterio de terminado y evidencia obligatoria de cada tarea |
| `docs/decisiones.md` | **tabla de decisiones** D-00…D-22 y las abiertas (A-01, A-02). Si algo contradice a otro documento, manda esta tabla |
| `docs/arquitectura.md` | diagramas: componentes, flujo de una petición con balanceo y failover, modelo de datos, despliegue k8s, observabilidad |
| `docs/manual-tecnico.md` | contrato de la API, contenedores y red, CI/CD, Kubernetes, problemas conocidos |
| `docs/manual-usuario.md` | pantalla por pantalla — **pendiente, bloqueado por T2.4** (necesita el SPA) |
| `docs/seguridad-etica-sostenibilidad.md` | bcrypt y el hash `$2y$`, roles, cabeceras, secretos, Ley 29733, ética y costo/sostenibilidad |
| `docs/actas/acta-sprint-0.md` | acta de cierre del Sprint 0: entregables con evidencia, decisiones, bloqueos |
| `docs/actas/retrospectiva-sprint-0.md` | qué salió bien, qué no y acciones con dueño |
| `docs/analisis/modelo-datos.md` | modelo de datos, reglas RN-01…RN-15, casos de uso, 49 comprobaciones |
| `docs/analisis/datos-seed.md` | **valores oficiales del seed** (códigos, DNI, conteos). Si un criterio cita otro dato, el criterio está mal |
| `docs/devops/plan-contenedores-ci.md` | plan de contenedores, CI/CD y observabilidad; contrato con @dev |
| `docs/devops/evidencia-sprint0.md` | evidencia real de infraestructura: comando → salida |
| `docs/devops/COMANDOS.md` | runbook: levantar, logs, observabilidad, k8s, problemas frecuentes |
| `docs/qa/plan-pruebas.md` | matriz de los 39 criterios, 27 comprobaciones del smoke, E2E de 10 pasos |
| `docs/qa/reporte-bugs.md` | 7 hallazgos con pasos, esperado, obtenido, evidencia y estado |

---

## 7. Cómo se comprueba que el entorno está sano

```bash
python scripts/validar_infra.py     # sin Docker: YAML, dashboard, Dockerfile, versiones fijadas
python scripts/verificar_stack.py   # con el stack arriba: 9 comprobaciones HTTP
bash scripts/smoke_api.sh --infra   # humo de infraestructura por el proxy (@qa)
```

Salida real de los dos primeros, corrida por @documentador el **21/09/2026 22:44** (los contenedores se
listaron con `docker ps`, 7 arriba):

```
$ python scripts/validar_infra.py
...
21 comprobaciones OK, 0 fallas

$ python scripts/verificar_stack.py
OK    nginx /healthz: HTTP 200 -> 'ok'
OK    SPA en /: HTTP 200, 371 bytes
OK    /health API directa: HTTP 200 -> {"status":"ok","motor":"PostgreSQL 16.15 on x86_64-pc-linux-musl","instancia":"ca662ba8ec69"}
OK    /health via nginx: HTTP 200 -> {"status":"ok","motor":"PostgreSQL 16.15 on x86_64-pc-linux-musl","instancia":"ca662ba8ec69"}
OK    /metrics: expone http_requests_total
OK    balanceo nginx: reparto entre 2 instancias: {'172.18.0.6:8000': 6, '172.18.0.5:8000': 6}
OK    targets Prometheus: 3 targets, caidos: ninguno
OK    paneles Grafana con datos: 9 paneles revisados, sin datos: ninguno
OK    dashboard provisionado: HTTP 200 en http://localhost:3000/d/gs08-matriculas
========================================================================
9 comprobaciones OK, 0 fallas          (exit 0)
```

**Modelo de datos** (no depende del API, ya está verificado):

```bash
bash db/verificacion/ejecutar_verificacion.sh    # 49 comprobaciones, exit 0
```

Prueba de balanceo y de failover (debe alternar dos IPs internas, y responder **200** con una instancia apagada):

```bash
for i in $(seq 1 6); do curl -s -o /dev/null -D - http://localhost:8080/api/v1/health | grep -i x-upstream-addr; done
```

---

## 8. Problemas conocidos

| Síntoma | Causa | Qué hacer |
|---|---|---|
| `docker compose build api` falla en `COPY requirements.txt` | El código del API es T1.1 y no existe todavía | Esperar T1.1. No es un bug del compose |
| `verificar_stack.py` salía con FALLA en un entorno recién levantado | La serie `status=~"5.."` no existe y Prometheus devuelve vacío, no 0 (BUG-01) | Decisión D-19: serie ausente = **ADVERTENCIA**, no falla. Lo aplica @devops en TC-01 |
| `/health` y `/metrics` por el proxy devolvían el `index.html` con **200** | nginx solo proxea `/api/`; el resto cae en el `try_files` del SPA (BUG-05) | D-17: `/metrics` directo en `:8000` y nginx **404** en `/health` y `/metrics`. TC-03 |
| La respuesta de `/api/` no traía las cabeceras de seguridad | En nginx, una `location` con su propio `add_header` **no hereda** los del `server` (BUG-06) | TC-02: repetir los `add_header` dentro de la `location /api/` |
| El buscador devuelve **0 filas** con tilde (`huaman`) | `ILIKE` ignora mayúsculas pero **no** tildes; falta `CREATE EXTENSION unaccent` (BUG-07) | Debe ir en `db/init/` **y** en la migración inicial de Alembic (D-14). Asignado a @dev + @analista |
| Los `id` de las tablas tienen huecos | `nextval` no se revierte con `ROLLBACK` y un INSERT rechazado consume el id | **No es bug** (D-13). Nadie «arregla» las secuencias a mano |
| El hash del seed es `$2y$...` y pgcrypto no lo valida | Quirk de pgcrypto, no del hash: solo coincide normalizando a `$2a$` | **No tocar el hash** (D-12). Se verifica con `bcrypt` de Python |
| `kubectl apply --dry-run=client` no valida sin cluster | Sin cluster, kubectl no puede descargar el OpenAPI | La validación offline es `kubectl kustomize k8s/` (11 objetos) |
| Con minikube y driver docker, el cluster no ve las imágenes locales | El daemon del cluster es otro | `minikube image load gs08-api:local gs08-web:local`, o construir dentro de `eval $(minikube docker-env)` |
| `host not found in upstream "api-b"` en los logs de `gs08-web` | nginx no arranca si `api-b` no existe | Levantar el stack completo, no solo `web` |
| El pull de imágenes llena el disco `C:` | Docker Desktop guarda en el disco del sistema (estaba al 94 %) | Mover el disco de datos a `D:` en Settings → Resources |

---

**Última verificación de este README:** 21/09/2026 22:44 (versiones, `docker ps`, `validar_infra.py` y
`verificar_stack.py` corridos por @documentador). Los datos de aplicación (12/7/24, `admin`/`Admin123!`)
salen de `docs/analisis/datos-seed.md`, no de este archivo.
