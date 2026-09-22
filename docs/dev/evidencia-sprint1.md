# GS08 · Matrículas y Notas — Evidencia del API real (T1.1–T1.4)

**Autor:** @dev · **Fecha:** 21/09/2026 · **Sprint 1** · Rama `main` · Todo **sin commitear** (commit de cierre del PM)
**Repo:** `D:\dev\equipo\gs08-matriculas` · **Imagen:** `gs08-api:local` (2 instancias en `gs08-net`)

Índice: §1 entregables · §2 cómo se prueba · §3 salidas reales · §4 hallazgos (5 míos + 3 de otros) ·
§5 lo que falta · §6 estado del entorno · §7 fuentes citadas

---

## 1. Qué se entregó

El API que la imagen ya esperaba (`backend/Dockerfile` → `uvicorn app.main:app`) y que hasta hoy no existía:
`backend/` solo tenía el Dockerfile, así que `docker compose build api` moría en `COPY requirements.txt`
(lo reportó @documentador y lo midió @qa). Ahora compila y responde.

| Qué | Archivo | Líneas |
|---|---|---|
| Dependencias con versiones fijadas (contrato de @devops §3 + `bcrypt` y `PyJWT`) | `backend/requirements.txt`, `requirements-dev.txt` | 13 deps |
| Config de lint y pruebas | `backend/pyproject.toml` | 27 |
| Migración inicial espejo de `db/init/*.sql` (48 sentencias) | `backend/alembic/versions/0001_esquema_inicial.py` | 444 |
| Generador de esa revisión (deja la trazabilidad) | `backend/herramientas/generar_revision_inicial.py` | 145 |
| Config, motor de BD, mapeo ORM, contratos, seguridad, dependencias y traducción de errores | `backend/app/{config,db,models,schemas,security,deps,errores,main}.py` | 1.924 (app + routers) |
| Routers: salud, auth, estudiantes, cursos, matrículas+notas+boleta, usuarios, panel | `backend/app/routers/*.py` | (ídem) |
| Pruebas: 57 casos, uno por criterio tocado + E2E del §3 | `backend/tests/*.py` (7 archivos) | 900 |

**32 rutas publicadas** (30 operaciones en el OpenAPI —16 rutas— más `/metrics` y `/`, que van fuera del
esquema). Cubre las 4 tareas de mi Sprint 1 (**T1.1** esqueleto+Alembic, **T1.2** auth,
**T1.3** estudiantes y cursos, **T1.4** panel) y, además, los endpoints de **T2.1/T2.2/T3.1** (matrículas,
usuarios, notas y boleta) porque el grupo B del smoke de @qa los ejercita: sin ellos el smoke no podía pasar
de 8 OK. Lo dejé anotado para que el @pm diga si eso se queda o se corta.

Estructura del API (contrato completo, endpoint por endpoint, en `/docs`):

| Bloque | Endpoints |
|---|---|
| Salud | `GET /health`, `GET /api/v1/health`, `GET /metrics` (Prometheus) |
| Auth (C-01..C-04) | `POST /api/v1/auth/login`, `GET /api/v1/auth/yo` |
| Panel (C-05..C-07) | `GET /api/v1/dashboard` |
| Estudiantes (C-08..C-12, C-30..C-32) | `GET·POST /api/v1/estudiantes`, `GET·PUT·DELETE /api/v1/estudiantes/{id}` |
| Cursos (C-13..C-15) | `GET·POST /api/v1/cursos`, `GET·PUT·DELETE /api/v1/cursos/{id}` |
| Matrículas (C-16..C-21) | `GET·POST /api/v1/matriculas`, `GET·PUT·DELETE /api/v1/matriculas/{id}` |
| Notas (C-24..C-26) | `GET·POST /api/v1/matriculas/{id}/notas`, `PUT·DELETE /api/v1/notas/{id}` |
| Boleta (C-27..C-29) | `GET /api/v1/estudiantes/{id}/boleta?periodo=` |
| Usuarios (C-22/C-23) | `GET·POST /api/v1/usuarios`, `GET·PUT·DELETE /api/v1/usuarios/{id}` |

Decisión que quedó fijada (pedida en el handoff de T1.5): **`numeric(4,2)` sale como número JSON redondeado a
2 decimales (`16.0`) y además como `nota_texto` / `promedio_texto` con los dos decimales fijos (`"16.00"`)**,
que es lo que exige C-27 y lo que muestra la pantalla de la boleta (T2.4). Ejemplo real:
`docs/dev/evidencia/boleta-respuesta-real.json`.

