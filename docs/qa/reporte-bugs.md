# GS08 · Matrículas y Notas — Reporte de bugs

**Autor:** @qa · **Ronda 1 (Sprint 1)** · **21/09/2026** · Repo: `D:\dev\equipo\gs08-matriculas`

Cada hallazgo con: pasos para reproducir, resultado esperado, resultado obtenido, evidencia y gravedad.
**Gravedad:** *Alta* = rompe un criterio de aceptación o el guion de la demo · *Media* = prueba mal escrita
o resultado no reproducible · *Baja* = molestia, no bloquea.

| # | Título | Gravedad | Dueño | Estado final |
|---|---|---|---|---|
| BUG-01 | `verificar_stack.py` da FALLA en un entorno recién levantado: el criterio «exit 0» no es reproducible | Alta | @devops | **Cerrado — verificado por mí (TC-01)**: `verificar_stack.py` dos veces seguidas → `13 OK, 1 advertencia, 0 fallas`, exit 0 y exit 0 |
| BUG-02 | El criterio AP-01 citaba un email que no existe en el seed | Media | @pm (+@analista) | **Cerrado — D-21**: el alcance (rev. 2) cita `admin@horizonte.edu.pe` en `C-01` |
| BUG-03 | El criterio AP-03 citaba un DNI que no existe en el seed | Media | @pm (+@analista) | **Cerrado — D-21**: `C-09` cita el DNI `45123456` del seed |
| BUG-04 | El alcance anunciaba 35 criterios; §4 tenía 39 | Media | @pm | **Cerrado — D-18**: 39 criterios con ID `C-01`…`C-39`, denominador único de T4.2 |
| BUG-05 | `/health` y `/metrics` por el proxy devuelven el `index.html` con **200** | Alta | @pm + @devops | **Cerrado — verificado por mí (TC-03)**: `localhost:8080/health` → **404**, `/metrics` → **404**, `/api/v1/health` → **200**; `localhost:8000/metrics` con texto Prometheus |
| BUG-06 | Los headers de seguridad no llegan a las respuestas de `/api/` | Baja | @devops | **Aceptado** (decisión de @pm en la sala). Arreglo en **TC-02**; pendiente de verificación por mí |
| BUG-07 | **C-08 no se puede cumplir con `ILIKE` solo**: falta la extensión `unaccent` | Alta | @dev (+@analista, DDL) | **Cerrado en `db/init/` — verificado por mí** (1 / 1 / 1). Falta la misma extensión en la revisión inicial de Alembic (D-14, T1.1 de @dev) |
| BUG-08 | **`POST /api/v1/matriculas` → 500** (`AmbiguousParameter`): rompe C-16, C-17 y todo el recorrido E2E | **Crítica** | @dev | **Cerrado — verificado por mí**: duplicado → **409** con el mensaje del legacy y matrícula nueva → 201. El smoke completo da **31 OK, 0 fallas, exit 0** |
| BUG-09 | **`POST /api/v1/usuarios` → 500** (`AmbiguousParameter`): rompe C-22 (409) y C-23 (403 por rol) | **Crítica** | @dev | **Cerrado — verificado por mí**: `POST /api/v1/usuarios` → 201, duplicado → **409**; el 403 por rol entra en la corrida verde |

> **Regla:** un bug se cierra con la corrida verde, no con la decisión. Los tres que están «pendiente de
> verificación» los vuelvo a probar yo cuando @devops aplique TC-01/TC-02/TC-03, con el comando pegado en
> §«Verificación de los arreglos».

---

## BUG-01 · `verificar_stack.py` no es determinista: sin tráfico 5xx reciente da FALLA y exit 1

**Dueño:** @devops · **Gravedad:** Alta · **Criterio afectado:** AP-09 #33 (`verificar_stack.py` exit 0) y el
gate de la demo (`docs/backlog-sprints.md` T4.4).

**Pasos para reproducir**
1. Levantar el stack **de cero**: `docker compose down -v && docker compose --profile obs up -d`.
2. **No** generar ningún 500 (no llamar a `/api/v1/error-forzado`): recorrer solo la app normal.
3. Correr: `python scripts/verificar_stack.py`.

