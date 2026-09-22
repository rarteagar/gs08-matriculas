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

**Sprints 0, 1 y 2 cerrados (21-22/09/2026)** — infraestructura, API real y SPA entregados y verificados; el
recorrido de extremo a extremo sale verde por el proxy.

| Sprint | Alcance | Estado hoy |
|---|---|---|
| **Sprint 0** | Alcance, modelo de datos, contenedores/CI/k8s, plan de pruebas | ✅ **Cerrado.** Todo con evidencia pegada (`docs/backlog-sprints.md` §Sprint 0) |
| **Sprint 1** | API núcleo (`/auth/login`, estudiantes, cursos) + cluster local | ✅ **Cerrado:** API real (28 endpoints), `pytest` con **57 pruebas en verde y 87,29 % de cobertura**, y **minikube desplegado** — 3 pods `Running` y el Job `gs08-migraciones` **Complete 1/1 en 39 s** (`83140fd`). El Ingress está creado pero el addon de ingress quedó apagado (anotado: no era criterio de la ronda) |
| **Sprint 2** | Matrículas, SPA y compose con la API real | ✅ **Entregado:** SPA Vue 3 de **4 vistas** (login, panel, estudiantes, matrículas, `9c95d8d`) y el **stub de humo reemplazado por la API real** en el compose (`d42fcfc`), con balanceo y failover probados |
| **Sprint 3** | Notas y boleta | ✅ **Funcionando y verificado en el recorrido completo:** `bash scripts/smoke_api.sh --e2e` → **39 comprobaciones OK, 0 fallas, 0 bloqueadas, exit 0** (login → estudiante → matrícula → 3 notas → boleta 16.00) |
| **Sprint 4** | Cierre, entregables y repo público | ⬜ Pendiente: el push al repo público y el CI en GitHub los hace el dueño al final |

> **Alcance vigente:** el dueño fijó el alcance final el 21/09/2026 en **`docs/alcance-final.md`** (12 endpoints
> de listar/crear/editar y 4 vistas del SPA; usuarios, notas, boleta, `DELETE` y filtros quedan fuera del alcance
> y de la demo). Ese documento **manda sobre cualquier lista anterior** — incluidas las secciones de este README
> que describen lo entregado antes del recorte, que quedan congeladas y no se reescriben.

**Lo que quedó pendiente y por qué** (dicho sin adornos):

- **El push al repositorio público no se hizo** (el repo no tiene remoto), así que los workflows de CI/CD están
  escritos y validados offline, pero no han corrido nunca en GitHub: lo hace el dueño al final.
- **El Ingress de minikube está creado, pero el addon de ingress quedó apagado** en esta ronda (no era criterio
  de esa noche). El acceso al cluster hoy es por `kubectl`: dentro del cluster, `wget /healthz` → `ok` y
  `curl /api/v1/health` → **200** con `entorno: k8s`.