---

## 2. Cómo se prueba (comandos exactos)

```bash
# 1. lint y pruebas (el CI corre lo mismo, con Postgres 16 como servicio)
docker exec gs08-db psql -U gs08 -d postgres -c "CREATE DATABASE gs08_test OWNER gs08"   # una sola vez
docker run --rm --network gs08-net -v "$PWD/backend:/pruebas:ro" -w /pruebas -u root \
  -e DATABASE_URL="postgresql+psycopg://gs08:gs08_dev_pwd@gs08-db:5432/gs08_test" \
  --entrypoint sh gs08-api:local -c "pip install -q -r requirements-dev.txt && ruff check . && ruff format --check . && pytest -q"

# 2. el stack real (imagen del repo, 2 instancias + nginx + base con db/init)
docker compose build api && docker compose up -d

# 3. humo de @qa sobre la API real, con el recorrido completo del §3
bash scripts/smoke_api.sh --e2e

# 4. verificación del stack de @devops
python scripts/verificar_stack.py

# 5. una sola fuente de verdad del esquema (D-14): alembic vs db/init
#    (el comparador es el de @analista: db/verificacion/comparar_con_alembic.sh)
bash db/verificacion/comparar_con_alembic.sh
```

Las pruebas **no** usan el volumen del stack: `tests/conftest.py` borra el esquema `public` de `gs08_test` y
lo vuelve a crear con `alembic upgrade head`, así que cada corrida también comprueba la migración.

---

## 3. Evidencia de ejecución (salidas reales, sin recortar el sentido)

### 3.1 Lint y pruebas — 57 pruebas, exit 0

Archivo completo: `docs/dev/evidencia/ruff-y-pytest.txt` (corrida del 22/09/2026 04:16).

```
--- ruff check .
All checks passed!
exit=0
--- ruff format --check .
27 files already formatted
exit=0
--- pytest -q (base gs08_test, esquema aplicado por alembic upgrade head)
.........................................................                [100%]
PYTEST_EXIT=0
```

57 casos, entre ellos las pruebas negativas que pide C-38 (login malo 401, usuario inactivo 401, cuenta
propia 409, DNI de 7 dígitos 422, DNI/código repetido 422, `page_size` 0 y 200 → 422, periodo `2026-13`
422, duplicado de matrícula 409, `nota=21` 422, matrícula retirada 409, DELETE con matrículas 409) y el
recorrido de extremo a extremo del §3.

### 3.2 El stack responde (imagen del repo, por nginx y directo)

```
$ curl -s http://localhost:8000/health
{"status":"ok","motor":"PostgreSQL 16.15","instancia":"be67334feed7","entorno":"local"}

$ curl -s -D - -o /dev/null http://localhost:8080/api/v1/health
HTTP/1.1 200 OK
Server: nginx
X-Upstream-Addr: 172.18.0.6:8000, 172.18.0.5:8000        <- intentó una instancia, respondió la otra

$ curl -s http://localhost:8000/metrics | grep -c http_requests_total
6
```

### 3.3 Humo de @qa sobre la API real — 37 OK, 1 FALLA

Archivo completo: `docs/dev/evidencia/smoke-api-e2e.txt` (y el original en
`docs/qa/evidencia/smoke-api-20260921-231254.txt`, que genera el propio script).