**Resultado esperado:** `9 comprobaciones OK, 0 fallas`, exit 0 — como reportó @devops.

**Resultado obtenido:** `8 comprobaciones OK, 1 fallas`, **exit 1**:
```
FALLA paneles Grafana con datos: 9 paneles revisados, sin datos:
      ['3. Tasa de errores 5xx (%)', '7. Respuestas por codigo de estado (2xx / 4xx / 5xx)']
```

**Causa (comprobada, no supuesta).** Los paneles 3 y 7 usan `rate(...status=~"5..")`. Mientras la serie
**no exista en absoluto** (nunca se sirvió un 5xx desde que Prometheus arrancó), la consulta devuelve
**resultado vacío**, no un 0 — y el script cuenta «resultado vacío» como «panel sin datos»:
```
$ curl -sG --data-urlencode 'query=sum by (status) (http_requests_total)' http://localhost:9090/api/v1/query
[('2xx', '218'), ('4xx', '7')]                 # no existe la serie 5xx
$ curl -sG ... 'query=100 * sum(rate(http_requests_total{status=~"5.."}[5m])) / ...'
{"data":{"result":[]}}                          # vacio -> el script lo cuenta como FALLA
$ curl -sG --data-urlencode 'query=sum(rate(http_requests_total{status=~"3.."}[5m]))'   # un status que nunca se sirvio
{"data":{"result":[]}}                          # mismo mecanismo, sobre un sistema perfectamente sano
```
Y se cierra la prueba en el otro sentido: disparando 3 `curl` a `/api/v1/error-forzado` (endpoint que existe
justamente para eso) **la serie pasa a existir con valor 0** y el script vuelve a `9 OK, 0 fallas`, exit 0 —
para siempre. **Hipótesis descartada por mí mismo:** «esperar 5 minutos sin 5xx» **no** reproduce el fallo
(probado: 9 OK, exit 0). Lo que lo dispara es que la serie nunca haya existido, o sea **un entorno recién
levantado**.

**Evidencia:** `docs/qa/evidencia/verificar-stack-no-determinista.txt` (las 4 partes: estado sin la serie,
la corrida en rojo, la corrida en verde tras un 500 y la comprobación del mecanismo con el 3xx).

**Impacto real:** el ensayo de la sustentación con el entorno recién levantado (`down -v` + `up`, T4.4) y
cualquier corrida de un jurado van a mostrar un rojo que **no es del sistema**; y el criterio AP-09 #33 queda
como «no reproducible». Un panel sin datos **no es** lo mismo que una prueba fallida.

**Qué propongo (decisión de @devops):** que el chequeo distinga *sin serie* de *serie en 0* — si el
selector no existe en `/api/v1/series`, se reporta `ADVERTENCIA sin datos todavía (no es falla)`; y si se
quiere el panel con datos en la demo, que el guion dispare un 5xx antes de entrar a Grafana.

**Estado:** **aceptado — D-19** («una serie de Prometheus ausente es ADVERTENCIA, no falla»), lo aplica
@devops en **TC-01**. Pendiente de verificación por mí (§«Verificación de los arreglos»).

---

## BUG-02 · El criterio AP-01 cita `admin@institucion.edu.pe`, que no existe en el seed

**Dueño:** @pm (documento) + @analista (aviso) · **Gravedad:** Media · **Criterio:** AP-01 #1.

**Reproducir**
1. `docker exec gs08-analista-verif psql -U gs08 -d gs08_matriculas -c "select nombre_usuario,email from usuarios;"`
2. Comparar con `docs/alcance-mvp.md` §4 AP-01.

**Esperado:** el criterio se puede ejecutar tal como está escrito.
**Obtenido:** el único email del seed es **`admin@horizonte.edu.pe`** (y el legacy también dice
`admin@horizonte.edu.pe`, `legacy/script.sql.txt` línea 122). `admin@institucion.edu.pe` **no existe en
ninguna tabla**: un test escrito literalmente contra el criterio daría 401 y el criterio parecería roto.

**Evidencia:** salida real (arriba) + `db/init/03-seed.sql` línea 20 + el smoke SM-10 usa el email real.

