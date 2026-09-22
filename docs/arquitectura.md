# GS08 · Matrículas y Notas — Arquitectura

**Entregable:** TD-02 de `docs/backlog-sprints.md` · **Redacta:** @documentador · **Fecha:** 21/09/2026
**Rama:** `main` @ `e051d43` · **Repo:** `D:\dev\equipo\gs08-matriculas`

Este documento **no inventa nada**: cada diagrama sale de un archivo del repositorio o de una salida real,
y cada uno dice de dónde. Los datos técnicos que lo respaldan están en `docs/devops/evidencia-sprint0.md`
(infraestructura, §1-2 y §5), `docs/devops/plan-contenedores-ci.md` (diseño) y `docs/analisis/modelo-datos.md`
§1 (modelo de datos).

**Aviso de estado, para leer los diagramas:** lo que **existe y corre** hoy es la infraestructura (compose,
PostgreSQL con el esquema del legacy, nginx balanceando 2 instancias, Prometheus/Grafana) y el **API real**
(28 endpoints publicados, probado contra una base limpia: 22 de los 39 criterios con corrida verde). **El SPA
es T2.4** y el compose todavía sirve el **stub de humo** en `:8080` (retirarlo es T2.6), así que los diagramas
de componentes y de flujo describen la arquitectura ya construida *alrededor* de ese código: el balanceo, el
failover y la observabilidad son reales; el SPA del diagrama §1 es el que falta.

## Índice