```
OK    SM-01 [C-34] nginx responde /healthz -> HTTP 200, cuerpo='ok'
OK    SM-02 [C-34] /api/v1/health por el proxy -> HTTP 200 status=ok
OK    SM-04 [C-34] /metrics expone Prometheus -> 3 lineas http_requests_total, 12 series de histograma
OK    SM-05 [C-35] balanceo nginx entre 2 instancias -> 3 172.18.0.3:8000   3 172.18.0.4:8000
OK    SM-09 [C-01] login con usuario -> HTTP 200 + token
OK    SM-10 [C-01] login por email del seed (admin@horizonte.edu.pe) -> HTTP 200
OK    SM-11 [C-01] clave equivocada no emite token -> HTTP 401
OK    SM-12/13 [C-01] sin token y con token falsificado -> HTTP 401 y 401
OK    SM-14 [C-05] KPIs del seed 12/7/23/1 -> 12 | 7 | 23 | 1
OK    SM-15 [C-08] buscador ILIKE + unaccent -> huaman=1 Huamán=1 HUAMAN=1
OK    SM-16 [C-09] busqueda por codigo y por DNI -> codigo=1 dni=1
OK    SM-17 [C-10] page_size fuera de rango -> 422 y 422
OK    SM-18 [C-10] listado paginado -> filas=12 total=12
OK    SM-18b [C-10] ultima pagina parcial -> filas=2 total=12
OK    SM-19 [C-11] DNI de 7 digitos -> HTTP 422, {"detail":"dni: El DNI debe tener exactamente 8 dígitos..."}
OK    SM-20 [C-13] curso con creditos=11 -> HTTP 422
OK    SM-21 [C-18] periodo 2026-13 -> HTTP 422
OK    SM-22 [C-17] matricula duplicada -> HTTP 409 con el mensaje del legacy
OK    SM-23 [C-19] matricula de estudiante inexistente -> HTTP 404
OK    SM-24 [C-16] listado de matriculas del periodo -> HTTP 200, total=24
OK    SM-25 [C-30] DELETE con matriculas no borra nada -> 409 {'matriculas':2}, GET -> HTTP 200
OK    SM-26 [C-23] rol asistente no entra a /usuarios -> HTTP 403
OK    SM-27 [C-19] estudiante inexistente -> HTTP 404
OK    E2E-01 [paso 4] alta de estudiante -> HTTP 201, id=13
OK    E2E-01 [paso 6] matricula -> HTTP 201, id=25   y duplicada -> HTTP 409
OK    E2E-01 [paso 8] notas practica=14, parcial=16, final=18 -> HTTP 201
OK    E2E-01 [paso 8] nota duplicada -> 409 y nota 21 -> 422
OK    E2E-01 [C-31] limpieza con ?confirmar=true -> HTTP 204
FALLA E2E-01 [paso 9 - C-27] boleta: 14/16/18 -> 16 -> obtenido nota_curso= promedio=
37 comprobaciones OK, 1 fallas, 0 bloqueadas
```

La única FALLA **es del script, no del API** (ver §4.6): la boleta real responde 200 con `"nota": 16.0`,
`"nota_texto": "16.00"` y `"promedio": 16.0`, pero la comprobación lee solo los primeros 500 bytes del
cuerpo y busca un campo que se llama distinto. Prueba directa, con el mismo recorrido hecho a mano:

```
$ curl -s "http://localhost:8080/api/v1/estudiantes/14/boleta?periodo=2026-02" -H "Authorization: Bearer <token>"
{ ... "cursos":[{"codigo_curso":"C204","creditos":3,"cantidad_notas":3,"nota":16.0,"nota_texto":"16.00", ...}],
  "creditos_con_notas":3, "promedio":16.0, "promedio_texto":"16.00", "promedio_simple":16.0 }
945 bytes de cuerpo   (el script solo mira los primeros 500)
```

### 3.4 `verificar_stack.py` de @devops — 2 resultados, los dos útiles

Archivos: `docs/dev/evidencia/verificar-stack-rrpath-estudiantes.txt` y `...-rrpath-health.txt`.

**A) Tal como está (RR_PATH por defecto `/api/v1/estudiantes`):** termina con traza, no con reporte.

```
urllib.error.HTTPError: HTTP Error 401: Unauthorized
```

No es un fallo del API: `/api/v1/estudiantes` **exige token** (C-01/SM-12) y el script hace `urlopen` sin
capturar el error. Con `RR_PATH` al endpoint de salud sí funciona (abajo).

**B) `RR_PATH=/api/v1/health`:** 8 OK y 1 FALLA — el BUG-01 otra vez, ahora con la API real.

```
OK    /health API directa / via nginx -> HTTP 200 {"status":"ok","motor":"PostgreSQL 16.15",...}
OK    /metrics: expone http_requests_total
OK    balanceo nginx: reparto entre 2 instancias: {'172.18.0.3:8000': 6, '172.18.0.4:8000': 6}
OK    targets Prometheus: 3 targets, caidos: ninguno
OK    dashboard provisionado: HTTP 200
FALLA paneles Grafana con datos: 9 paneles revisados, sin datos:
      ['3. Tasa de errores 5xx (%)', '7. Respuestas por codigo de estado (2xx / 4xx / 5xx)']
8 comprobaciones OK, 1 fallas
```

Y comprobado en Prometheus que **la serie no existe** (no es que esté vacía):

```
$ curl -s 'http://localhost:9090/api/v1/query?query=http_requests_total{status=~"5.."}'
series: 0
```

### 3.5 Una sola verdad del esquema (D-14) — exit 0