- **El arnés de humo ya no participa:** el compose del repositorio levanta la API real. Sus fixtures viven fuera
  del repo (`D:\dev\_tmp\`) y esperan la orden del dueño para borrarse.

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

Las dependencias del API están **instaladas y verificadas**: `backend/requirements.txt` existe y el comando
exacto del CI (`ruff check . && ruff format --check . && pytest -q --cov=app --cov-fail-under=60`) corre
**57 pruebas con 87,29 % de cobertura, exit 0**. Versiones contratadas (fuente:
`docs/devops/plan-contenedores-ci.md` §3, verificadas contra PyPI el 21/09/2026):

| Componente | Versión |
|---|---|
| FastAPI | `fastapi==0.141.1` |
| uvicorn | `uvicorn==0.53.0` |
| SQLAlchemy | `SQLAlchemy==2.0.54` |
| psycopg | `psycopg[binary]==3.3.6` |
| Instrumentación Prometheus | `prometheus-fastapi-instrumentator==8.1.0` |
| Configuración | `pydantic-settings==2.15.0` |
| Migraciones | `alembic==1.20.0` |
| Frontend | Vue 3 + Vite + Tailwind (`frontend/package.json`): **4 vistas** (login, panel, estudiantes, matrículas) |

---

## 3. Mapa de carpetas

```
gs08-matriculas/
├── README.md                    este archivo
├── docker-compose.yml           db + api + api-b + web; perfil `obs` con Prometheus y Grafana
├── .env.example                 variables con valores por defecto (compose funciona sin .env)
├── .github/workflows/           ci.yml (PR/push) y cd.yml (GHCR + despliegue guardado)
├── backend/                     API FastAPI: 28 endpoints, Alembic y tests (57 pruebas, 87,29 % cobertura)
├── frontend/                    SPA Vue 3 de 4 vistas (src/) + Dockerfile y config de nginx
│   └── nginx/default.conf.template   SPA, proxy /api/, balanceo, cabeceras de seguridad
├── db/
│   ├── init/                    scripts que PostgreSQL ejecuta UNA vez al crear el volumen
│   │   ├── 01-schema.sql        4 tablas + 16 CHECK, 6 UNIQUE, 2 FK, 7 índices, extensión unaccent
│   │   ├── 02-view.sql          v_matriculas_detalle
│   │   ├── 03-seed.sql          1 admin, 12 estudiantes, 7 cursos, 24 matrículas
│   │   └── 04-notas.sql         tabla notas + v_notas_detalle (RN-14/RN-15)
│   └── verificacion/            modelo + notas + comparación con Alembic (exit 0)
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

**Este arranque funciona y está verificado en el entorno real** (`docker compose up -d --build` deja 4
contenedores `healthy` con la API real y el SPA, y el recorrido completo del smoke sale verde por el proxy).
Criterio de terminado de este README (TD-01): «seguido solo el README, el stack queda arriba y
`verificar_stack.py` da exit 0».

| Paso | Comando | Estado |
|---|---|---|
| 1 | `cp .env.example .env` (opcional: compose trae valores por defecto) | ✅ |
| 2 | `docker compose up -d --build` | ✅ db, api, api-b y web en `healthy` |
| 3 | `docker compose ps` → 4 contenedores en `healthy` (+2 con el perfil `obs`) | ✅ verificado (6 contenedores) |
| 4 | `docker compose --profile obs up -d` → +Prometheus +Grafana | ✅ verificado |
| 5 | `python scripts/verificar_stack.py` → `9 comprobaciones OK, 0 fallas`, exit 0 | ✅ verificado (ver §7) |
| 6 | entrar a http://localhost:8080 con `admin` / `Admin123!` y crear una matrícula | ✅ recorrido E2E del smoke, **39 OK, 0 fallas** |

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
`SECRET_KEY` (`docs/devops/plan-contenedores-ci.md` §6). **Puertos publicados al host, todos solo en local:**
`8080` (nginx/SPA), `8000` (API directa), `5432` (PostgreSQL), `9090` (Prometheus) y `3000` (Grafana), más el
`55432`/`55433` de los contenedores de verificación. *(El backlog decía «4000»: verifiqué contra
`docker-compose.yml` y ese puerto no existe; el del API es `8000`.)*

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
| `docs/alcance-final.md` | **alcance vigente fijado por el dueño (21/09/2026)**: 12 endpoints, 4 vistas del SPA y lo que queda fuera de la demo. **Manda sobre cualquier lista anterior** |
| `docs/qa/plan-pruebas.md` | matriz de los 39 criterios, 27 comprobaciones del smoke, E2E de 10 pasos |
| `docs/informe/informe-gs08-matriculas-2026-09-21.docx` · `.pdf` | **informe del proyecto** (borrador, 10 páginas): carátula con los 3 integrantes y el docente, índice, resumen, alcance, arquitectura, modelo de datos, API, infraestructura, Kubernetes, calidad, seguridad/ética/sostenibilidad, firma grupal y anexo de comandos |
| `docs/informe/exposicion-gs08-10-laminas-2026-09-21.pptx` · `.pdf` | **PPTX de sustentación**: 10 láminas exactas, una idea por lámina, con notas del expositor y el documento fuente en cada una (borrador) |
| `docs/qa/reporte-bugs.md` | 9 hallazgos con pasos, esperado, obtenido, evidencia y estado |

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

**Modelo de datos** (no depende del API; verificado por @documentador contra la base viva el 21/09/2026):

```bash
$ docker exec -i gs08-analista-verif psql -q -U gs08 -d gs08_matriculas < db/verificacion/verificar_modelo.sql | grep -c 'NOTICE:  OK'
54
$ docker exec -i gs08-analista-verif psql -q -U gs08 -d gs08_matriculas < db/verificacion/verificar_notas.sql | grep -c 'NOTICE:  OK'
32          # 0 fallas y 0 errores en las dos corridas
```

O todo junto, con una base desechable propia: `bash db/verificacion/ejecutar_verificacion.sh`
(modelo + hash del admin + `04-notas.sql`).

**API real** (el mismo `:8080` del stack; el recorrido completo del contrato, criterio por criterio):

```bash
curl -s http://localhost:8080/api/v1/health          # {"status":"ok","motor":"PostgreSQL 16.15","entorno":"local"}
bash scripts/smoke_api.sh --e2e                       # 39 comprobaciones OK, 0 fallas, 0 bloqueadas (exit 0)
```

Prueba de balanceo y de failover (debe alternar dos IPs internas, y responder **200** con una instancia apagada):

```bash
for i in $(seq 1 6); do curl -s -o /dev/null -D - http://localhost:8080/api/v1/health | grep -i x-upstream-addr; done
```

---

## 8. Problemas conocidos

| Síntoma | Causa | Qué hacer |
|---|---|---|
| El Ingress de minikube está creado pero no responde por `gs08.local` | El **addon de ingress quedó apagado** en esa ronda (el commit `83140fd` anota el estado; no era criterio de esa noche) | `minikube addons enable ingress` cuando se quiera entrar por el host; mientras tanto el cluster se verifica por `kubectl`: dentro del pod, `wget /healthz` → `ok` y `curl /api/v1/health` → **200** con `entorno: k8s` |
| Los `id` de las tablas tienen huecos | `nextval` no se revierte con `ROLLBACK` y un INSERT rechazado consume el id | **No es bug** (D-13). Nadie «arregla» las secuencias a mano |
| El hash del seed es `$2y$...` y pgcrypto no lo valida | Quirk de pgcrypto, no del hash: solo coincide normalizando a `$2a$` | **No tocar el hash** (D-12). Se verifica con `bcrypt` de Python |
| `kubectl apply --dry-run=client` no valida sin cluster | Sin cluster, kubectl no puede descargar el OpenAPI | La validación offline es `kubectl kustomize k8s/` (11 objetos) |
| Con minikube y driver docker, el cluster no ve las imágenes locales | El daemon del cluster es otro | `minikube image load gs08-api:local gs08-web:local`, o construir dentro de `eval $(minikube docker-env)` |
| `host not found in upstream "api-b"` en los logs de `gs08-web` | nginx no arranca si `api-b` no existe | Levantar el stack completo, no solo `web` |
| El pull de imágenes llena el disco `C:` | Docker Desktop guarda en el disco del sistema (estaba al 94 %) | Mover el disco de datos a `D:` en Settings → Resources |

**Problemas que ya están cerrados** (no los busques en la tabla): **BUG-01** (verificador no determinista → TC-01, commit `fbd1d52`), **BUG-05** (nginx `404` en `/health` y `/metrics` → TC-03: verificado hoy, `404` / `404` / `/api/v1/health` `200`), **BUG-06** (las 4 cabeceras en `/api/` → TC-02: verificado hoy, incluida `X-Upstream-Addr`), **BUG-07** (`unaccent` ya en `db/init/` **y** en la revisión inicial de Alembic: `bash db/verificacion/comparar_con_alembic.sh` → exit 0, D-14 cerrado) y **BUG-08/BUG-09** (los dos `500` de los `POST`: no se reprodujeron en la corrida de 39/39). Detalle y estado final: `docs/qa/reporte-bugs.md`.

---

**Última verificación de este README:** 21/09/2026 22:44 (versiones, `docker ps`, `validar_infra.py` y
`verificar_stack.py` corridos por @documentador). Los datos de aplicación (12/7/24, `admin`/`Admin123!`)
salen de `docs/analisis/datos-seed.md`, no de este archivo.