1. [Vista de componentes (Docker Compose)](#1-vista-de-componentes-docker-compose)
2. [Flujo de una petición: balanceo y failover](#2-flujo-de-una-petición-balanceo-y-failover)
3. [Modelo de datos](#3-modelo-de-datos)
4. [Despliegue en Kubernetes](#4-despliegue-en-kubernetes)
5. [Observabilidad](#5-observabilidad)
6. [Decisiones de arquitectura que explican estos diagramas](#6-decisiones-de-arquitectura-que-explican-estos-diagramas)

---

## 1. Vista de componentes (Docker Compose)

**Fuente:** `docker-compose.yml` (servicios `db`, `api`, `api-b`, `web`, perfil `obs` con `prometheus` y
`grafana`), `frontend/nginx/default.conf.template`, `backend/Dockerfile`, `frontend/Dockerfile`.
**Evidencia de que levanta:** `docker compose --profile obs ps` → 6 contenedores healthy
(`docs/devops/evidencia-sprint0.md` §2).

```mermaid
flowchart TB
    subgraph HOST["Host Windows 11 + Docker Desktop 29.8.0"]
        direction TB
        subgraph NET["red bridge gs08-net"]
            WEB["gs08-web · nginx 1.31.6-alpine<br/>usuario nginx, escucha 8080<br/>SPA + proxy inverso /api/"]
            API1["gs08-api · FastAPI (Python 3.12)<br/>usuario app uid 10001, :8000"]
            API2["gs08-api-b · misma imagen<br/>segunda instancia, sin puerto al host"]
            DB[("gs08-db · postgres:16.15-alpine3.24<br/>base gs08_matriculas<br/>volumen pgdata")]
            PROM["gs08-prometheus · v3.13.3<br/>perfil obs, :9090"]
            GRAF["gs08-grafana · 12.4.11<br/>perfil obs, :3000"]
        end
    end

    NAV["Navegador / @qa<br/>http://localhost:8080"]
    QA2["Pruebas directas al API<br/>http://localhost:8000 + /docs"]

    NAV -->|"GET / (SPA)"| WEB
    NAV -->|"GET /api/v1/... (proxy)"| WEB
    QA2 -->|"health, metrics, Swagger"| API1
    WEB -->|"upstream gs08_api (round-robin<br/>max_fails=3 fail_timeout=10s)"| API1
    WEB -->|"misma zona de balanceo"| API2
    API1 -->|"SQLAlchemy + psycopg 3"| DB
    API2 -->|"SQLAlchemy + psycopg 3"| DB
    PROM -->|"scrape /metrics cada 15 s"| API1
    PROM -->|"scrape /metrics cada 15 s"| API2
    GRAF -->|"datasource Prometheus (provisionado)"| PROM

    subgraph VOL["volúmenes con nombre"]
        V1["pgdata"]
        V2["prometheus_data · retención 15 d"]
        V3["grafana_data"]
    end
    DB -.-> V1
    PROM -.-> V2
    GRAF -.-> V3

    subgraph INIT["db/init/*.sql (solo al crear el volumen)"]
        I1["01-schema.sql · 02-view.sql · 03-seed.sql"]
    end
    I1 -.->|"docker-entrypoint-initdb.d"| DB
```

**Puertos publicados al host:** `8080` (web), `8000` (api), `5432` (db), `9090` (prometheus), `3000` (grafana).
**`api-b` no publica puerto a propósito:** solo lo alcanza nginx por la red interna.
**Un contenedor por servicio, imágenes alpine y usuario no root:** el porqué está en
`docs/seguridad-etica-sostenibilidad.md` §3.

---

## 2. Flujo de una petición: balanceo y failover

**Fuente:** `frontend/nginx/default.conf.template` (bloque `upstream gs08_api` con `zone`, `keepalive` y
`proxy_next_upstream`) y `docker-compose.yml` (`API_UPSTREAM` con dos `server` y `max_fails=3 fail_timeout=10s`).
**Evidencia real:** `docs/devops/evidencia-sprint0.md` §3 (12 peticiones alternando `172.18.0.5`/`172.18.0.6`)
y la verificación independiente de @qa (`docs/qa/plan-pruebas.md` §8: 6 peticiones, 3 y 3; y **failover con
las 6 en HTTP 200** con `gs08-api-b` apagado).

```mermaid
sequenceDiagram
    autonumber
    participant N as Navegador / QA
    participant W as nginx (gs08-web:8080)
    participant A as gs08-api (:8000)
    participant B as gs08-api-b (:8000)
    participant D as PostgreSQL (gs08-db:5432)

    N->>W: GET /api/v1/matriculas
    Note over W: upstream gs08_api con zone compartida<br/>-> round-robin entre api y api-b
    W->>A: proxy_pass http://gs08_api
    A->>D: SELECT ... (v_matriculas_detalle)
    D-->>A: filas
    A-->>W: 200 JSON
    W-->>N: 200 JSON + X-Upstream-Addr: 172.18.0.5:8000

    N->>W: GET /api/v1/matriculas (2ª)
    W->>B: proxy_pass (siguiente en el turno)
    B->>D: SELECT ...
    D-->>B: filas
    B-->>W: 200 JSON
    W-->>N: 200 JSON + X-Upstream-Addr: 172.18.0.6:8000

    Note over B: se apaga gs08-api-b (docker stop)
    N->>W: GET /api/v1/matriculas
    W->>B: intento (error de conexión)
    Note over W: proxy_next_upstream error timeout<br/>proxy_next_upstream_tries 2
    W->>A: reintento en la instancia viva
    A->>D: SELECT ...
    A-->>W: 200 JSON
    W-->>N: 200 JSON + X-Upstream-Addr: 172.18.0.6:8000, 172.18.0.5:8000
```

**Cómo se reproduce (un comando, sin tocar nada):**

```bash
for i in $(seq 1 6); do curl -s -o /dev/null -D - http://localhost:8080/api/v1/health | grep -i x-upstream-addr; done
```

**Dos detalles que costaron hallazgos y ya están corregidos** (`docs/devops/evidencia-sprint0.md` §8):

- Sin `zone gs08_api 64k;` cada **worker** de nginx lleva su propio contador y el round-robin salía desparejo
  (todo caía en una instancia). Con la zona, el reparto es 1 a 1.
- Sin `max_fails`/`fail_timeout` + `proxy_next_upstream error timeout`, una instancia que aún no aceptaba
  conexiones al arrancar quedaba penalizada y no había reintento. **Nota deliberada:** solo se reintenta en
  `error timeout`, **no** en 5xx: reintentar un 5xx repetiría escrituras.

---

## 3. Modelo de datos

**Fuente:** `docs/analisis/modelo-datos.md` §1 (traducción de `legacy/script.sql.txt`, MySQL 8 → PostgreSQL 16)
y `db/init/01-schema.sql`, `02-view.sql`, `03-seed.sql`.
**Evidencia:** `bash db/verificacion/ejecutar_verificacion.sh` → **49 comprobaciones OK, exit 0** (incluye 15
pruebas negativas que exigen que la base **rechace** cada regla violada).

```mermaid
erDiagram
    usuarios {
        integer id PK "identity BY DEFAULT"
        varchar nombre_usuario UK "3-50, [A-Za-z0-9_.]"
        varchar email UK "formato válido"
        varchar password_hash "bcrypt coste 10, $2y$ del seed"
        varchar nombre_completo "no vacío"
        varchar rol "admin | asistente, default admin"
        boolean estado "default true"
        timestamptz creado_en "default now()"
    }

    estudiantes {
        integer id PK "identity"
        varchar codigo UK "E20260001, hasta 20"
        char dni UK "exactamente 8 dígitos"
        varchar nombres "no vacío, indexado"
        varchar apellidos "no vacío, indexado"
        varchar email "nullable, formato válido"
        varchar telefono "nullable"
        date fecha_nacimiento "nullable, mayor a 1900-01-01"
        varchar direccion "nullable"
        boolean estado "false = baja lógica"
        timestamptz creado_en "default now()"
    }

    cursos {
        integer id PK "identity"
        varchar codigo UK "C101..."
        varchar nombre "no vacío"
        text descripcion "nullable"
        smallint creditos "CHECK 1..10, default 3"
        smallint horas "CHECK 1..1000, default 48"
        boolean estado "default true"
        timestamptz creado_en "default now()"
    }

    matriculas {
        integer id PK "identity"
        integer estudiante_id FK "ON DELETE CASCADE"
        integer curso_id FK "ON DELETE CASCADE"
        varchar periodo "CHECK AAAA-MM, ej 2026-02"
        date fecha_matricula "no nula"
        varchar estado "activa | retirado, default activa"
        timestamptz creado_en "default now()"
    }

    notas {
        integer id PK "PROPUESTA, Sprint 3 - T1.5/T3.1"
        integer matricula_id FK "ON DELETE CASCADE"
        varchar tipo "practica | parcial | final"
        smallint numero "mayor o igual a 1"
        numeric nota "0..20"
        date fecha_registro "default CURRENT_DATE"
        varchar observacion "nullable"
    }

    estudiantes ||--o{ matriculas : "se matricula en"
    cursos ||--o{ matriculas : "recibe"
    matriculas ||--o{ notas : "se califica con"
    usuarios ||..o{ matriculas : "sin FK - sin auditoria (D-08)"
```

**Objetos y reglas, en números** (`docs/analisis/modelo-datos.md` §1 y §3):

| Objeto | Qué tiene | Dónde vive |
|---|---|---|
| `usuarios`, `estudiantes`, `cursos`, `matriculas` | 4 tablas · **16 CHECK** · **6 UNIQUE** · **2 FK** · **7 índices** | `db/init/01-schema.sql` |
| `v_matriculas_detalle` | JOIN `matriculas + estudiantes + cursos`, **24 filas** con el seed | `db/init/02-view.sql` |
| Seed | 1 admin · 12 estudiantes · 7 cursos · **24 matrículas (23 activas + 1 retirada)** | `db/init/03-seed.sql` |
| La regla central | **`UNIQUE (estudiante_id, curso_id, periodo)`** — un estudiante no repite curso en el mismo periodo | `uq_matriculas_estudiante_curso_periodo` |
| `notas` | **propuesta escrita, no aplicada.** Entra en el Sprint 3 (D-01) como esquema **aditivo**: no se toca ninguna de las 4 tablas | `docs/analisis/modelo-datos.md` §7 |

**Dos cosas que el diagrama no dice y conviene tener presentes:**

- **`periodo` es `varchar(7)`** con CHECK `^[0-9]{4}-(0[1-9]|1[0-2])$`: en MySQL la columna aceptaba 10
  caracteres y el formato lo validaba PHP, así que `2026-13` entraba. Ahora lo rechaza la base.
- **`estado` pasa de `TINYINT(1)` a `boolean`**: en el JSON de la API eso es `true`/`false`, no `1`/`0`.
  Avisado a @dev y @qa por @analista (`modelo-datos.md` §8).

---

## 4. Despliegue en Kubernetes

**Fuente:** `k8s/kustomization.yaml` + los 7 manifiestos que referencia; render verificado con
`kubectl kustomize k8s/` → **11 objetos** (`docs/devops/evidencia-sprint0.md` §5, reconfirmado el 21/09/2026).

> **Estado real: manifiestos listos, cluster NO desplegado en esta máquina.** `kubectl config current-context`
> → `error: current-context is not set`; `minikube`/`kind`/`k3s` **no están instalados** y su instalación
> espera la decisión del dueño (**A-02**). El criterio `C-37` («3/3 pods Running y respuesta por el ingress»)
> está **bloqueado**, y se escribe así: *pendiente — bloqueado por A-02 / T1.6*.
> Lo que sí está validado: el render de kustomize (estructura y referencias cruzadas entre objetos), no el
> despliegue.

```mermaid
flowchart TB
    subgraph NODE["Nodo local (minikube con driver docker — pendiente de instalar)"]
        subgraph NS["namespace gs08"]
            CFG["ConfigMap gs08-config<br/>DB_HOST, puertos, ENVIRONMENT=k8s, API_UPSTREAM"]
            SEC["Secret gs08-secrets<br/>POSTGRES_PASSWORD, SECRET_KEY, DATABASE_URL<br/>(plantilla 02-secret.example.yaml, el real va en .gitignore)"]
            PVC["PersistentVolumeClaim gs08-pgdata<br/>2Gi, ReadWriteOnce"]

            subgraph DBSTACK["Capa de datos"]
                DB["Deployment gs08-db (1 réplica, strategy Recreate)<br/>postgres:16.15-alpine3.24"]
                DBS["Service gs08-db :5432"]
            end

            JOB["Job gs08-migraciones<br/>alembic upgrade head (1 vez por despliegue)"]

            subgraph APPSTACK["Capa de aplicación"]
                APID["Deployment gs08-api (2 réplicas)<br/>RollingUpdate maxUnavailable 0<br/>probes /health, runAsNonRoot 10001"]
                WBD["Deployment gs08-web (2 réplicas)<br/>nginx, probes /healthz"]
                APIS["Service gs08-api :8000 (ClusterIP)"]
                WBS["Service gs08-web :80 (ClusterIP)"]
            end

            ING["Ingress gs08 (ingressClassName nginx)<br/>gs08.local/ -> gs08-web:80<br/>gs08.local/api -> gs08-api:8000"]
        end
    end

    USR["Navegador<br/>http://gs08.local"]
    USR --> ING
    ING --> WBS
    ING --> APIS
    WBS --> WBD
    APIS --> APID
    APID --> APIS
    WBD -->|"API_UPSTREAM = server gs08-api:8000"| APIS
    APID --> DBS
    JOB --> DBS
    DB --> PVC
    CFG -.-> APID
    CFG -.-> WBD
    CFG -.-> DB
    SEC -.-> APID
    SEC -.-> DB
```

**Los 11 objetos** (salida de `kubectl kustomize k8s/`, en orden de render):

| # | Kind | Nombre | Para qué |
|---|---|---|---|
| 1 | Namespace | `gs08` | todo vive en su namespace |
| 2 | ConfigMap | `gs08-config` | configuración no sensible |
| 3 | Service | `gs08-api` | ClusterIP `:8000` |
| 4 | Service | `gs08-db` | ClusterIP `:5432` |
| 5 | Service | `gs08-web` | ClusterIP `:80` → `8080` del contenedor |
| 6 | PersistentVolumeClaim | `gs08-pgdata` | 2Gi, `ReadWriteOnce` |
| 7 | Deployment | `gs08-api` | 2 réplicas, `RollingUpdate` sin caídas |
| 8 | Deployment | `gs08-db` | 1 réplica, `Recreate` (RWO no se monta dos veces) |
| 9 | Deployment | `gs08-web` | 2 réplicas |
| 10 | Job | `gs08-migraciones` | `alembic upgrade head` una vez por despliegue |
| 11 | Ingress | `gs08` | un solo host para SPA y API |

**Nota de coherencia (D-14):** en el cluster el DDL inicial lo aplica **Alembic**, no `db/init/` — el Job
`gs08-migraciones` corre `alembic upgrade head`. Por eso la revisión inicial de Alembic se genera **desde**
`db/init/` y hay una sola fuente de verdad del esquema.

Comandos exactos para levantarlo cuando se apruebe minikube: `docs/devops/COMANDOS.md` §5.

---

## 5. Observabilidad

**Fuente:** `infra/prometheus/prometheus.yml`, `infra/grafana/provisioning/*`,
`infra/grafana/dashboards/gs08-matriculas.json`, `docs/devops/plan-contenedores-ci.md` §5.
**Evidencia:** `docs/devops/evidencia-sprint0.md` §4 (3 targets `up`, consultas de los paneles con tráfico
real: 0,517 req/s · 3,12 % 5xx · 8,13 % 4xx · p95 0,095 s) y la corrida de `verificar_stack.py` del
21/09/2026 22:44: *«targets Prometheus: 3 targets, caidos: ninguno»*, *«paneles Grafana con datos: 9 paneles
revisados, sin datos: ninguno»*.

```mermaid
flowchart LR
    subgraph APIS["Instancias del API"]
        A["gs08-api :8000"]
        B["gs08-api-b :8000"]
    end

    subgraph OBS["Perfil obs (docker compose --profile obs up -d)"]
        P["Prometheus v3.13.3 :9090<br/>scrape_interval 15s<br/>retención 15d"]
        G["Grafana 12.4.11 :3000<br/>usuario admin"]
    end

    subgraph DASH["Dashboard API RED (método Rate-Errors-Duration)"]
        D1["1 Disponibilidad (up)"]
        D2["2 Peticiones/segundo"]
        D3["3 Errores 5xx (%)"]
        D4["4 Errores 4xx (%)"]
        D5["5 Tráfico por instancia"]
        D6["6 Latencia p50/p95/p99"]
        D7["7 Respuestas por estado"]
        D8["8 Top 5 endpoints"]
        D9["9 p95 por endpoint"]
    end

    A -->|"/metrics"| P
    B -->|"/metrics"| P
    P -->|"datasource (provisionado)"| G
    G --> D1
    G --> D2
    G --> D3
    G --> D4
    G --> D5
    G --> D6
    G --> D7
    G --> D8
    G --> D9
    GRAFJSON["infra/grafana/dashboards/gs08-matriculas.json<br/>ES la fuente: se editó el título y Grafana lo<br/>reflejó en 30 s (v2 -> v3)"] -.->|"provisioning automático"| G
```

**Lecturas clave de los paneles** (`docs/devops/plan-contenedores-ci.md` §5):

- **Panel 1 (up):** 2/2 vivas = todo OK; una **CAÍDO** con tráfico en la otra demuestra que nginx y el
  servicio sobreviven — es la vista en vivo del failover del §2.
- **Panel 3 vs 4:** 5xx debe ser **0**; un 4xx alto con 5xx en 0 es buena señal: significa que las reglas de
  negocio están rechazando lo que deben (401, 404, 409).
- **Panel 6:** criterio del MVP, p95 < 0,5 s (medido: 0,095 s con el stub; se repite con el API real, T2.6).

**Limitación declarada:** no hay paneles de PostgreSQL ni de nginx. Ninguno de los dos expone métricas en
formato Prometheus sin un exporter propio; el job de nginx que existía se eliminó porque fallaba
(`ok\n` no es formato Prometheus). Agregar `postgres-exporter` y `nginx-prometheus-exporter` es Sprint 1 si
el tiempo alcanza (`docs/devops/plan-contenedores-ci.md` §5 y §7).

---

## 6. Decisiones de arquitectura que explican estos diagramas

Citadas **tal cual** de `docs/decisiones.md` (no se reescriben, D-20):

| Decisión | Qué fija | Dónde se ve en este documento |
|---|---|---|
| **D-00** | Stack: FastAPI + PostgreSQL 16 + Vue 3 (Vite) + Tailwind, Docker, GitHub Actions, Kubernetes local, Prometheus + Grafana. Se reimplementa el legacy, no se migra | §1, §4, §5 |
| **D-14** | Una sola fuente de verdad del esquema: la revisión inicial de Alembic se genera desde `db/init/` | §3 y §4 (Job de migraciones) |
| **D-17** | Health por el proxy en `/api/v1/health`; `/metrics` **directo** en `:8000`; nginx **404** en `/health` y `/metrics` | §1, §2, §5 |
| **D-04** | Kubernetes local con minikube y driver `docker`; instalarlo requiere aprobación del dueño | §4 |
| **D-11** | Buscador con `ILIKE` (+ `unaccent` para tildes), nunca `LIKE` | §3 (nota de `periodo`/buscador) |
| **D-02** | Borrar estudiante o curso con matrículas no borra en cascada silenciosa: `409` con el conteo, y `204` solo con `?confirmar=true` | §3 (FK `ON DELETE CASCADE` + regla de la API) |
| **D-01** | Las notas **sí** entran al MVP, en el Sprint 3, como esquema aditivo | §3 (bloque `notas`, marcado como propuesta) |
| **D-08** | Sin auditoría (`creado_por`, triggers) en la v1 | §3 (relación punteada `usuarios` ↔ `matriculas`) |

---

**Archivos de los que sale este documento:** `docker-compose.yml`, `frontend/nginx/default.conf.template`,
`frontend/Dockerfile`, `backend/Dockerfile`, `db/init/*.sql`, `k8s/*.yaml`, `infra/prometheus/prometheus.yml`,
`infra/grafana/**`, `docs/devops/evidencia-sprint0.md`, `docs/devops/plan-contenedores-ci.md`,
`docs/analisis/modelo-datos.md`, `docs/decisiones.md`, `docs/qa/plan-pruebas.md`.
**Verificado por @documentador el 21/09/2026 22:44:** `kubectl kustomize k8s/` (11 objetos),
`docker ps` (7 contenedores), `python scripts/validar_infra.py` (21 OK), `python scripts/verificar_stack.py` (9 OK, exit 0).