**Corrección:** en §4 AP-01, `admin@institucion.edu.pe` → `admin@horizonte.edu.pe`.

**Estado:** **cerrado — D-21**, corregido en la rev. 2 del alcance (`C-01`). El seed no se toca.

---

## BUG-03 · El criterio AP-03 cita el DNI `12345678`, que no existe en el seed

**Dueño:** @pm (documento) · **Gravedad:** Media · **Criterio:** AP-03 #9.

**Reproducir:** `select dni from estudiantes order by id;` y comparar con §4 AP-03.
**Esperado:** `?q=12345678` devuelve exactamente 1 fila (según el criterio).
**Obtenido:** los DNI del seed son `45123456`, `46234567`, `47345678`, … Ningún estudiante tiene `12345678`:
la búsqueda devolvería **0 filas** y el criterio quedaría incumplido por el dato, no por el código.

**Corrección:** usar `45123456` (estudiante 1, `E20260001`). El smoke ya lo comprueba así (SM-16).

**Estado:** **cerrado — D-21**, corregido en la rev. 2 del alcance (`C-09`). El seed no se toca.

---

## BUG-04 · El alcance dice 35 criterios; la tabla §4 tiene 39

**Dueño:** @pm · **Gravedad:** Media · **Afecta:** `alcance-mvp.md` (resumen del Sprint 0) y T4.2, que exige
«**100 %** de los criterios de §4 con estado y evidencia».

**Cómo lo conté:** todo ítem de lista de §4 que lleve ✅ o ⛔.
```
AP-01: 4 · AP-02: 3 · AP-03: 5 · AP-04: 3 · AP-05: 6 · AP-06: 2 · AP-07: 6 · AP-08: 3 · AP-09: 7  = 39
```
**Por qué importa:** con dos denominadores distintos (35 y 39), «100 % de cobertura» no se puede verificar,
y los 4 criterios de diferencia son justo los que se cuelan sin dueño. El plan de pruebas
(`docs/qa/plan-pruebas.md` §3) ya lista los 39, uno por uno, con su estado.

**Estado:** **cerrado — D-18**: son **39**, con ID único `C-01`…`C-39` en la rev. 2 del alcance, y ese es el
único denominador de T4.2. Mi conteo y el de @pm coinciden (el error era del grep de @pm, que no veía los
criterios escritos en línea). La matriz de `plan-pruebas.md` ya usa los `C-xx`.

---

## BUG-05 · `/health` y `/metrics` por el proxy devuelven el `index.html` con **200**

**Dueño:** @pm (criterio) + @devops (nginx) · **Gravedad:** Alta · **Criterio:** AP-09 #34.