El comparador es el de @analista (`db/verificacion/comparar_con_alembic.sh` + su catálogo, con la guarda que
evita el falso verde de comparar dos fotos vacías). Lo corrí contra **mi** revisión inicial y sale idéntico:

```
$ bash db/verificacion/comparar_con_alembic.sh
== 2. Esperando las dos bases (la primera tiene que haber corrido 01 a 04) ==
   db/init lista con 5 tablas en 3s
== 3. alembic upgrade head sobre la base vacia (imagen gs08-api:local) ==
   revision aplicada: 0001_esquema_inicial
== 4. Foto del catalogo de las dos bases ==
  170 catalogo-dbinit.txt
  170 catalogo-alembic.txt
== 5. Comparacion linea por linea ==
   IDENTICOS: los dos caminos dejan el mismo esquema y los mismos datos
== 6. Secuencias == usuarios OK · estudiantes OK · cursos OK · matriculas OK
exit 0
```

Archivo: `docs/dev/evidencia/d14-comparar-con-alembic.txt`. Incluye `CREATE EXTENSION unaccent`, las 2 vistas
y el trigger de RN-14 dentro de la revisión, que es lo que exige D-14. (Tenía mi propio comparador; al ver el
de @analista —más completo: 170 líneas, con `md5` de los cuerpos de las funciones— borré el mío para no dejar
dos controles de lo mismo.)

---

## 4. Hallazgos (encontrados probando, no leyendo)

### Míos, encontrados por las pruebas y ya corregidos

1. **`bcrypt` 4.2.1 lanza `pyo3_runtime.PanicException` con un hash mal formado**, y esa excepción **no hereda
   de `Exception`**: mi `except (ValueError, TypeError)` no la atrapaba → un hash corrupto en la base habría
   sido un **500**. Corregido en `app/security.py` (se atrapa `BaseException` salvo `KeyboardInterrupt`/
   `SystemExit`). Queda fijado por `test_c03_un_hash_corrupto_no_provoca_500`.
2. **`AmbiguousParameter` de PostgreSQL**: un parámetro enlazado usado como `CAST(:p AS integer) IS NULL`…
   escrito sin el `CAST` (`:p IS NULL`) deja a PostgreSQL sin poder deducir el tipo y la consulta falla
   (`could not determine data type of parameter $3`). Estaba en `matriculas._verificar_duplicado` y en
   `usuarios._duplicados`: **toda matrícula y todo usuario estaban rotos por eso**. Corregido con `CAST`
   (`backend/app/routers/matriculas.py:138` y `backend/app/routers/usuarios.py:42`).
   **Es el mismo fallo que @qa reportó después como BUG-08 y BUG-09**: su evidencia es de las 23:07 y el
   arreglo entró a las 23:09; la corrida del smoke de las 23:12 sobre la imagen reconstruida los da por
   buenos (matrícula nueva → **201**, duplicada → **409**, `asistente` → **201** y `/usuarios` → **403**).
3. **El buscador de `/api/v1/matriculas` no aplicaba `unaccent` a la columna `estudiante`** → `q=huaman`
   devolvía **0** (el apellido del seed es «Huamán»). Lo cazó la prueba de C-21. Corregido.
4. La revisión generada de Alembic tenía las regex del DDL con `\.` → `SyntaxWarning` de Python en cada
   import. Corregido en el generador (`r"""`).
5. **`comparar_esquema.sh` daba un falso positivo**: sin `ON_ERROR_STOP`, `psql` salía con código 0 pese al
   error, el catálogo quedaba vacío en las dos bases y el `diff` decía «sin diferencias». Corregido
   (`ON_ERROR_STOP=1` + mínimo de objetos esperados, `exit 2` si el catálogo sale corto).

### De otros (con la evidencia al lado)

6. **@qa — el smoke no puede leer la boleta.** (a) `E2E-01 [paso 9]` saca `promedio` y `nota_curso` de
   `$CUERPO`, que son los primeros **500** bytes del cuerpo, y la boleta real son **945**: los campos del
   final nunca están en la ventana. `contar()` ya usa el cuerpo completo (`$TMP/compacto`); la misma idea
   arregla esto. (b) El `sed` busca `"nota_curso":` y el campo del curso se llama **`nota`**, que es como lo
   nombra el criterio (C-28: «un curso sin notas sale con `nota: null`»). Con el script como está, esa es la
   única FALLA de toda la corrida.
