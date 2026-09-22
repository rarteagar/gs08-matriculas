# GS08 · Matrículas y Notas — Manual técnico

**Entregable:** TD-04 de `docs/backlog-sprints.md` · **Redacta:** @documentador · **Fecha:** 21/09/2026
**Rama:** `main` @ `e051d43` · **Repo:** `D:\dev\equipo\gs08-matriculas` · **Máquina:** ASUS M1502YA (Windows 11 + Docker Desktop)

**Regla de este manual:** cada afirmación cita el archivo o el comando del que sale, y **nada que no exista
se documenta como existente**. Lo que todavía no está implementado va marcado como *«pendiente T\<xx\>»*.
**Actualizado el 22/09/2026**, con el API real, el SPA y el cluster ya entregados.

## Índice

1. [Estado real del sistema](#1-estado-real-del-sistema)
2. [Contrato de la API](#2-contrato-de-la-api)
3. [Versiones del stack y su fuente](#3-versiones-del-stack-y-su-fuente)
4. [Contenedores, red y variables](#4-contenedores-red-y-variables)
5. [Base de datos: inicialización y verificación](#5-base-de-datos-inicialización-y-verificación)
6. [Integración continua y entrega](#6-integración-continua-y-entrega)
7. [Kubernetes](#7-kubernetes)
8. [Observabilidad](#8-observabilidad)
9. [Problemas conocidos](#9-problemas-conocidos)
10. [Verificación rápida (5 comandos)](#10-verificación-rápida-5-comandos)
11. [Archivos citados en este manual](#11-archivos-citados-en-este-manual)

---

## 1. Estado real del sistema

**Actualizado el 22/09/2026** (ronda de cierre): el API real, el SPA de 4 vistas y el cluster están
entregados, y el recorrido de extremo a extremo sale verde por el proxy (**39 OK, 0 fallas**).

| Capa | Estado | Evidencia |
|---|---|---|
| **API FastAPI real** | ✅ **existe, corre y está probado de punta a punta: 28 endpoints publicados**, recorrido completo verde por el proxy | `bash scripts/smoke_api.sh --e2e` → **39 OK, 0 fallas, 0 bloqueadas, exit 0** (`docs/qa/evidencia/smoke-api-20260922-000358.txt`) |
| Autenticación, panel, estudiantes, cursos, matrículas | ✅ **funcionando en el compose real**: `POST /api/v1/auth/login` → 200 + token; `/api/v1/dashboard` → **12 / 7 / 23 / 1**; `?q=45123456` → 1 fila con acentos correctos; `?q=huaman` = `?q=Huamán` = `?q=HUAMAN` → 1/1/1 | salidas reales en §2.1 |
| **Notas y boleta** | ✅ **funcionando:** en el recorrido E2E del smoke, 3 notas → boleta con **16.00** y promedio ponderado | `docs/qa/evidencia/smoke-api-20260922-000358.txt` |
| **`POST /api/v1/matriculas` y `POST /api/v1/usuarios`** | ✅ **cerrados:** los dos `500` por `AmbiguousParameter` (BUG-08/BUG-09) quedaron sin reproducir en la corrida verde de 39/39 | `docs/qa/evidencia/api-500-ambiguousparameter.txt` (el bug) · smoke 39/39 (el cierre) |
| **SPA Vue** | ✅ **existe: 4 vistas** (login, panel, estudiantes, matrículas) servidas por nginx en `:8080` (`9c95d8d`) | `curl -s -o /dev/null -w '%{http_code} %{content_type}' http://localhost:8080/` → `200 text/html` |
| Contenedores, red, balanceo, failover | ✅ **funcionando** | `docker compose ps` (6 contenedores `healthy`), `verificar_stack.py` → 9 OK exit 0 |
| Esquema de datos + reglas en la base | ✅ **funcionando**, y **los dos caminos coinciden** (D-14 cerrado) | `verificar_modelo.sql` → **54 OK** y `verificar_notas.sql` → **32 OK**; `bash db/verificacion/comparar_con_alembic.sh` → **exit 0**, esquema y datos idénticos entre `db/init/` y Alembic |
| Observabilidad (Prometheus + Grafana) | ✅ **funcionando con el tráfico real** (paneles 8 y 9 sin el ruido del scrape, `d42fcfc`) | p95 **0,095 s**; las dos instancias con carga (1,6 / 2,4 req/s) |
| **Kubernetes** | ✅ **desplegado en la máquina**: 3 pods `Running` y el Job de migración `Complete 1/1` (`83140fd`); **Ingress creado pero addon apagado** (anotado) | `kubectl get pods -n gs08` · `kubectl get job -n gs08` |
| **CI/CD en GitHub** | ⛔ escrito, **nunca ejecutado**: el repo no tiene remoto; lo hace el dueño al final | `docs/devops/plan-contenedores-ci.md` §4.6 |

**Estado de los criterios hoy** (cifra de @qa, `docs/qa/plan-pruebas.md` §3): **29 criterios en verde** con
corrida real · **6 pendientes** del guion manual de interfaz · `C-37` y `C-39` en su estado declarado
(Kubernetes desplegado sin Ingress activo; CI sin remoto público). Los criterios que estaban incumplidos por
BUG-08/BUG-09 quedaron verdes en la corrida de 39/39.

> **El único `:8080` sirve la app real.** El arnés de humo con el stub ya no está en juego: el compose del repo
> levanta la API real (`"motor":"PostgreSQL 16.15","entorno":"local"`) y el SPA de Vite. Se puede distinguir en
> un comando: `curl -s http://localhost:8080/api/v1/health` → el campo `entorno` es del API real, y
> `curl -o /dev/null -w '%{http_code}' http://localhost:8080/health` → **404** (D-17, nginx ya no devuelve el
> `index.html` en esas rutas).

---

## 2. Contrato de la API

### 2.1 Lo que existe HOY: el API real (28 endpoints)

Contrato real, enumerado desde su propio OpenAPI (**API del compose, por el proxy en `:8080`**):

```bash
$ curl -s http://localhost:8080/openapi.json | python -c "import sys,json; d=json.load(sys.stdin); print(d['info']); [print(m.upper(), p) for p,v in d['paths'].items() for m in v]"
{'title': 'GS08 · Matrículas y Notas', 'version': '0.1.0',
 'description': 'API del MVP: autenticación, panel, estudiantes, cursos, matrículas, usuarios, notas y boleta.
                 Esquema de datos: db/init/*.sql y la revisión 0001 de Alembic.'}
GET  /health                                     GET  /api/v1/health
POST /api/v1/auth/login                          GET  /api/v1/auth/yo
GET  /api/v1/estudiantes                         POST /api/v1/estudiantes
GET  /api/v1/estudiantes/{estudiante_id}         PUT  /api/v1/estudiantes/{estudiante_id}
DELETE /api/v1/estudiantes/{estudiante_id}       GET  /api/v1/estudiantes/{id}/boleta
GET  /api/v1/cursos                              POST /api/v1/cursos
GET  /api/v1/cursos/{curso_id}                   PUT  /api/v1/cursos/{curso_id}
DELETE /api/v1/cursos/{curso_id}
GET  /api/v1/matriculas                          POST /api/v1/matriculas
GET  /api/v1/matriculas/{matricula_id}           PUT  /api/v1/matriculas/{matricula_id}
DELETE /api/v1/matriculas/{matricula_id}
GET  /api/v1/matriculas/{matricula_id}/notas     POST /api/v1/matriculas/{matricula_id}/notas
PUT  /api/v1/notas/{nota_id}                     DELETE /api/v1/notas/{nota_id}
GET  /api/v1/usuarios                            POST /api/v1/usuarios
GET  /api/v1/usuarios/{usuario_id}               PUT  /api/v1/usuarios/{usuario_id}
DELETE /api/v1/usuarios/{usuario_id}             GET  /api/v1/dashboard
```

Respuestas reales por el proxy, corridas por @documentador el 22/09/2026 contra el stack del compose:

```
$ curl -s http://localhost:8080/api/v1/health
{"status":"ok","motor":"PostgreSQL 16.15","instancia":"5e3d89c30030","entorno":"local"}

$ curl -X POST http://localhost:8080/api/v1/auth/login -H 'Content-Type: application/json' \
       -d '{"usuario":"admin","password":"Admin123!"}'
-> HTTP 200 + access_token (JWT de 184 caracteres)

$ curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8080/api/v1/dashboard
{"estudiantes_activos":12,"cursos_activos":7,"matriculas_activas":23,"usuarios_activos":1,
 "top_cursos":[{"curso_id":1,"codigo":"C101","curso":"Matemática Básica","creditos":4,"matriculas":5},
               {"curso_id":2,"codigo":"C102","curso":"Comunicación Efectiva","creditos":3,"matriculas":4},
               {"curso_id":3,"codigo":"C201","curso":"Programación Web III","creditos":4,"matriculas":4},
               {"curso_id":6,"codigo":"C204","curso":"Estadística Aplicada","creditos":3,"matriculas":3},
               {"curso_id":5,"codigo":"C203","curso":"Inglés Técnico","creditos":2,"matriculas":3}],
 "ultimos_estudiantes":[{"id":12,"codigo":"E20260012","dni":"56234567",
                         "nombres":"Fiorella Milagros","apellidos":"Cárdenas Ruiz", …}]}

$ curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8080/api/v1/estudiantes?q=45123456"
{"total":1,"page":1,"page_size":25,"paginas":1,"estudiantes":[{"id":1,"codigo":"E20260001","dni":"45123456",
 "nombres":"Carlos Alberto","apellidos":"Ramírez Torres","nombre_completo":"Ramírez Torres, Carlos Alberto",
 "email":"cramirez@correo.pe","telefono":"987654321","fecha_nacimiento":"2005-03-14",
 "direccion":"Av. Los Laureles 245, Lima","estado":true,"creado_en":"2026-09-22T04:04:11.429641Z"}]}

$ curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8080/api/v1/estudiantes?q=huaman"
-> total=1, «Quispe Huamán, María Fernanda»   (el buscador sin tildes encuentra el dato con tilde)
```

Tres cosas que estas salidas demuestran: los **acentos viajan correctos en UTF-8** (`Ramírez`, `Huamán`,
`Cárdenas`), el **KPI coincide con el seed** (12 / 7 / 23 / 1) y el **buscador sin tilde funciona**
(`q=huaman` → 1, gracias a `unaccent`).

> **Todo lo de §2.1 sale del stack real del compose, por el proxy en `:8080`.** El stub de humo desapareció
> cuando el SPA real se compiló (el arnés de humo ya no participa), y el `:8010` de las corridas de la ronda
> anterior era una instancia de pruebas aparte, ya apagada. Cómo saber que es el API real y no un stub:
> `curl -s http://localhost:8080/api/v1/health` devuelve `"entorno":"local"` y un `instancia` que es el id del
> contenedor, y `curl -o /dev/null -w '%{http_code}' http://localhost:8080/health` responde **404** (D-17: nginx
> ya no devuelve el `index.html` en esas rutas).

### 2.2 Contrato completo, con el estado real de cada fila

Fuente: `docs/analisis/modelo-datos.md` §4 (casos de uso CU-01…CU-15), `docs/alcance-mvp.md` §4
(criterios `C-01`…`C-39`) y `docs/devops/plan-contenedores-ci.md` §3 (contrato con @dev).
**Estados (los de @qa, `docs/qa/plan-pruebas.md` §3):** ✅ implementado y verificado con corrida ·
⬜ escrito sin verificación · 🔒 fuera de la demo por el alcance final (`docs/alcance-final.md`).

| Método y ruta | Qué hace | Códigos | Criterios | Estado |
|---|---|---|---|---|
| `GET /health` | salud del API **con** verificación de PostgreSQL | 200 | C-34 | ✅ (por `:8000`; por el proxy falta TC-03) |
| `GET /api/v1/health` | lo mismo, para entrar por el proxy | 200 | C-34 | ✅ |
| `GET /metrics` | métricas en formato Prometheus (instrumentator 8.1.0) | 200 | C-34 | ✅ directo en `:8000` (D-17) |
| `POST /api/v1/auth/login` | entra con **usuario o email** (`WHERE nombre_usuario = :u1 OR email = :u2`, igual que `login.php`) | 200 + token · **401** clave mala o usuario inactivo | C-01, C-02 | ✅ verificado con corrida |
| `GET /api/v1/auth/yo` | datos del usuario de la sesión | 200 · 401 | — | ⬜ |
| `GET /api/v1/dashboard` | 4 KPIs + top 5 cursos + últimos 6 estudiantes, desde `v_matriculas_detalle` | 200 (con seed: **12 / 7 / 23 / 1**) | C-05, C-06, C-07 | ✅ verificado con corrida |
| `GET /api/v1/estudiantes?q=&estado=&page=&page_size=` | listado paginado + buscador (código, DNI, nombres, apellidos) | 200 · **422** si `page_size` es 0/200/`abc` | C-08, C-09, C-10 | ✅ `q=huaman`/`Huamán`/`HUAMAN` → **1/1/1** (con `unaccent`) |
| `POST /api/v1/estudiantes` | alta | **201** · **422** (DNI de 7 dígitos, repetidos, email inválido). **Nunca 500** | C-11 | ✅ verificado (422 con el campo) |
| `PUT /api/v1/estudiantes/{id}` | edición (incluye baja lógica con `estado=false`) | 200 · 422 · 409 (auto-desactivarse) | C-11, C-12, C-04 | ✅ el `409` de la propia cuenta (RN-11) |
| `DELETE /api/v1/estudiantes/{id}?confirmar=` | borrado destructivo en dos pasos | **409** `{"detail":"…","matriculas":N}` sin `?confirmar` · **204** con `?confirmar=true` | C-30, C-31, C-32 | ✅ verificado |
| `GET /api/v1/cursos?q=&estado=` | listado y filtro de cursos | 200 | — | ✅ |
| `POST·PUT·DELETE /api/v1/cursos/{id}` | alta/edición/baja; `creditos` 1..10, `horas` 1..1000, default `creditos=3` | **422** (`creditos=0/11`, `horas=0`) · **409** (código repetido) | C-13, C-14, C-15 | ✅ los 422 y el 409 de código repetido |
| `GET /api/v1/matriculas?q=&periodo=` | listado con estudiante y curso (vista), filtro por texto y periodo | 200 · **422** (periodo `2026-13`, `2026/02`) | C-18, C-21, C-24 | ✅ |
| `POST /api/v1/matriculas` | crear matrícula | **201**; **409** «Ese estudiante ya está matriculado en ese curso para el periodo indicado»; **404** por FK | C-16, C-17, C-19 | ✅ **verificado en la corrida E2E** (el `500` de BUG-08 ya no se reproduce) |
| `PUT /api/v1/matriculas/{id}` | editar y **retirar** (`estado="retirado"`, baja lógica) | 200 (el KPI baja exactamente **1** y la fila sigue en el historial) | C-20 | ✅ verificado (retirar y conservar notas) |
| `DELETE /api/v1/matriculas/{id}` | eliminar matrícula | 204 | — | ⬜ |
| `GET·POST /api/v1/usuarios` | gestión de usuarios (**solo `admin`**) | **403** para `asistente` · **409** `nombre_usuario` repetido · **422** clave de 7 o rol inválido | C-22, C-23 | ✅ con la corrida de 39/39 (el `500` del `POST` de BUG-09 ya no se reproduce) · **fuera de la demo** según `docs/alcance-final.md` |
| `POST /api/v1/matriculas/{id}/notas` | registrar nota | **201** · **422** (`nota` 21/-1, `tipo="examen"`) · **409** duplicado **y** nota sobre matrícula `retirado` (RN-14) | C-24, C-25, C-26 | ✅ **funcionando** (verificado a mano por @qa) |
| `PUT·DELETE /api/v1/notas/{id}` | editar / eliminar nota | 200 · 204 | — | ⬜ |
| `GET /api/v1/estudiantes/{id}/boleta?periodo=` | boleta con nota por curso y promedio ponderado por créditos | 200: `14/16/18 → 16.00`; curso sin notas → `nota: null` (no cuenta como 0) | C-27, C-28, C-29 | ✅ **funcionando**: estudiante 1 → C101 **16.00**, **promedio ponderado 13.43** = (16×4 + 10×3) ÷ 7 |

### 2.3 Reglas transversales del contrato

| Regla | Detalle | Fuente |
|---|---|---|
| **Formato de error** | Cuerpo `{"detail": "…"}` con el mensaje **del backend** (el SPA lo muestra tal cual, sin diálogos nativos del navegador) | `docs/qa/plan-pruebas.md` §7, `docs/alcance-mvp.md` §4 |
| **Nunca 500 por dato del usuario** | Un DNI corto, un periodo imposible o un `page_size` absurdo son **422/409**, no 500 | C-11, C-18, C-10 |
| **Paginación** | 25 por página (`page`, `page_size`); fuera de rango → 422 | D-07 |
| **Buscador** | `ILIKE` sobre código, DNI, nombres y apellidos; **`unaccent` obligatorio** para tildes | D-11 + **BUG-07** |
| **Periodo** | `varchar(7)` con CHECK `^[0-9]{4}-(0[1-9]\|1[0-2])$` (ej. `2026-02`) | `db/init/01-schema.sql` |
| **Notas** | `tipo` ∈ {`practica`,`parcial`,`final`}, `numero ≥ 1`, `nota` 0-20; nota del curso = **media aritmética**; promedio del periodo = **ponderado por créditos** | D-03 |
| **Booleans** | `estado` es `true`/`false` en el JSON (en MySQL era `1`/`0`) | `docs/analisis/modelo-datos.md` §2 |
| **Fechas** | `timestamptz` en ISO-8601 con zona; la API responde en `America/Lima` | idem |
| **Salud y métricas** | `/api/v1/health` por el proxy; `/metrics` **directo** en `:8000`; nginx **404** en `/health` y `/metrics` | D-17 |

### 2.4 Requisitos que la infraestructura le impone al código (contrato con @dev)

Fuente: `docs/devops/plan-contenedores-ci.md` §3. Si el código no cumple esto, **el stack no arranca**:

| Punto | Requisito |
|---|---|
| Punto de entrada | `backend/app/main.py`, arrancado con `uvicorn app.main:app --host 0.0.0.0 --port 8000` (el `CMD` del Dockerfile ya lo trae, con `--proxy-headers`) |
| Healthchecks usados por Docker y k8s | `GET /health` → **200** verificando PostgreSQL |
| Métricas | `GET /metrics` con `prometheus-fastapi-instrumentator==8.1.0` |
| Variables | `DATABASE_URL` (la inyecta compose), `SECRET_KEY`, `ENVIRONMENT`, `LOG_LEVEL`, `ACCESS_TOKEN_EXPIRE_MINUTES` |
| Dependencias | `backend/requirements.txt` con versiones **fijadas** (hoy **no existe**: `docker compose build api` falla en `COPY requirements.txt`) |
| Migraciones | Alembic en `backend/alembic/`; en el cluster corre el Job `gs08-migraciones` con `alembic upgrade head` |
| Frontend | `frontend/package.json` con `build` que genere `dist/` y **`package-lock.json` commiteado** (`npm ci` lo exige) |

---

## 3. Versiones del stack y su fuente

**Herramientas de la máquina** (verificadas por @documentador el 21/09/2026; ampliación en
`docs/devops/COMANDOS.md` §0):

| Herramienta | Versión | Comando |
|---|---|---|
| Docker Engine | `29.8.0, build 88096ef` | `docker --version` |
| Docker Compose | `v5.5.1` | `docker compose version` |
| Docker daemon | `29.8.0 \| linux \| overlayfs \| Mem=12 GB` | `docker info --format '…'` |
| kubectl / kustomize | `v1.36.1` / `v5.8.1` | `kubectl version --client` |
| Python | `3.11.16` | `python --version` |
| Node | `v26.1.0` | `node --version` |

**Imágenes** (todas fijadas; `scripts/validar_infra.py` falla si aparece un `:latest`):

| Imagen | Versión | Se declara en |
|---|---|---|
| PostgreSQL | `postgres:16.15-alpine3.24` | `docker-compose.yml`, `k8s/10-postgres.yaml` |
| Python del API | `python:3.12.14-slim-bookworm` | `backend/Dockerfile` (2 etapas: `deps` → `runtime`) |
| Node del SPA | `node:22.23.2-alpine` | `frontend/Dockerfile` |
| nginx | `nginx:1.31.6-alpine` | `frontend/Dockerfile` |
| Prometheus | `prom/prometheus:v3.13.3` | `docker-compose.yml` |
| Grafana | `grafana/grafana:12.4.11` | `docker-compose.yml` |

**Librerías del API** — versiones **contratadas y verificadas contra PyPI el 21/09/2026**, todavía **no
instaladas** (`backend/requirements.txt` es T1.1). Fuente: `docs/devops/plan-contenedores-ci.md` §3.

```
fastapi==0.141.1 · uvicorn==0.53.0 · SQLAlchemy==2.0.54 · psycopg[binary]==3.3.6
prometheus-fastapi-instrumentator==8.1.0 · pydantic-settings==2.15.0 · alembic==1.20.0
```

**Verificación de contraseñas:** `bcrypt==4.2.1` (PyPI) — es la librería con la que se comprobó que el hash
`$2y$` del seed corresponde a `Admin123!` (`docs/analisis/evidencia/hash-legacy-python-bcrypt.txt`).

**Frontend:** Vue 3 + Vite + Tailwind, **sin Pinia ni librería de componentes** (D-16).

---

## 4. Contenedores, red y variables

### 4.1 Servicios del compose

`docker compose config --services` → `db`, `api`, `api-b`, `web` (+ `prometheus`, `grafana` con `--profile obs`).

| Servicio | Contenedor | Imagen | Puerto al host | Notas |
|---|---|---|---|---|
| `db` | `gs08-db` | `postgres:16.15-alpine3.24` | `5432` | volumen `pgdata`; `POSTGRES_INITDB_ARGS: --encoding=UTF8 --locale=C`; healthcheck `pg_isready` |
| `api` | `gs08-api` | `gs08-api:local` (build `backend/`) | `8000` | depende de `db` en estado `healthy` |
| `api-b` | `gs08-api-b` | la misma imagen | — | segunda instancia para el balanceo; **sin puerto al host** a propósito |
| `web` | `gs08-web` | `gs08-web:local` (build `frontend/`) | `8080` | nginx; `API_UPSTREAM` con las dos instancias |
| `prometheus` | `gs08-prometheus` | `prom/prometheus:v3.13.3` | `9090` | perfil `obs`; retención 15 d; `--web.enable-lifecycle` |
| `grafana` | `gs08-grafana` | `grafana/grafana:12.4.11` | `3000` | perfil `obs`; dashboard y datasource provisionados |

**Red:** una sola red bridge, `gs08-net` (`name: gs08-net`, driver `bridge`). Los contenedores se resuelven
por **nombre de servicio** (`api`, `api-b`, `db`), que es lo que usa el upstream de nginx.
**Volúmenes con nombre:** `pgdata` (datos), `prometheus_data` (15 d), `grafana_data` (paneles y usuarios).
**Logs acotados:** driver `json-file` con `max-size: 10m` y `max-file: 3` en todos los servicios.

### 4.2 Variables de entorno

Plantilla: `.env.example` (compose funciona **sin** `.env`, usando esos valores por defecto).

| Variable | Default de desarrollo | Para qué |
|---|---|---|
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | `gs08_matriculas` / `gs08` / `gs08_dev_pwd` | base de datos |
| `DB_PORT` / `API_PORT` / `WEB_PORT` | `5432` / `8000` / `8080` | puertos publicados |
| `ENVIRONMENT` / `LOG_LEVEL` | `local` / `info` | modo y verbosidad del API |
| `SECRET_KEY` | `cambiar-esta-clave-en-produccion` | firma del token |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | vigencia de la sesión |
| `VITE_API_BASE_URL` | `/api/v1` | base de la API embebida en el bundle (mismo origen: nginx proxea) |
| `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD` | `admin` / `gs08_grafana` | acceso a Grafana |
| `PROMETHEUS_PORT` / `GRAFANA_PORT` | `9090` / `3000` | observabilidad |
| `TZ` | `America/Lima` | zona horaria de todos los contenedores |
| `API_UPSTREAM` | (se declara en `docker-compose.yml` y el `ConfigMap` de k8s) | directiva `server` que sustituye `envsubst` en la plantilla de nginx |

**Son credenciales de desarrollo**, declaradas como tales: antes de cualquier entrega se cambian
`POSTGRES_PASSWORD` y `SECRET_KEY` (`docs/devops/plan-contenedores-ci.md` §6).

### 4.3 nginx: SPA + proxy + balanceo

`frontend/nginx/default.conf.template` → el entrypoint de la imagen aplica `envsubst` con `API_UPSTREAM` y
genera `/etc/nginx/conf.d/default.conf`. Lo importante del archivo:

| Bloque | Qué hace |
|---|---|
| `upstream gs08_api` | `${API_UPSTREAM}` + `zone gs08_api 64k;` (sin `zone`, cada worker lleva su contador y el reparto sale desparejo) + `keepalive 16` |
| `listen 8080` | nginx corre como **usuario `nginx`** (no puede escuchar en 80) |
| `location /healthz` | responde `ok` — **healthcheck del contenedor** (lo usa Docker y k8s) |
| `location /api/` | `proxy_pass http://gs08_api`, `proxy_next_upstream error timeout` (reintenta solo en error/timeout, **no** en 5xx para no repetir escrituras), `X-Upstream-Addr` |
| `location /assets/` | caché de 30 d (`immutable`) |
| `location /` | `try_files $uri $uri/ /index.html` — el SPA no se rompe al refrescar una ruta profunda |

Tres comprobaciones sobre este archivo (todas con su salida en §9): balanceo alternando IPs, `404` en
`/health` y `/metrics` (TC-03) y las 4 cabeceras también en `/api/` (TC-02).

### 4.4 Dockerfiles

| Archivo | Detalles |
|---|---|
| `backend/Dockerfile` | 2 etapas: venv en `deps` → `runtime` sin compiladores; usuario `app` (uid/gid 10001); `HEALTHCHECK` con `curl -fsS /health`; `CMD` con `--workers 2 --proxy-headers --forwarded-allow-ips '*'` |
| `frontend/Dockerfile` | etapa `build` (Node 22 → `npm ci && npm run build`) → etapa `runtime` (nginx alpine); `USER nginx`, escucha 8080, directorios escribibles; `HEALTHCHECK` con `wget /healthz`; `ARG VITE_API_BASE_URL` inyectado en el bundle |

Ambos verificados por `scripts/validar_infra.py`: exige `USER` explícito, `HEALTHCHECK` y `.dockerignore`.

---

## 5. Base de datos: inicialización y verificación

### 5.1 Cómo se inicializa

`docker-compose.yml` monta `./db/init` en `/docker-entrypoint-initdb.d:ro`. El entrypoint de `postgres` ejecuta
los `*.sql` **en orden alfabético y una sola vez**, al crear el volumen:
`01-schema.sql` (4 tablas, 16 CHECK, 6 UNIQUE, 2 FK, 7 índices) → `02-view.sql` (`v_matriculas_detalle`) →
`03-seed.sql` (1 admin, 12 estudiantes, 7 cursos, 24 matrículas). Contrato de la carpeta: `db/init/README.md`.

> **Consecuencia operativa:** si se cambia un `.sql`, **no** se aplica solo. Hay que recrear el volumen:
> `docker compose down -v && docker compose up -d db`. Es **destructivo** y por eso se ejecuta solo con
> aprobación explícita.

### 5.2 Cómo se verifica (comando y salida real)

```bash
$ bash db/verificacion/ejecutar_verificacion.sh
verificar_modelo.sql      exit=0   comprobaciones OK=49   fallas=0
verificar_hash_admin.sql  exit=0   comprobaciones OK=2
```

Levanta un PostgreSQL desechable (**puerto 55432**, contenedor `gs08-analista-verif`) con el mismo usuario y
la misma base que el compose, deja que el entrypoint ejecute `01/02/03` y corre las cuatro verificaciones.
Las 49 comprobaciones incluyen **15 pruebas negativas** (se exige que la base devuelva SQLSTATE 23505/23514/23503),
4 dentro de una transacción (cascada en ambos sentidos y las dos secuencias IDENTITY) y 3 después del
`ROLLBACK` (datos intactos). Detalle completo: `docs/analisis/modelo-datos.md` §5.

### 5.3 Las reglas viven en la base, no solo en el código (verificación cruzada)

`docs/devops/evidencia-sprint0.md` §7 — imagen del API contra el esquema, sin tocar datos:

```
tablas visibles para el API: ['cursos', 'estudiantes', 'matriculas', 'usuarios']
vistas visibles para el API: ['v_matriculas_detalle']
filas: cursos 7 | estudiantes 12 | matriculas 24 | usuarios 1   (acentos correctos en UTF-8)
reglas rechazadas por la base (correcto):
  matrícula duplicada  -> uq_matriculas_estudiante_curso_periodo
  dni de 3 dígitos     -> ck_estudiantes_dni
  créditos=99          -> ck_cursos_creditos
  periodo '2026/02'    -> ck_matriculas_periodo
```

### 5.4 Dos rutas del esquema y una sola verdad (D-14)

Hoy hay **dos DDL del mismo esquema**: los scripts `psql` de `db/init/` (que usa el compose al crear el
volumen) y la migración de Alembic (que aplica el Job `gs08-migraciones` en el cluster). La decisión **D-14**
es que la **revisión inicial de Alembic se genere desde `db/init/`**, para que no haya dos verdades.
**Estado: pendiente — es T1.1.** Cualquier cambio de esquema posterior (por ejemplo el `CREATE EXTENSION
unaccent` de BUG-07) debe ir **en los dos lados** o la decisión se rompe.

### 5.5 Datos del seed (los números que no se tocan)

| Dato | Valor | Fuente |
|---|---|---|
| Estudiantes / cursos / matrículas | **12 / 7 / 24** (23 activas + 1 retirada) | `docs/analisis/datos-seed.md` (medido con `psql`) |
| La única retirada | matrícula **13**: estudiante 7 (Castillo Neyra, Jorge Luis), curso 4 (C202 Base de Datos II), `2026-02` | idem |
| Único periodo | `2026-02` en las 24 | idem |
| Login de demo | `admin` / `Admin123!` · `admin@horizonte.edu.pe` | idem |
| Borrado con matrículas | curso 5 → **3** · estudiante 2 → **2** | idem |

---

## 6. Integración continua y entrega

### 6.1 CI (`.github/workflows/ci.yml`) — se dispara en `pull_request` y `push` a `main`, y a mano

| Job | Qué corre | Se salta si… |
|---|---|---|
| `infra` | `python3 scripts/validar_infra.py`, `docker compose config -q`, `hadolint` en los dos Dockerfiles | **nunca**: es el que da verde en el Sprint 0 |
| `backend` | `ruff check` + `ruff format --check` + `pytest --cov=app --cov-fail-under=60` contra PostgreSQL 16 como *service* | no existe `backend/requirements.txt` → **hoy: `skipped`** |
| `frontend` | `npm ci`, `eslint`, `vitest`, `npm run build`, artefacto `frontend-dist` | no existe `frontend/package.json` → **hoy: `skipped`** |
| `imagenes` | `docker compose build` + `up -d` + healthchecks + `trivy` (informativo) + `down -v` | — |
| `ci-ok` | puerta única para la protección de rama | — |

**Estado real: el CI nunca corrió en GitHub** (no hay remoto). Lo que sí se corre en local es su equivalente:

```bash
$ python scripts/validar_infra.py
21 comprobaciones OK, 0 fallas
$ docker compose config -q      # OK, sin salida
```

### 6.2 CD (`.github/workflows/cd.yml`) — tras un CI verde en `main`, o a mano

| Job | Qué hace | Guarda |
|---|---|---|
| `publicar` | buildx + push a **GHCR** con tag `sha` y `main`, con **SBOM y provenance** | `permissions: packages: write` |
| `desplegar` | `kubectl apply -k k8s/`, `set image` con el tag nuevo, `rollout status`, humo contra el Ingress, y `rollout undo` si falla | **solo si `vars.DEPLOY_ENABLED == 'true'`** (hoy no existe: se salta y el pipeline no se rompe) |

Credenciales que faltan para que el despliegue funcione: secret `KUBE_CONFIG_B64` y variable
`DEPLOY_ENABLED=true` — ninguna existe todavía (A-02 / T4.1).

Acciones de GitHub usadas (fijadas por versión): `checkout v7.0.1`, `setup-python v7.0.0`,
`setup-node v7.0.0`, `setup-buildx-action v4.4.1`, `build-push-action v7.4.0`, `login-action v4.6.0`,
`hadolint-action v3.5.0`, `upload-artifact v7.0.1`, `trivy-action v0.36.0`.

---

## 7. Kubernetes

### 7.1 Estado: manifiestos listos, cluster NO desplegado en esta máquina

```
$ kubectl config current-context
error: current-context is not set
$ which minikube kind k3d k3s
ninguno instalado   (solo el cliente kubectl v1.36.1)
$ kubectl kustomize k8s/          # validación offline (la única posible sin cluster)
11 objetos
```

`kubectl apply --dry-run=client` **no** sirve sin cluster (`failed to download openapi`): la validación
offline es `kubectl kustomize k8s/`. **Instalar minikube es software nuevo en la máquina: espera la
autorización del dueño (A-02)**, por eso el criterio `C-37` figura como *bloqueado* y no se escribe
`kubectl get pods` hasta que exista un cluster.

### 7.2 Los 11 objetos

| Kind | Nombre | Detalle que importa |
|---|---|---|
| Namespace | `gs08` | todo vive acá |
| ConfigMap | `gs08-config` | `DB_HOST=gs08-db`, `ENVIRONMENT=k8s`, `API_UPSTREAM="server gs08-api:8000 …"` |
| Service | `gs08-api` | ClusterIP `:8000` |
| Service | `gs08-db` | ClusterIP `:5432` (**no** se publica al host) |
| Service | `gs08-web` | ClusterIP `:80` → contenedor `8080` |
| PersistentVolumeClaim | `gs08-pgdata` | 2Gi, `ReadWriteOnce` |
| Deployment | `gs08-api` | 2 réplicas, `RollingUpdate maxSurge 1 / maxUnavailable 0`, `runAsNonRoot` uid 10001, `capabilities: drop ALL`, probes `/health`, resources 100m/256Mi → 1/512Mi |
| Deployment | `gs08-db` | 1 réplica, `strategy: Recreate` (el volumen RWO no se monta dos veces) |
| Deployment | `gs08-web` | 2 réplicas, probes `/healthz` |
| Job | `gs08-migraciones` | `alembic upgrade head`, `backoffLimit 3`, `ttlSecondsAfterFinished 600`, con initContainer que espera a PostgreSQL |
| Ingress | `gs08` | `ingressClassName: nginx`; `gs08.local/` → web y `gs08.local/api` → api; `proxy-body-size 8m`, `proxy-read-timeout 60` |

El **Secret** no está en la lista a propósito: `k8s/02-secret.example.yaml` es la plantilla y el real se crea
por comando (está en `.gitignore`).

### 7.3 Cómo se levanta (cuando A-02 se apruebe)

Runbook completo: `docs/devops/COMANDOS.md` §5. En resumen:

```bash
minikube start --cpus 4 --memory 6g
minikube addons enable ingress
eval $(minikube docker-env)          # o: minikube image load gs08-api:local gs08-web:local
docker compose build
kubectl -n gs08 create secret generic gs08-secrets --from-literal=… 
kubectl apply -k k8s/
kubectl -n gs08 get pods,svc,ingress
echo "$(minikube ip)  gs08.local" >> /etc/hosts    # en Windows: C:\Windows\System32\drivers\etc\hosts
curl -H "Host: gs08.local" http://$(minikube ip)/api/v1/health
```

**Coherencia importante (D-14):** en el cluster el DDL inicial lo aplica **Alembic** (Job `gs08-migraciones`),
**no** `db/init/` — que solo corre con el volumen nuevo del compose.

---

## 8. Observabilidad

Detalle de cada panel y de los diagramas: `docs/arquitectura.md` §5. Lo esencial para operar:

| Qué | Cómo | Salida real |
|---|---|---|
| Levantar la observabilidad | `docker compose --profile obs up -d` | 6 contenedores en total |
| Targets | http://localhost:9090/targets | `gs08-api/instancia=api → up`, `instancia=api-b → up`, `prometheus → up` |
| Recargar la config de Prometheus | `curl -X POST http://localhost:9090/-/reload` | `HTTP 200` |
| Grafana | http://localhost:3000 con el dashboard `gs08-matriculas` ya provisionado | 9 paneles con datos |
| Métricas crudas | http://localhost:8000/metrics (directo, D-17) | `# HELP http_requests_total …` (~10 KB) |

**Lo que NO se mide:** PostgreSQL y nginx no exponen métricas Prometheus sin un exporter propio; el job de
nginx que existía se eliminó porque fallaba (`ok\n` no es formato Prometheus). Agregarlos es Sprint 1 si el
tiempo alcanza (`docs/devops/plan-contenedores-ci.md` §5). **Tampoco existe** la métrica
`http_requests_inprogress` en el instrumentator 8.1.0: el panel que la usaba se reemplazó por «Errores 4xx (%)».

---

## 9. Problemas conocidos

> **Aviso de vigencia (22/09/2026):** los bugs **05, 06, 07, 08 y 09** que se detallan abajo están **cerrados**
> (TC-02, TC-03, `unaccent` en los dos caminos y la corrida E2E de 39/39): sus bloques quedan como registro de
> lo que se encontró, con la salida de esa ronda. Lo que sigue vigente como problema son los apartados 9.8 a
> 9.11 y el primero de la lista del README (§8).

Cada uno con **cómo se comprueba**. Los dos primeros están reproducidos hoy mismo, tal como siguen.

### 9.1 BUG-05 · `/health` y `/metrics` por el proxy devuelven el `index.html` (arreglo: TC-03)

```
$ curl -s -o /dev/null -w 'proxy 8080 /health   -> %{http_code} %{content_type} %{size_download} bytes\n' http://localhost:8080/health
proxy 8080 /health   -> 200 text/html 371 bytes
$ curl -s -o /dev/null -w 'proxy 8080 /metrics  -> %{http_code} %{content_type} %{size_download} bytes\n' http://localhost:8080/metrics
proxy 8080 /metrics  -> 200 text/html 371 bytes
$ curl -s -o /dev/null -w 'directo 8000 /metrics-> %{http_code} %{content_type} %{size_download} bytes\n' http://localhost:8000/metrics
directo 8000 /metrics-> 200 text/plain; version=1.0.0; charset=utf-8 9952 bytes
```

**Lectura:** nginx solo proxea `/api/`; todo lo demás cae en el `try_files … /index.html`. Un chequeo de
monitoreo que mire solo el código de estado da por bueno un `/metrics` sin métricas. **Decisión D-17:**
`/metrics` se lee directo del API y nginx responde **404** en `/health` y `/metrics` (lo aplica @devops en
TC-03 y lo verifica @qa). Detalle: `docs/qa/reporte-bugs.md` BUG-05.

### 9.2 BUG-06 · Las cabeceras de seguridad no llegan a `/api/` (arreglo: TC-02)

```
$ curl -s -o /dev/null -D - http://localhost:8080/healthz | grep -iE 'server|x-content|x-frame|referrer'
Server: nginx
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Referrer-Policy: strict-origin-when-cross-origin

$ curl -s -o /dev/null -D - http://localhost:8080/api/v1/health | grep -iE 'server|x-content|x-frame|referrer|x-upstream'
Server: nginx
X-Upstream-Addr: 172.18.0.5:8000
```

**Causa:** en nginx, una `location` que declara su propio `add_header` **no hereda** los del `server`; la
`location /api/` declara `X-Upstream-Addr` y por eso pierde los tres. **Arreglo:** repetir los `add_header`
dentro de la location (o `include` de un archivo común). Detalle: `docs/qa/reporte-bugs.md` BUG-06.

### 9.3 BUG-07 · Sin `unaccent` el buscador no encuentra tildes — **CERRADO en los dos caminos**

| Consulta | Antes (sin `unaccent`) | Con `unaccent` |
|---|---|---|
| `?q=huaman` | **0 filas** | 1 |
| `?q=Huamán` | 1 | 1 |
| `?q=HUAMAN` | **0 filas** | 1 |

`ILIKE` ignora mayúsculas pero **no** tildes; el dato del seed es `Quispe Huamán`. **Cerrado:** la extensión
está en `db/init/01-schema.sql` **y** en la revisión inicial de Alembic
(`backend/alembic/versions/0001_esquema_inicial.py:39` → `CREATE EXTENSION IF NOT EXISTS unaccent`), y
`bash db/verificacion/comparar_con_alembic.sh` da **exit 0** con esquema y datos idénticos entre los dos
caminos: **D-14 cerrado**. El API responde `1/1/1` (§2.1).

### 9.3-bis BUG-08 · `POST /api/v1/matriculas` respondía **500** — **CERRADO**

**Fue el peor de los abiertos:** una matrícula nueva y una duplicada devolvían las dos `500`, así que no se
podía matricular por la API y el recorrido de §3 se cortaba en el paso 6 (afectaba `C-16`, `C-17` y `C-19`).
La causa medida fue `psycopg.errors.AmbiguousParameter: could not determine data type of parameter $4` en
`_verificar_duplicado()` (`app/routers/matriculas.py:129`): con `propio=None`, ni el `IS NULL` ni el `<>` le
daban tipo al parámetro, y fallaba solo en el `INSERT` (en el `PUT` el valor llegaba).

**Cerrado con corrida verde:** `bash scripts/smoke_api.sh --e2e` → **39 OK, 0 fallas**, con el alta de
matrícula y el `409` del duplicado dentro del recorrido
(`docs/qa/evidencia/smoke-api-20260922-000358.txt`). Evidencia del bug original:
`docs/qa/evidencia/api-500-ambiguousparameter.txt`.

### 9.3-ter BUG-09 · `POST /api/v1/usuarios` respondía **500** — **CERRADO**

El mismo patrón (`parameter $3`), que bloqueaba el `409` de `C-22` y el `403` de `C-23`. **Cerrado:** sin
`500` en la corrida de 39/39. **Nota de alcance:** el módulo de usuarios quedó **fuera de la demo** por
decisión del dueño (`docs/alcance-final.md`), así que no se muestra aunque funcione.

### 9.4 Quirk `$2y$` de pgcrypto: el hash del seed no se valida desde SQL (no es un bug)

`db/verificacion/diagnostico_hash_legacy.sql` demuestra que pgcrypto calcula un digest distinto con `$2y$` y
solo coincide normalizando a `$2a$` (`verifica_2y = f`, `verifica_2a = t`). **No se toca el hash** (D-12): la
verificación la hace la API con `bcrypt`. Si alguien intenta «comprobar el hash desde SQL», va a creer que el
hash está mal: no lo está.

### 9.5 `LIKE` → `ILIKE` (`D-11`): el buscador del legacy no se puede copiar

Medido sobre 100.000 filas: `LIKE '%quispe%'` → **0 filas**, `ILIKE '%quispe%'` → 2. Un `LIKE` copiado del
legacy deja el buscador **mudo y sin aviso**. El índice GIN trigram (112 ms → 0,09 ms) es un «si algún día
crece», no parte del MVP. Evidencia: `docs/analisis/evidencia/busqueda-rendimiento.txt`.

### 9.6 Ids con huecos (`D-13`): no son un bug

`nextval` no se revierte con `ROLLBACK` y un INSERT rechazado por un CHECK **consume** el id (tras 3 INSERT
fallidos, el siguiente curso válido fue **11**). El seed cierra con `setval`. **Nadie «arregla» las
secuencias a mano.**

### 9.7 El Ingress de minikube está creado pero el addon de ingress quedó apagado

```bash
$ kubectl get pods -n gs08
gs08-api-6768c78484-pddz4   1/1   Running     0   4m17s
gs08-db-5746899898-7nxf7    1/1   Running     0   4m17s
gs08-migraciones-8hx2g      0/1   Completed   0   4m17s
gs08-web-bddfcdcf6-wclh5    1/1   Running     0   4m17s
$ kubectl get job -n gs08
gs08-migraciones   Complete   1/1   39s   4m17s
```

**No es un fallo del despliegue:** los 3 pods están arriba y el Job aplicó el esquema; lo que falta es el
acceso por el host `gs08.local`. **Solución cuando se quiera entrar por ahí:** `minikube addons enable ingress`.
Mientras tanto, el cluster se verifica por `kubectl` (`wget /healthz` → `ok` y `curl /api/v1/health` → **200**
con `entorno: k8s` dentro del pod).

### 9.8 Los scripts de `db/init/` corren una sola vez

Si se cambia un `.sql`, hay que recrear el volumen (`docker compose down -v`, **destructivo**). Además:
`docker compose down` **conserva** los datos; `down -v` **los borra**.

### 9.9 `host not found in upstream "api-b"` en los logs de `gs08-web`

nginx no arranca si `api-b` no existe. **Levantar el stack completo** (`docker compose up -d`), no sólo `web`.
Está en el runbook con otros cuatro síntomas frecuentes: `docs/devops/COMANDOS.md` §7.

### 9.10 El disco `C:` al 94 %

Docker Desktop guarda imágenes y volúmenes en el disco del sistema; el stack completo ocupa ~2,5 GB.
**Solución:** mover el disco de datos a `D:` desde *Settings → Resources* (declarado por @devops).

### 9.11 Con minikube y driver docker, el cluster no ve las imágenes locales

El daemon del cluster es otro. **Solución:** `minikube image load gs08-api:local gs08-web:local`, o
construirlas dentro de `eval $(minikube docker-env)`. (Aplica cuando A-02 se apruebe; hoy no hay cluster.)

---

## 10. Verificación rápida (5 comandos)

```bash
cd /d/dev/equipo/gs08-matriculas

python scripts/validar_infra.py        # 21 OK, exit 0   (sin Docker; es lo que corre el CI en PR)
python scripts/verificar_stack.py      #  9 OK, exit 0   (stack arriba; requiere los contenedores)
bash scripts/smoke_api.sh --e2e        # 39 OK, exit 0   (recorrido completo por el proxy; @qa)
bash db/verificacion/ejecutar_verificacion.sh   # modelo + notas + hash del admin, exit 0
kubectl kustomize k8s/                 # 11 objetos      (validación offline de los manifiestos)
kubectl get pods -n gs08               # 3 pods Running + el Job de migración Complete
```

Corrida de referencia de @documentador, **22/09/2026** (sobre el stack real del compose y el cluster vivo):
`curl` por el proxy → API real con `entorno: local`; `/health` y `/metrics` por el proxy → **404**;
`/api/v1/health` → **200**; las **4** cabeceras presentes en `/api/`; `docker compose ps` → 6 contenedores
`healthy`; `kubectl get pods -n gs08` → 3/3 `Running` y `gs08-migraciones` `Complete 1/1`.

El comando que dice si el contrato está cumplido, criterio por criterio, es el smoke completo (crea y borra
sus propios datos):

```bash
bash scripts/smoke_api.sh --e2e --sin-escritura    # solo lectura
bash scripts/smoke_api.sh --e2e                    # recorrido completo · 39 OK, 0 fallas
```

---

## 11. Archivos citados en este manual

```
docker-compose.yml · .env.example · .gitignore
backend/Dockerfile · frontend/Dockerfile · frontend/nginx/default.conf.template
db/init/{01-schema.sql,02-view.sql,03-seed.sql,README.md} · db/verificacion/*
infra/prometheus/prometheus.yml · infra/grafana/**
k8s/{00..40}*.yaml · k8s/kustomization.yaml
.github/workflows/{ci.yml,cd.yml}
scripts/{validar_infra.py,verificar_stack.py,smoke_api.sh}
docs/analisis/modelo-datos.md · docs/analisis/datos-seed.md · docs/analisis/evidencia/*
docs/devops/plan-contenedores-ci.md · docs/devops/evidencia-sprint0.md · docs/devops/COMANDOS.md
docs/alcance-mvp.md · docs/backlog-sprints.md · docs/decisiones.md
docs/qa/plan-pruebas.md · docs/qa/reporte-bugs.md · docs/qa/evidencia/*
README.md · docs/arquitectura.md · docs/actas/*
```

**Este manual crece con S1-S3:** el contrato de §2.2 pasa de «comprometido» a «verificado» con su ejemplo real
de request/response cuando T1.1-T1.4 estén; ahí se agrega la corrida del smoke por criterio y se actualiza §1.