**Pasos para reproducir**
```
curl -s -o /dev/null -w '%{http_code} %{content_type} %{size_download}\n' http://localhost:8080/health
curl -s -o /dev/null -w '%{http_code} %{content_type} %{size_download}\n' http://localhost:8080/metrics
curl -s -o /dev/null -w '%{http_code} %{content_type} %{size_download}\n' http://localhost:8000/metrics
```
**Esperado:** `/health` y `/metrics` responden con su contenido por el proxy `http://localhost:8080`
(es lo que pide el criterio AP-09 #34).

**Obtenido:**
```
proxy 8080 /health          -> HTTP 200  text/html   371 bytes   <!doctype html>...   (el index.html del SPA)
proxy 8080 /metrics         -> HTTP 200  text/html   371 bytes   <!doctype html>...
directo 8000 /metrics       -> HTTP 200  text/plain 12.349 bytes  # HELP http_requests_total...
```
Nginx solo hace proxy de `/api/`; todo lo demás cae en el `try_files ... /index.html` del SPA. Resultado:
**HTTP 200 con HTML** donde debería haber métricas. Es el mismo tipo de trampa que el `LIKE` del legacy:
algo que responde «bien» sin traer lo que se pidió. Un chequeo de monitoreo que mire solo el código de
estado da por bueno un `/metrics` que no existe.

**Evidencia:** la salida de arriba (corrida hoy sobre el stack en marcha).

**Dos arreglos posibles (decisión de @pm/@devops):**
- (a) nginx publica `/health` y `/metrics` (bloque `location = /metrics { proxy_pass ...; }`, restringido a
  la red interna en el cluster), y el criterio se mantiene tal cual;
- (b) el criterio se corrige: `/api/v1/health` **por el proxy** y `/metrics` **directo** en `:8000` (que es
  como los scrapea Prometheus).

**Estado:** **aceptado — D-17**, y la decisión va más lejos que las dos opciones que planteé: `/metrics` se
lee **directo** en `:8000` (para no mezclar las métricas de las dos instancias en el balanceador) **y nginx
responde 404 en `/health` y `/metrics`** en vez del `index.html`, que es lo que pedía el bug: que un chequeo
de código HTTP no pueda dar por bueno algo que no trae métricas. Lo aplica @devops en **TC-03**; el criterio
`C-34` ya está reescrito en la rev. 2. Pendiente de verificación por mí.

---

## BUG-06 · Los headers de seguridad no llegan a las respuestas de `/api/`

**Dueño:** @devops · **Gravedad:** Baja (no rompe ningún criterio; sí afecta la entrega de seguridad del informe)

**Pasos para reproducir**
```
curl -s -o /dev/null -D - http://localhost:8080/healthz     | grep -i x-content
curl -s -o /dev/null -D - http://localhost:8080/api/v1/health | grep -i x-content
```
**Esperado:** las dos respuestas traen `X-Content-Type-Options: nosniff` (está declarado en el bloque
`server` de `frontend/nginx/default.conf.template`).

**Obtenido:** `/healthz` trae los tres headers; **la respuesta de `/api/` no trae ninguno**:
```
/healthz      -> Server: nginx | X-Content-Type-Options: nosniff | X-Frame-Options: SAMEORIGIN | Referrer-Policy: strict-origin-when-cross-origin
/api/v1/health-> Server: nginx | X-Upstream-Addr: 172.18.0.5:8000
```
**Causa:** en nginx, un `location` que declara su propio `add_header` **no hereda** los del `server`; la
location `/api/` declara `add_header X-Upstream-Addr` y por eso pierde los tres. No es un bug de seguridad
grave (son cabeceras de endurecimiento), pero es exactamente el tipo de detalle que un jurado pregunta y
que se arregla repitiendo los `add_header` (o con `include` de un archivo común) dentro de la location.

**Evidencia:** la salida de los dos `curl` de arriba.

**Estado:** **aceptado** por @pm; lo aplica @devops en **TC-02** (los 4 headers también en `/api/`, incluido
`X-Upstream-Addr`). Pendiente de verificación por mí.

---

## BUG-07 · El criterio C-08 no se puede cumplir con `ILIKE` solo: falta `unaccent`

**Dueño:** @dev (buscador) + @analista (DDL) · **Gravedad:** Alta · **Criterio:** `C-08` (y `C-21` en el
filtro de matrículas).

**Qué pide el criterio:** `GET /api/v1/estudiantes?q=huaman`, `?q=Huamán` y `?q=HUAMAN` devuelven **la misma
cantidad** de filas (≥ 1).

**Lo que medí yo contra la base del seed** (contenedor `gs08-analista-verif`):
```
$ psql -c "select apellidos ilike '%huaman%' ..."      -> q=huaman  -> 0 filas
                                                        -> q=Huamán  -> 1 fila
                                                        -> q=HUAMAN  -> 0 filas
```
Es decir: **sin `unaccent`, las tres variantes NO dan lo mismo** y el criterio queda incumplido aunque el
`ILIKE` esté bien puesto. El dato del seed tiene tilde (`Quispe Huamán`), y en PostgreSQL `ILIKE` ignora
mayúsculas pero **no** tildes.

**La extensión existe pero no está instalada:**
```
$ psql -c "select name, default_version, coalesce(installed_version,'(no instalada)')
           from pg_available_extensions where name='unaccent';"
unaccent | 1.1 | (no instalada)
```
**Con la extensión instalada** (la instalé, medí y la **desinstalé** para dejar la base como estaba):
```
$ psql -c "create extension unaccent;"
$ psql -c "... unaccent(apellidos) ilike unaccent('%huaman%') ..."
estudiantes q=huaman  -> 1
estudiantes q=Huamán  -> 1
estudiantes q=HUAMAN  -> 1
matriculas  q=huaman  -> 2     (las 2 matrículas del estudiante 2; ver nota abajo)
$ psql -c "drop extension unaccent;"
estado final: (no instalada)
```

**Por qué importa y qué falta:** `CREATE EXTENSION` lo puede ejecutar el superusuario (el usuario `gs08` lo
es en el contenedor), así que tiene que ir en **`db/init/`** (un `00-extensiones.sql` o dentro de
`01-schema.sql`, antes de la vista) **y** en la **migración inicial de Alembic** — si solo va en `db/init/`,
vuelven a existir dos verdades del esquema (D-14). Y `D-11` dice «`unaccent` si se quieren tildes», pero
`C-08` lo **exige**: sin extensión, el criterio no se puede aprobar.

**Nota de precisión para los documentos:** la cifra **«`q=huaman` → 2 filas»** de `docs/analisis/datos-seed.md`
es de **matrículas** (`/matriculas?q=huaman`, el estudiante 2 tiene 2 matrículas). En `/api/v1/estudiantes`
el mismo `q` devuelve **1 fila** (una sola persona con ese apellido). Las dos están bien; citadas en el
endpoint equivocado, no.

**VERIFICADO POR MÍ (21/09, después de la corrección de @analista):** `CREATE EXTENSION IF NOT EXISTS
unaccent;` está en `db/init/01-schema.sql` (con la nota del `op.execute` para Alembic). Recreé la base desde
`db/init/` en el contenedor de verificación y medí **1 / 1 / 1**:
```
$ docker exec gs08-analista-verif psql -U gs08 -d gs08_matriculas -c "select extname, extversion from pg_extension where extname='unaccent';"
unaccent | 1.1
$ ... select count(*) from estudiantes where unaccent(apellidos) ilike unaccent('%huaman%');  -> 1
                                     ... ilike unaccent('%Huamán%');                          -> 1
                                     ... ilike unaccent('%HUAMAN%');                          -> 1
```
El log del entrypoint confirma que corrió `04-notas.sql` después de `01`–`03` sin un solo error.

**Estado:** **cerrado en `db/init/` — verificado por mí.** Queda **una mitad abierta**: la misma extensión
tiene que estar en la **revisión inicial de Alembic** (D-14). Hoy `alembic/` no existe, así que eso va con
T1.1 de @dev; cuando esté, lo verifico con `alembic upgrade head` sobre base limpia y `\dx unaccent`.

---

## BUG-08 · `POST /api/v1/matriculas` responde **500** (no 201, no 409)

**Dueño:** @dev · **Gravedad:** **Crítica** · **Criterios:** C-16 y C-17 (y de arrastre todo el recorrido
E2E §3: sin matrícula no hay notas ni boleta).

**Cómo lo encontré (y cómo lo reproduce cualquiera).** La API real ya arranca, así que la corrí:

```
# 1. base limpia desde db/init, en un contenedor aparte (puerto 55433, no toca el stack de @devops)
docker run -d --name gs08-qa-api -e POSTGRES_USER=gs08 -e POSTGRES_PASSWORD=gs08_dev_pwd \
  -e POSTGRES_DB=gs08_matriculas -p 55433:5432 \
  -v "D:/dev/equipo/gs08-matriculas/db/init:/docker-entrypoint-initdb.d:ro" postgres:16.15-alpine3.24
# 2. la API de @dev, sin Docker (venv con backend/requirements.txt)
uv venv D:/dev/_tmp/qa-venv-api --python 3.11
uv pip install -p D:/dev/_tmp/qa-venv-api/Scripts/python.exe -r backend/requirements.txt
cd backend && DATABASE_URL="postgresql+psycopg://gs08:gs08_dev_pwd@localhost:55433/gs08_matriculas" \
  SECRET_KEY="qa-clave-de-prueba" D:/dev/_tmp/qa-venv-api/Scripts/python.exe -m uvicorn app.main:app --port 8010
# 3. el plan de pruebas completo contra la API real
bash scripts/smoke_api.sh --solo-contrato --e2e --url http://localhost:8010
```

**Resultado:** `20 comprobaciones OK, 10 fallas`, y **las 10 fallas salen de estos dos bugs**.

**Pasos mínimos para reproducir el 500**
```
curl -X POST http://localhost:8010/api/v1/auth/login -H 'Content-Type: application/json' \
     -d '{"usuario":"admin","password":"Admin123!"}'          # -> 200 + token
curl -X POST http://localhost:8010/api/v1/matriculas -H 'Content-Type: application/json' \
     -H "Authorization: Bearer <token>" \
     -d '{"estudiante_id":1,"curso_id":1,"periodo":"2026-02","fecha_matricula":"2026-08-01"}'
```
**Esperado:** `409` con el mensaje del legacy (ese par ya existe en el seed).
**Obtenido:** **`500`** `{"detail":"Error interno del servidor (revisar el log del API)."}` — y también `500`
al crear una matrícula **nueva** válida, así que no se puede matricular a nadie por la API.

**Causa exacta (del log del API, no es una suposición):**
```
sqlalchemy.exc.ProgrammingError: (psycopg.errors.AmbiguousParameter) could not determine data type of parameter $4
LINE 1: ...e_id = $1 AND curso_id = $2 AND periodo = $3 AND ($4 IS NULL...
[SQL: SELECT id FROM matriculas WHERE estudiante_id = %(e)s AND curso_id = %(c)s AND periodo = %(p)s
      AND (%(propia)s IS NULL OR id <> %(propia)s)]
[parameters: {'e': 1, 'c': 1, 'p': '2026-02', 'propia': None}]
  File ".../app/routers/matriculas.py", line 143, in crear
    _verificar_duplicado(db, datos.estudiante_id, datos.curso_id, datos.periodo)
  File ".../app/routers/matriculas.py", line 129, in _verificar_duplicado
```
El patrón `AND (:propio IS NULL OR id <> :propio)` con `propio=None` deja a PostgreSQL sin poder tipar el
parámetro: ni el `IS NULL` ni el `<>` le dan tipo. **Falla solo en el INSERT** (en el `PUT` el valor llega).
Arreglo: `CAST(:propio AS integer)` en las dos apariciones, o armar la condición en Python
(`"" if propio is None else " AND id <> :propio"`).

**Evidencia:** `docs/qa/evidencia/api-500-ambiguousparameter.txt` (tracebacks completos) y la corrida
`docs/qa/evidencia/smoke-api-20260921-230607.txt`.

---

## BUG-09 · `POST /api/v1/usuarios` responde **500** (no 201)

**Dueño:** @dev · **Gravedad:** **Crítica** · **Criterios:** C-22 (parte del 409) y C-23 (el 403 por rol: sin
poder crear un `asistente` no hay forma de probarlo).

**Es el mismo defecto en otro archivo** — mismo patrón, mismo SQLSTATE:
```
sqlalchemy.exc.ProgrammingError: (psycopg.errors.AmbiguousParameter) could not determine data type of parameter $3
[SQL: SELECT id, nombre_usuario, email FROM usuarios WHERE (nombre_usuario = %(nombre_usuario)s
      OR lower(email) = lower(%(email)s)) AND (%(propio)s IS NULL OR id <> %(propio)s)]
[parameters: {'nombre_usuario': 'qa_asistente', 'email': 'qa_asistente@horizonte.edu.pe', 'propio': None}]
```
**Reproducir:** `POST /api/v1/usuarios` con los datos del SM-26 (`qa_asistente`, rol `asistente`) → `500`.

**Lo que sí funciona en ese endpoint** (probado a mano, para acotar el arreglo): clave de 7 caracteres →
`422` («RN-01»), rol `docente` → `422`, y `DELETE /api/v1/usuarios/1` (la propia cuenta) → **`409`**
«No puedes desactivar ni eliminar tu propia cuenta (RN-11)» ✔. Lo único roto es el camino que pasa por la
verificación de duplicados.

**Evidencia:** la misma que BUG-08 (`api-500-ambiguousparameter.txt`, parte 2).

---

## Lo que la API real ya cumple (verificado por mí, 21/09)

Además de lo que cubre el smoke, probé a mano lo que el script no alcanzaba:

| Criterio | Prueba | Resultado |
|---|---|---|
| C-11 | DNI repetido, código repetido, email inválido | **422** los tres, con el campo en el mensaje |
| C-13 | `horas=0`; curso **sin** `creditos` | **422**; y guardó **3** (default del legacy) |
| C-14 | código de curso repetido | **409** |
| C-04 | `DELETE` de la propia cuenta | **409** (RN-11) |
| C-24, C-25 | nota 14 → **201**; la misma otra vez → **409**; `nota=21` → **422** | OK |
| C-26 | nota sobre la matrícula 13 (retirada) | **409** «No se registran notas de una matrícula retirada (RN-14)» |
| C-27 | boleta del estudiante 1 | C101 **16.00**; promedio ponderado **13.43** = (16×4 + 10×3) ÷ 7 ✔ |
| C-28 | boleta del estudiante 3 (cursos sin notas) | `nota: null`, `promedio: null`, `creditos_con_notas: 0` |
| C-08 | `q=huaman` / `q=Huamán` (%C3%A1) / `q=HUAMAN` | **1 / 1 / 1** — el `unaccent` funciona |
| — | base de pruebas al terminar | **0 notas / 12 / 7 / 24**: la dejé como el seed |

**OBS-01 cerrada de paso:** la API devuelve `nota: 16.0` **y** `nota_texto: "16.00"`, así que los dos
decimales del criterio C-27 existen como dato, además del valor numérico. Nada que reclamar.

---

## Verificación de los arreglos (lo que corro yo cuando @devops aplique TC-01/TC-02/TC-03)

Un bug no se cierra por decisión: se cierra con la corrida. Estos son los comandos exactos y el resultado
exigido; cuando salgan, cambio el estado a **Cerrado** con la salida pegada.

| Bug | Comando | Resultado exigido |
|---|---|---|
| BUG-01 (TC-01) | `docker compose down -v && docker compose --profile obs up -d && python scripts/verificar_stack.py` (dos veces seguidas, sin provocar ningún 500) | las dos corridas con **exit 0**; los paneles sin serie aparecen como **ADVERTENCIA**, no como FALLA |
| BUG-05 (TC-03) | `curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/health` · `... /metrics` · `... /api/v1/health` | **404**, **404**, **200**; y `curl -s http://localhost:8000/metrics \| head -1` con texto Prometheus |
| BUG-06 (TC-02) | `curl -s -o /dev/null -D - http://localhost:8080/api/v1/health \| grep -i -E 'x-content-type\|x-frame\|referrer\|x-upstream'` | los **4** headers presentes en la respuesta de `/api/` |
| BUG-07 | `psql -c "\dx unaccent"` sobre una base creada desde `db/init/` **y** tras `alembic upgrade head` | la extensión instalada en las dos rutas (una sola fuente de verdad, D-14) |

---

## Lo que verifiqué y **sí** está bien (para no dejar solo malas noticias)

| Qué | Cómo lo verifiqué | Resultado |
|---|---|---|
| Modelo de datos de @analista | re-corrí `db/verificacion/verificar_modelo.sql` contra la base en marcha | **49 OK, exit 0**, incluidas las 15 pruebas negativas |
| Números del seed (12 / 7 / 24 = 23 activas + 1 retirada) | `psql` directo | coinciden; la retirada es la matrícula 13 (estudiante 7, curso 4) |
| Balanceo de nginx | 6 peticiones por el proxy | 3 y 3 entre `172.18.0.5` y `172.18.0.6` |
| **Failover** | apagué `gs08-api-b` y repetí 6 peticiones | **las 6 → HTTP 200** con reintento (`X-Upstream-Addr: .6, .5`); contenedor levantado y `healthy` |
| Headers de seguridad | `curl -D -` a `/healthz` | `Server: nginx` sin versión (`server_tokens off`), `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` — en `/api/` no llegan (BUG-06) |
| Arnés de pruebas (`smoke_api.sh`) | contra una API falsa con 2 defectos plantados | detectó **exactamente** los 2 (17 OK, 2 fallas, exit 1) |