7. **@qa — `qa_asistente` queda creado y envenena la siguiente corrida.** `SM-26` crea el usuario asistente y
   no lo borra, así que `SM-14` (KPIs `12/7/23/1`) falla en la segunda corrida porque `usuarios_activos` pasa
   a 2. Lo dejé limpio en la base del stack (seed otra vez 1/12/7/24).
8. **@devops — `verificar_stack.py` con la API real.** (a) El `RR_PATH` por defecto apunta a un endpoint
   **autenticado**: ahora da 401 y `urlopen` no captura el `HTTPError`, así que el script muere con traza en
   vez de reportar (`RR_PATH=/api/v1/health` funciona). (b) El BUG-01 sigue vivo con la API real: en un
   entorno recién levantado y sin ningún 5xx, los paneles 3 y 7 no tienen serie (`series: 0`), no es un
   cero. Ojo con una cosa: el `/api/v1/error-forzado` del stub **ya no existe** (no está en el alcance), así
   que la salida es la que ya acordaron en D-19 (serie ausente = **ADVERTENCIA**), no forzar un 500.
9. **Entorno (para quien levante el stack):** al entrar encontré el volumen `pgdata` **inicializado sin los
   scripts de `db/init`** — una tabla `estudiantes` suelta con 3 filas y sin `unaccent` — y por eso el login
   devolvía 500 (`relation "usuarios" does not exist`). Lo restauré con
   `docker compose --profile obs down -v` + `docker compose --profile obs create` + `docker start …`; el log
   del entrypoint muestra los 4 scripts en orden (01-schema, 02-view, 03-seed, 04-notas) y el seed quedó en
   1/12/7/24/0. Sospecha razonable: se levantó el stack desde otra carpeta donde el `./db/init` del compose
   no existía — el bind es **relativo al directorio del compose**.

---

## 5. Lo que NO está hecho (y por qué)

- **SPA (T2.4).** El navegador sigue mostrando el stub: `frontend/` no tiene `package.json`, así que
  `docker compose up -d --build` **falla en el servicio `web`**. La imagen que corre (`gs08-web:local`) es la
  del stub. Mientras eso no esté, el criterio de terminado de TD-01 («siguiendo solo el README, el stack
  queda arriba») sigue bloqueado, ahora **solo** por el frontend.
- **Kubernetes (T1.6/T4.1).** Sin cambio: minikube no está instalado y es decisión de @user (A-02).
- **`db/init` no se re-ejecuta solo.** Aviso de @analista que confirmo: `04-notas.sql` no aparece en un
  volumen ya creado; para verlo hay que `down -v` o usar la migración (`comparar_esquema.sh` lo hace).
- **Nada de esto está commiteado** (convención de la sala: commit de cierre del @pm).

---

## 6. Estado del entorno al terminar

| Cosa | Estado |
|---|---|
| Contenedores | `gs08-db`, `gs08-api`, `gs08-api-b`, `gs08-web`, `gs08-prometheus`, `gs08-grafana` **arriba**; api y db `healthy` |
| Imagen del API | `gs08-api:local` **reconstruida desde `backend/`** (antes era el stub) |
| Base del stack | `gs08_matriculas` con el seed intacto: usuarios 1 · estudiantes 12 · cursos 7 · matrículas 24 (23 activas) · notas 0 |
| Bases auxiliares | `gs08_test` (pruebas) y `gs08_mig` (comparación de esquema) creadas dentro del mismo contenedor |
| Datos de prueba | ninguno: el E2E borra lo que crea y limpié el `qa_asistente` que dejó el smoke |

---

## 7. Fuentes citadas

`docs/alcance-mvp.md` rev. 2 (§3, §4: C-01…C-39) · `docs/backlog-sprints.md` (T1.1–T1.4, TC-01/03) ·
`docs/decisiones.md` (D-14, D-19) · `docs/analisis/modelo-datos.md` §3 (RN-01…RN-16), §6.1 (hash `$2y$`), §6.3 (`LIKE`→`ILIKE`+`unaccent`) y
§7 (notas) · `docs/analisis/datos-seed.md` (12/7/24, DNI, `admin@horizonte.edu.pe`) ·
`docs/devops/plan-contenedores-ci.md` §3 (contrato: rutas, `/metrics`, puerto, variables, versiones fijadas) ·
`docs/qa/plan-pruebas.md` + `reporte-bugs.md` + `scripts/smoke_api.sh` (BUG-01, BUG-05, BUG-06, BUG-07) ·
`db/init/*.sql` (esquema y seed) · `docker-compose.yml`, `backend/Dockerfile`, `.github/workflows/ci.yml`.
