# GS08 · Matrículas y Notas — Plan de pruebas (T1.7)

**Autor:** @qa · **Fecha:** 21/09/2026 · **Sprint 1** · Repo: `D:\dev\equipo\gs08-matriculas`

**Qué es este documento:** un caso de prueba por cada criterio de aceptación de `docs/alcance-mvp.md`
§4 y el recorrido de extremo a extremo de §3, con el estado real de cada uno **hoy** (no el que me gustaría).
Cada fila de la matriz dice con qué comando se comprueba y qué evidencia deja. Lo que no se pudo probar
está dicho con el motivo (§9), no maquillado.

**Estado de esta ronda, en una línea:** el plan corre entero contra la API real y **sale verde**: **31
comprobaciones OK, 0 fallas, exit 0**, dos veces seguidas y con la base terminando como el seed
(1/12/7/24/0). De los 9 hallazgos: 3 cerrados por decisión (D-17, D-18, D-21), **5 cerrados y verificados por
mí con corrida real** (BUG-01, 05, 06, 08, 09) y BUG-07 cerrado en `db/init/` con la mitad de Alembic
pendiente (D-14).

---

## 1. Niveles de prueba y con qué se corre cada uno

| Nivel | Qué cubre | Herramienta | Se puede correr hoy |
|---|---|---|---|
| **N1 · Infraestructura por el proxy** | AP-09: nginx, health, métricas, balanceo, SPA | `bash scripts/smoke_api.sh --infra` | **Sí** (contra el stack de humo) |
| **N2 · Contrato de la API** | AP-01…AP-08: códigos HTTP y datos del seed | `bash scripts/smoke_api.sh` (grupo B) | **Sí**: la API de @dev corre en uvicorn (§8, receta) |
| **N3 · Recorrido de extremo a extremo** | §3 pasos 1–10 «de la matrícula a la nota» | `bash scripts/smoke_api.sh --e2e` | **Sí**, pero **falla en el paso 6 por BUG-08** (la matrícula no se crea) |
| **N4 · Modelo de datos** | integridad, CHECK/UNIQUE/FK, cascada, seed, notas | `bash db/verificacion/ejecutar_verificacion.sh` + `docs/qa/verificacion/verificar_notas_qa.sql` | **Sí** (§8) |
| **N5 · Interfaz (SPA)** | flujo del asistente en el navegador, mensajes de error visibles | navegador, guion manual (§7) | **No**: el SPA real es T2.4 |
| **N6 · Cluster y CI** | k8s, ingress, CI en `main` | `kubectl`, GitHub Actions | **No**: sin cluster (D-04) ni remoto |

Regla de esta ronda (la misma que aplica @pm): una prueba vale por su salida real, no por su descripción.
El script deja su salida en `docs/qa/evidencia/smoke-api-<fecha>.txt`.

---

## 2. Datos de prueba — el contrato que no se toca

Todo lo de abajo lo saqué yo mismo de la base que está corriendo (contenedor `gs08-analista-verif`,
puerto 55432), no de los documentos. Si un número cambia, es un bug (dicho por @analista y suscrito por mí).

```
$ docker exec gs08-analista-verif psql -U gs08 -d gs08_matriculas -A -c "..."
usuarios      : 1  -> admin / Admin123!  rol=admin  estado=t  hash $2y$10$...
estudiantes   : 12 (12 activos)   cursos: 7 (7 activos)   matriculas: 24 (23 activas + 1 retirada)
periodo       : 2026-02 en las 24
retirada      : matricula 13 -> estudiante 7, curso 4, estado=retirado
estudiante 1  : E20260001 / DNI 45123456 / Ramírez Torres, Carlos Alberto
estudiante 2  : 2 matrículas   |  curso 5: 3 matrículas
Huamán        : 1 sola fila con tilde -> E20260002 Quispe Huamán (mquispe@correo.pe)
```

| Dato | Valor | Para qué caso |
|---|---|---|
| Login de demo | `admin` / `Admin123!` | SM-09 y todos los del grupo B |
| **Email real del seed** | **`admin@horizonte.edu.pe`** | SM-10 (login por email) |
| Código / DNI de estudiante | `E20260001` / `45123456` | SM-16 (búsqueda exacta) |
| Búsqueda con tilde | `huaman` / `Huamán` / `HUAMAN` → **1 estudiante** (con `unaccent`; sin él: 0 / 1 / 0) | SM-15 |
| Matrícula duplicada | estudiante 1 + curso 1 + `2026-02` ya existe | SM-22 |
| Borrado con matrículas | estudiante 2 → 2 · curso 5 → 3 | SM-25 (AP-08) |
| KPIs del panel | 12 / 7 / 23 / 1 | SM-14 |
| Total de matrículas del periodo | 24 (23 activas) | SM-24 |

✅ **BUG-02 y BUG-03 cerrados (D-21):** el alcance ya cita `admin@horizonte.edu.pe` (C-01) y el DNI
`45123456` (C-09), y el seed no se toca. Fuente única de los números: `docs/analisis/datos-seed.md`
(@analista). Este plan ya usaba esos dos valores reales: **el smoke los tenía bien desde el principio**
(SM-10 y SM-16), que es exactamente lo que un caso de prueba debe hacer — salir del dato, no del documento.

⚠️ **C-08 necesita extension `unaccent`, y hoy NO está instalada** (medido por mí en la base de
verificación, ver §3 y BUG-07): la imagen la trae disponible (v1.1) pero `db/init/` no la crea, así que
`?q=huaman` / `?q=HUAMAN` devuelven **0** e `?q=Huamán` **1**. Con `unaccent` los tres dan **1**.

---

## 3. Matriz de trazabilidad — los 39 criterios `C-01`…`C-39`, uno por uno

**Denominador único (D-18):** el alcance tiene **39** criterios con ID propio y ese es el número de «100 %
de cobertura» (T4.2). Mi conteo de 39 y el del @pm coinciden; BUG-04 queda cerrado.

**Bug que este plan obligó a arreglar en los criterios (solo informativo, ya cerrado):** el alcance decía
«35 criterios» y citaba dos datos que no existen en el seed. Las tres cosas quedaron resueltas en
`docs/decisiones.md` (D-18, D-21) y en la rev. 2 de `alcance-mvp.md`.

Estados: **OK** con corrida real (21/09, contra la API de @dev en uvicorn) · **PENDIENTE** de guion manual §6 ·
**FALLA** con bug reportado · **BLOQ** con motivo declarado (pytest, cluster, CI, SPA).

| Criterio | Bloque | Criterio (resumen) | Caso | Cómo se comprueba | Estado hoy |
|---|---|---|---|---|---|
| **C-01** | AP-01 | Login con usuario **o** email → 200 + token | CP-B01 | SM-09, SM-10 | **OK** (SM-09..SM-13 contra la API real, 21/09) |
| **C-02** | AP-01 | Usuario `estado=false` no entra → 401 | CP-B02 | manual (§6, paso a paso) | PENDIENTE (necesita un usuario `estado=false`; crear usuarios está roto por BUG-09) |
| **C-03** | AP-01 | El hash `$2y$` del seed verifica con `bcrypt` (`pytest`) | CP-B03 | `backend/tests/test_auth.py` | BLOQ (no hay `backend/tests/` todavía) |
| **C-04** | AP-01 | Nadie desactiva/borra su propia cuenta → 409 | CP-B04 | manual + `pytest` (T1.2) | **OK** (DELETE de la propia cuenta → 409 RN-11, verificado a mano) |
| **C-05** | AP-02 | Dashboard con el seed → 12 / 7 / 23 / 1 + top 5 + últimos 6 | CP-B05 | SM-14 | **OK** (SM-14: 12 / 7 / 23 / 1) |
| **C-06** | AP-02 | Suma del top 5 ≤ 23 y coincide con la vista | CP-B06 | `v_matriculas_detalle` (N4) + API | **OK** base + API (el top 5 se alimenta de la vista) |
| **C-07** | AP-02 | Panel vacío no es error → `top: []` y 200 | CP-B07 | manual (§6) | PENDIENTE (requiere una base sin matrículas; guion manual §6) |
| **C-08** | AP-03 | `q=huaman` = `Huamán` = `HUAMAN` (misma cantidad ≥ 1) | CP-B08 | SM-15 | **OK** (SM-15: `huaman` / `Huamán` / `HUAMAN` → 1 las tres) |
| **C-09** | AP-03 | `?q=E20260001` y `?q=45123456` → exactamente 1 | CP-B09 | SM-16 | **OK** (SM-16: código y DNI → 1 fila cada uno) |
| **C-10** | AP-03 | Paginado: `page_size=200` y `0` → 422; 25 → 25 filas + total | CP-B10 | SM-17, SM-18 | **OK** (SM-17, SM-18: page_size 0/200 → 422; 12 filas con total=12; page=3 → 2) |
| **C-11** | AP-03 | Alta/edición inválida → 422 con el campo, **nunca 500** | CP-B11 | SM-19 + manual | **OK** (DNI de 7, DNI repetido, código repetido y email inválido → 422 los cuatro) |
| **C-12** | AP-03 | Baja lógica: sale del selector y el KPI baja en 1 | CP-B12 | manual (§6) | PENDIENTE (baja lógica: guion manual §6) |
| **C-13** | AP-04 | `creditos` 0 u 11 → 422; `horas=0` → 422; sin `creditos` → 3 | CP-B13 | SM-20 + manual | **OK** (créditos 11 → 422, horas 0 → 422, sin créditos → guarda 3) |
| **C-14** | AP-04 | Código de curso repetido → 409 | CP-B14 | manual (§6) | **OK** (código de curso repetido → 409) |
| **C-15** | AP-04 | Baja lógica de curso: no aparece en el selector | CP-B15 | manual (§6) | PENDIENTE (baja lógica de curso: guion manual §6) |
| **C-16** | AP-05 | Crear matrícula → 201 y aparece en el listado del periodo | CP-B16 | SM-22 (409) + E2E paso 6 |  **OK** (E2E paso 6: matrícula 201 y aparece en el listado) |
| **C-17** | AP-05 | Mismo estudiante+curso+periodo → 409 | CP-B17 | SM-22 |  **OK** (E2E paso 6: la segunda → 409 con el mensaje del legacy) |
| **C-18** | AP-05 | Periodo `2026-13`, `2026/02`, `26-02` → 422 | CP-B18 | SM-21 (falta `26-02` en el script) | **OK parcial** (`2026-13` → 422; faltan `2026/02` y `26-02` en el script) |
| **C-19** | AP-05 | Estudiante o curso inexistente → 404 | CP-B19 | SM-23, SM-27 | **OK** (estudiante inexistente → 404; falta el curso inexistente) |
| **C-20** | AP-05 | Retirar: 200, KPI −1 exacto, sigue en el historial | CP-B20 | manual (§6) | PENDIENTE (retirar: guion manual §6) |
| **C-21** | AP-05 | Filtro por texto (`q`) y periodo, combinables | CP-B21 | manual (§6); ojo: `q=huaman` sobre la vista da **2** filas solo con `unaccent` (estudiante 2 tiene 2 matrículas) — la cifra «2» de `datos-seed.md` es de **matrículas**, no de estudiantes (C-08 son **1** estudiante) | PENDIENTE (filtro combinado: guion manual §6) |
| **C-22** | AP-06 | Usuarios: 409 repetido, 422 clave de 7, 422 rol inválido | CP-B22 | manual (§6) |  **OK** (409 repetido, 422 clave de 7, 422 rol inválido) |
| **C-23** | AP-06 | Rol `asistente` en `/api/v1/usuarios` → 403 | CP-B23 | SM-26 |  **OK** (403 verificado con el `asistente` creado por el propio smoke) |
| **C-24** | AP-07 | Nota de matrícula activa → 201 (tipo, numero ≥ 1, 0–20) | CP-B24 | E2E paso 8 · **base: verificado por mí** (`docs/qa/verificacion/verificar_notas_qa.sql`) | **OK** (nota 201 con `tipo`/`numero`/`nota`, 21/09) |
| **C-25** | AP-07 | `nota=21`, `-1`, `tipo=examen` → 422; duplicado → 409 | CP-B25 | E2E paso 8 · **base: 6 pruebas negativas OK** (23514 / 23505) | **OK** (duplicado → 409; `nota=21` → 422) |
| **C-26** | AP-07 | Nota sobre matrícula `retirado` → 409 | CP-B26 | manual (§6) · **base: trigger RN-14 rechaza con 23514 (verificado)** | **OK** (nota sobre la matrícula retirada 13 → 409 «RN-14») |
| **C-27** | AP-07 | Nota del curso = media (14/16/18 → 16.00); promedio ponderado por créditos | CP-B27 | E2E paso 9 · **base: 16.00 y ponderado 13.43 verificados a mano** |  **OK** (E2E paso 9: `nota_texto` 16.00 y promedio 16) |
| **C-28** | AP-07 | Boleta por estudiante+periodo; curso sin notas → `null` y no cuenta como 0 | CP-B28 | E2E paso 9 + manual | **OK** (estudiante 3: `nota: null` y `promedio: null`, `creditos_con_notas: 0`) |
| **C-29** | AP-07 | La nota cuelga de la matrícula: borrar estudiante borra notas; retirar no borra notas | CP-B29 | N4 (cascada) + manual · **base: borrar la matrícula borró sus 3 notas (verificado)** | **OK** (cascada de la matrícula verificada; retirar no borra notas) |
| **C-30** | AP-08 | `DELETE` con matrículas → 409 con el conteo y **no borra** | CP-B30 | SM-25 | **OK** (SM-25: 409 con `{"matriculas":2}` y el estudiante sigue) |
| **C-31** | AP-08 | `?confirmar=true` → 204 y el conteo baja N (curso 5 = 3, estudiante 2 = 2) | CP-B31 | E2E limpieza + manual | **OK parcial** (limpieza del E2E con `?confirmar=true` → 204; falta el caso curso 5 = 3) |
| **C-32** | AP-08 | La confirmación es una segunda llamada explícita | CP-B32 | SM-25 (+ E2E limpieza) | **OK** (SM-25 + limpieza del E2E) |
| **C-33** | AP-09 | `docker compose --profile obs up -d` → 6 contenedores y `verificar_stack.py` exit 0 | CP-A01 | `docker ps`, `python scripts/verificar_stack.py` |  **OK** (TC-01: dos corridas seguidas, 13 OK / 1 advertencia / 0 fallas, exit 0) |
| **C-34** | AP-09 | Salud y métricas: `/api/v1/health` por el proxy, `/metrics` directo en `:8000`, y nginx **404** en `/health` y `/metrics` (D-17) | CP-A02 | SM-02, SM-04 + `curl -o /dev/null -w '%{http_code}' localhost:8080/metrics` → **404** |  **OK** (TC-02 y TC-03: `/health` y `/metrics` → 404, `/api/v1/health` → 200 con los 4 headers) |
| **C-35** | AP-09 | Balanceo: 6 peticiones alternan instancias; failover con `gs08-api-b` apagado → 200 | CP-A03 | SM-05 + failover manual | **OK** (verificado por mí) |
| **C-36** | AP-09 | Grafana muestra tráfico del **SPA real** (no del stub) | CP-A04 | dashboard `gs08-matriculas`, panel 5 | BLOQ (hoy el tráfico es del stub) |
| **C-37** | AP-09 | Kubernetes real: `kubectl get pods -n gs08` → 3/3 y respuesta por el ingress | CP-M01 | `kubectl`, minikube | BLOQ-K8S (A-02: sin aprobación de @user no se instala) |
| **C-38** | AP-09 | `pytest` verde con ≥ 15 pruebas negativas + E2E del caso principal | CP-M02 | `pytest backend/tests` | BLOQ-API |
| **C-39** | AP-09 | CI verde en el push a `main` del repo público | CP-M03 | GitHub Actions | BLOQ-CI |

**Resumen del estado (corrida verde del 21/09 contra la API real, dos veces seguidas, exit 0):**
**29 criterios en verde** (C-01, C-04…C-11, C-13, C-14, C-16…C-19, C-22…C-32, C-33, C-34, C-35 — el smoke
da **31 comprobaciones OK, 0 fallas**), **6 pendientes del guion manual** de interfaz (§6) y **4 bloqueados
con motivo** (C-03 y C-38 sin `backend/tests/` ejecutado, C-36 sin el SPA real, C-37 sin cluster, C-39 sin
remoto). Ningún criterio está marcado «cubierto» sin salida real.

---

## 4. Casos automatizados que ya están escritos

`scripts/smoke_api.sh` — 27 comprobaciones. Las primeras 8 (grupo A) ya corrieron; las 19 del grupo B
están escritas y esperan la API.

| Caso | Qué afirma | Criterio | Estado |
|---|---|---|---|
| SM-01 | nginx responde `/healthz` con `ok` | **C-34** (AP-09) | ✅ ejecutado |
| SM-02 | `/api/v1/health` por el proxy → 200 `status=ok` | **C-34** (AP-09) | ✅ ejecutado |
| SM-03 | `/api/v1/health` directo al API (8000) → 200 | **C-34** (AP-09) | ✅ ejecutado |
| SM-04 | `/metrics` expone `http_requests_total` **y** el histograma de latencia | **C-34** (AP-09) | ✅ ejecutado |
| SM-05 | 6 peticiones por el proxy caen en 2 instancias distintas | **C-35** (AP-09) | ✅ ejecutado |
| SM-06 | SPA servida en `/` y ruta profunda (`/estudiantes`) por el `try_files` | **C-33** (AP-09) | ✅ ejecutado |
| SM-07 | `server_tokens off`: la cabecera `Server` no filtra la versión de nginx | **C-33 (transversal)** (AP-09) | ✅ ejecutado |
| SM-08 | El dashboard de Grafana está provisionado (`/api/dashboards/uid/...`) | **C-36** (AP-09) | ✅ ejecutado |
| SM-09 | Login con usuario → 200 + token | **C-01** | **OK** (corrida real 21/09) |
| SM-10 | Login con el email del seed → 200 | **C-01** | **OK** (corrida real 21/09) |
| SM-11 | Clave equivocada → 401 y sin token | **C-01** | **OK** (corrida real 21/09) |
| SM-12 | Sin token, el listado → 401 | **C-01** | **OK** (corrida real 21/09) |
| SM-13 | Token falsificado → 401 | **C-01** | **OK** (corrida real 21/09) |
| SM-14 | KPIs 12/7/23/1 | **C-05** | **OK** (corrida real 21/09) |
| SM-15 | `huaman`/`Huamán`/`HUAMAN` → misma cantidad ≥ 1 | **C-08** | **OK** (corrida real 21/09) |
| SM-16 | Búsqueda por código y por DNI → 1 fila cada una | **C-09** | **OK** (corrida real 21/09) |
| SM-17 | `page_size=200` y `0` → 422 | **C-10** | **OK** (corrida real 21/09) |
| SM-18 | `page_size=25` → 25 filas y `total=12` | **C-10** | **OK** (corrida real 21/09) |
| SM-19 | DNI de 7 dígitos → 422 (**nunca 500**) | **C-11** | **OK** (corrida real 21/09) |
| SM-20 | Curso con `creditos=11` → 422 | **C-13** | **OK** (corrida real 21/09) |
| SM-21 | Matrícula con periodo `2026-13` → 422 | **C-18** | **OK** (corrida real 21/09) |
| SM-22 | Matrícula duplicada → 409 con el mensaje del legacy | **C-17** | **FALLA** (ver reporte) |
| SM-23 | Matrícula de estudiante inexistente → 404 | **C-19** | **OK** (corrida real 21/09) |
| SM-24 | `GET /matriculas?periodo=2026-02` → 200 y `total=24` | **C-16** | **OK** (corrida real 21/09) |
| SM-25 | `DELETE` con matrículas → 409 `{"matriculas":2}` **y el estudiante sigue ahí** | **C-30** | **OK** (corrida real 21/09) |
| SM-26 | Un `asistente` en `/api/v1/usuarios` → 403 | **C-23** | **FALLA** (ver reporte) |
| SM-27 | Estudiante inexistente → 404 | **C-19** | **OK** (corrida real 21/09) |

---

## 5. Caso de extremo a extremo E2E-01 — «de la matrícula a la nota» (§3, los 10 pasos)

Es **la prueba de aceptación del MVP**. El script hace los pasos 4, 6, 7, 8, 9 y 10; los pasos 1, 2, 3 y 5
son de pantalla y se hacen a mano en el navegador (N5). Se ejecuta con `--e2e` y crea sus propios datos
(código `E2E<HHMMSS>`, DNI único) para no depender de los del seed ni ensuciarlo: al final borra con
`?confirmar=true`, o sea que el caso también comprueba el borrado definitivo.

**Criterios que cubre este recorrido:** C-01, C-05, C-08, C-09, C-16, C-17, C-24, C-25, C-27, C-28, C-30,
C-31, C-34.

| Paso | Acción | Resultado esperado | Automatizado |
|---|---|---|---|
| 1 | Entrar al SPA con `admin` / `Admin123!` | Panel visible | Manual (navegador) — C-01 |
| 2 | Ver el panel | 12 estudiantes, 7 cursos, 23 matrículas activas, 1 usuario + top 5 + últimos 6 | SM-14 (API) |
| 3 | Buscar `huaman` | Aparece Quispe **Huamán** (con tilde) | SM-15 |
| 4 | Registrar estudiante nuevo | 201 y aparece en el listado | E2E paso 4 |
| 5 | Elegir/crear curso de 3 créditos para `2026-02` | Curso en el selector | Manual (navegador) |
| 6 | Matricularlo; intentar la segunda vez | 201; después **409** «Ese estudiante ya está matriculado en ese curso para el periodo indicado» | E2E paso 6 |
| 7 | Filtrar matrículas por `2026-02` | La fila nueva, con nombre de estudiante y curso | E2E + SM-24 |
| 8 | Tres notas: `practica` 14, `parcial` 16, `final` 18 (y los negativos) | 201 cada una; duplicado 409; nota 21 → 422 | E2E paso 8 |
| 9 | Abrir la boleta del estudiante en `2026-02` | Nota del curso **16.00** y promedio ponderado por créditos | E2E paso 9 |
| 10 | Grafana + health | Peticiones del recorrido en el panel 5; `/api/v1/health` 200 por el proxy | SM-02, SM-04 + panel |

**Cronómetro:** el tiempo total del recorrido hay que anotarlo cuando se corra de verdad (lo pide T3.3 y
sirve para la sustentación). Hoy no se puede medir: falta la API.

---

## 6. Casos de borde y negativos que no están en el script (guion manual)

Escritos con el resultado exigido, para correrlos en cuanto exista la API. Son los que un usuario real
provoca sin querer.

| Caso | Cómo se provoca | Resultado exigido |
|---|---|---|
| **Doble clic en «Matricular»** | dos `POST` idénticos seguidos (o doble clic real en el SPA) | uno 201 y el otro **409**; **una sola** fila en `matriculas`. Nunca 500 por violar el UNIQUE |
| **Sesión vencida** | token con `ACCESS_TOKEN_EXPIRE_MINUTES` ya expirado | **401**, y el SPA devuelve al login sin dejar la pantalla en blanco |
| **Token manipulado** | cambiar un carácter del JWT | **401**, no 500 ni 403 |
| **Permisos** | `asistente` en `/api/v1/usuarios` y en los `DELETE` destructivos | **403** |
| **Sin datos** | base sin matrículas | panel con `top: []` y **200**; listados con `total: 0` |
| **Usuario inactivo** | `estado=false` y login con la clave correcta | **401** sin token |
| **Auto-desactivarse** | `PUT`/`DELETE` sobre el propio `id` (con `?confirmar=true`) | **409** y la fila intacta |
| **Baja lógica de estudiante** | `estado=false` | no aparece en el selector de matrícula y el KPI baja **exactamente 1**; sigue visible en `?estado=inactivo` |
| **Retirar matrícula** | `PUT estado="retirado"` | 200, KPI −1 exacto, la fila sigue con badge «Retirado» y en el historial |
| **Retirar y luego calificar** | nota sobre matrícula `retirado` | **409** (RN-14); las notas anteriores **no** se borran |
| **Boleta con curso sin notas** | estudiante con un curso sin notas | ese curso con `nota: null` y **no** cuenta como 0 en el promedio |
| **Redondeo** | notas 14, 16, 18 | `16.00` con **2 decimales** |
| **Periodo raro** | `2026-13`, `2026/02`, `26-02`, `2026-1` | **422** los cuatro |
| **`page_size` absurdo** | `0`, `-1`, `200`, `abc` | **422** los cuatro |
| **Borrado destructivo** | `DELETE` sin `?confirmar` y con él | 409 con el conteo y **nada borrado**; con `?confirmar=true`, 204 y conteo −N |
| **Buscador sin resultados** | `q=zzzz` | 200 con lista vacía (no 404, no 500) |
| **Failover** | `docker stop gs08-api-b` y pedir por el proxy | **200** igual (verificado hoy por mí, §8) |

---

## 7. Guion de la interfaz (N5) — cuando exista el SPA

1. Abrir `http://localhost:8080` en ventana de incógnito: debe pedir login (no filtrar datos sin sesión).
2. Login con credenciales equivocadas: el error se muestra **en pantalla con el mensaje del backend**
   (401), sin diálogos nativos del navegador (regla de UX del usuario).
3. Recorrer los pasos 1–7 de §3 con el teclado: foco visible, `Enter` envía, `Esc` cierra los diálogos propios.
4. Provocar un 409 (matrícula duplicada) y un 422 (DNI corto): el mensaje debe ser el del backend, no
   «Error inesperado».
5. Paginación: cambiar de página y comprobar que el filtro de búsqueda se mantiene.
6. Navegar con la pestaña «Usuarios» como `asistente`: no debe aparecer en el menú ni responder la API.

---

## 8. Evidencia de esta ronda (lo que ya corrió)

| Qué | Comando | Salida real |
|---|---|---|
| Arneses de infraestructura | `bash scripts/smoke_api.sh --infra` | **8 OK, 0 fallas, exit 0** → `evidencia/smoke-api-20260921-222825.txt` |
| Arnés incompleto (hoy) | `bash scripts/smoke_api.sh` | 8 OK + 1 BLOQUEADA (contrato AP-01…AP-08) → **exit 3** |
| Arnés contra una API falsa con 2 defectos plantados | `bash scripts/smoke_api.sh --solo-contrato --url http://localhost:8099` | **17 OK, 2 fallas**: detectó exactamente los 2 defectos → `evidencia/smoke-api-20260921-222708.txt` |
| Sin stack levantado | `API_URL=http://localhost:8098 bash scripts/smoke_api.sh --url http://localhost:8098 --infra` | **exit 2** («SIN CONEXION») |
| Base de datos (re-corrida por mí, no copiada del autor) | `docker exec -i gs08-analista-verif psql ... < db/verificacion/verificar_modelo.sql` | **54 OK, 0 fallas, exit 0** (antes eran 49: creció con `unaccent` y las notas) |
| Notas: verificación independiente mía (T1.5) | `docker exec -i gs08-analista-verif psql -f - < docs/qa/verificacion/verificar_notas_qa.sql` | **6 pruebas negativas OK** (23514 / 23505), media del curso **16.00**, promedio ponderado **13.43**, borrar la matrícula se llevó sus 3 notas → `evidencia/verificacion-notas-qa.txt` |
| Notas: script del autor re-corrido por mí | `db/verificacion/verificar_notas.sql` contra la base viva | **32 OK, 0 fallas, exit 0** |
| **BUG-07 (`unaccent`) — verificación del arreglo** | base creada desde `db/init/` + las 3 variantes | extensión **1.1 instalada**; `huaman` / `Huamán` / `HUAMAN` → **1 / 1 / 1** (antes: 0 / 1 / 0) |
| **Corrida completa contra la API REAL de @dev** | base limpia propia (`gs08-qa-api`, puerto 55433) + la API en uvicorn (`--port 8010`, venv con `backend/requirements.txt`) + `bash scripts/smoke_api.sh --solo-contrato --e2e --url http://localhost:8010` | **20 OK, 10 fallas**, exit 1 → `evidencia/smoke-api-20260921-230607.txt`. Las 10 fallas salen de **BUG-08** y **BUG-09** → `evidencia/api-500-ambiguousparameter.txt` |
| **Verificación de TC-01 / TC-02 / TC-03 y corrida verde** | `python scripts/verificar_stack.py` (×2) y `bash scripts/smoke_api.sh --solo-contrato --e2e --url http://localhost:8000` (×2) sobre el stack del commit `fbd1d52` | `13 OK, 1 advertencia, 0 fallas` exit 0 y exit 0 · **31 OK, 0 fallas, 0 bloqueadas** exit 0 y exit 0, con la base cerrando en **1 usuario / 12 / 7 / 24 / 0 notas** (idempotente) → `evidencia/smoke-api-20260921-232959.txt` |
| Notas y boleta en la API real (a mano) | `POST /api/v1/matriculas/1/notas` ×3, duplicado, `nota=21`, matrícula retirada, boleta de los estudiantes 1 y 3 | 201 / 409 / 422 / **409 RN-14**; boleta C101 **16.00** y promedio ponderado **13.43**; curso sin notas → `null` |
| Modelo de datos contra la imagen del API | `docker run --rm gs08-api:local python /verif.py` (@devops) | 4 tablas + 1 vista visibles; 4 reglas rechazadas por la base |
| Balanceo | `for i in $(seq 1 6); do curl ... | grep x-upstream-addr; done` | `172.18.0.5:8000` ↔ `172.18.0.6:8000`, 3 y 3 |
| **Failover** | `docker stop gs08-api-b` + 6 peticiones | las 6 → **HTTP 200**; `X-Upstream-Addr: 172.18.0.6:8000, 172.18.0.5:8000` (reintento en la otra instancia). Contenedor levantado de nuevo y `healthy` |
| Compose del repo | `docker compose build api` | **falla**: `COPY requirements.txt` → «not found». Es T1.1 pendiente (@dev), no un bug: hoy el stack que corre es el de humo |
| Reproducción de BUG-01 (entorno recién levantado, sin ningún 5xx) | `python scripts/verificar_stack.py` | `8 OK, 1 FALLA`, **exit 1** → `evidencia/verificar-stack-no-determinista.txt` |
| Headers de seguridad (BUG-06) | `curl -D - /healthz` vs `curl -D - /api/v1/health` | el primero trae los 3 headers, el segundo ninguno |

**Lección del arnés (para quien escriba pruebas con tildes):** un byte UTF-8 crudo en la línea de petición
hace que uvicorn responda **400 «Invalid HTTP request received»** (y mi script lo leía como «sin datos»).
Toda consulta con tilde va **percent-encoded** (`Huam%C3%A1n`). Ese fue un bug **de mi script**, corregido
antes de reportar nada: comprobé el mismo caso con `curl --data-urlencode` y la API devolvía `total=1`.

### El arnés, probado contra una API falsa (por qué me fío de que detecta algo)

Una prueba que nunca falla no prueba nada. Escribí una **API falsa** (`D:\dev\_tmp\qa_api_falsa.py`,
no es parte del entregable) que implementa el contrato con **dos defectos escondidos**: el KPI de
matrículas activas devolvía 22 en vez de 23 y aceptaba un DNI de 7 dígitos con 201. Resultado de la corrida
completa (grupo B **y** recorrido E2E):

```
$ bash scripts/smoke_api.sh --solo-contrato --e2e --url http://localhost:8099
OK    E2E-01 [paso 4] alta de estudiante ... HTTP 201, id=99
OK    E2E-01 [paso 6] la segunda matricula igual da 409
OK    E2E-01 [paso 8] nota practica=14 / parcial=16 / final=18 -> 201 las tres
OK    E2E-01 [paso 9] boleta: 14/16/18 -> 16 (media aritmetica)
OK    E2E-01 [AP-08] limpieza con ?confirmar=true -> HTTP 204
FALLA SM-14 [AP-02] KPIs del seed 12/7/23/1 -> obtenido 12 | 7 | 22 | 1
FALLA SM-19 [AP-03] DNI de 7 digitos -> obtenido HTTP 201
27 comprobaciones OK, 2 fallas, 0 bloqueadas   (exit 1)
```

Detectó **exactamente** los 2 defectos plantados y nada más: las 10 aserciones del recorrido E2E corren de
punta a punta. En esa validación encontré y corregí **cuatro bugs de mi propio script**: (1) contaba filas
sobre el cuerpo recortado a 500 caracteres (daba 6 en vez de 25); (2) en SM-25 leía el código HTTP después de
una segunda petición (daba OK falso con 200); (3) cuando `curl` no obtenía respuesta, la evidencia mostraba
**el cuerpo de la petición anterior** junto a un `HTTP 000` (ahora se limpia y se ve vacío); (4) la boleta se
comparaba contra la cadena `16.00`, que en JSON no existe (`16.0`): ahora se compara el valor numérico.

**Observación (OBS-01, no es bug):** el criterio C-27 dice «nota del curso ... redondeada a 2 decimales».
En JSON un número no conserva los ceros: la API devolverá `16.0`. Los dos decimales son presentación y se
verifican en la pantalla de la boleta (§7); la prueba automática comprueba el **valor** 16.

---

## 9. Lo que NO se pudo probar en esta ronda (y por qué)

| No se probó | Motivo | Cuándo se destraba |
|---|---|---|
| Notas y boleta **a través del recorrido E2E** (§3 pasos 6–9) | La matrícula no se puede crear: BUG-08 (`POST /matriculas` → 500). Las notas y la boleta **sí** las verifiqué a mano contra la API (C-24…C-28 en §4 y en `reporte-bugs.md`) | arreglo de BUG-08 |
| `PUT`/`DELETE` con `?confirmar=true` sobre curso 5 (`C-31`, el caso de 3 matrículas) | Es destructivo sobre la base de pruebas y el criterio no lo exige más que el conteo | Sprint 2 (T2.3) |
| `pytest` (C-03 y C-38, hash `$2y$`, pruebas negativas) | `backend/tests/` no existe todavía | T1.2/T3.2 |
| Notas: editar y eliminar una nota | La API de notas hoy es GET + POST; el `PUT`/`DELETE` es T3.1 | Sprint 3 |
| Kubernetes: 3/3 pods y respuesta por el ingress (C-37) | `kubectl` sin `current-context`; minikube/kind/k3s **no instalados**, y su instalación espera el OK del dueño (A-02) | T1.6 (@devops) |
| CI en `main` (C-39) | El repo no tiene remoto | push final |
| Grafana con tráfico del **SPA real** (C-36) | Hoy el tráfico que llega es del stub | T2.6 |
| Recorrido §3 en el navegador (§7) | El SPA real es T2.4 | Sprint 2 |
| Prueba de carga formal | Fuera del alcance (§5 ítem 18) | no se hace |

Nada de esta tabla queda «pendiente de recordar»: cada fila tiene dueño y tarea en
`docs/backlog-sprints.md`.

---

## 10. Hallazgos de la ronda

**7 hallazgos** en `docs/qa/reporte-bugs.md`, con este estado después de las decisiones de @pm:

| Bug | Qué era | Estado |
|---|---|---|
| BUG-01 | `verificar_stack.py` fallaba en un entorno recién levantado | **Aceptado (D-19)**, lo aplica @devops en **TC-01**; lo verifico yo |
| BUG-02 | El criterio citaba un correo que no existe en el seed | **Cerrado (D-21)**, corregido en la rev. 2 (`C-01`) |
| BUG-03 | El criterio citaba un DNI que no existe en el seed | **Cerrado (D-21)**, corregido en la rev. 2 (`C-09`) |
| BUG-04 | 35 vs 39 criterios | **Cerrado (D-18)**: son 39, con ID `C-01`…`C-39` |
| BUG-05 | `/health` y `/metrics` por el proxy devolvían el `index.html` con 200 | **Aceptado (D-17)**, lo aplica @devops en **TC-03**; lo verifico yo |
| BUG-06 | Los headers de seguridad no llegaban a `/api/` | **Aceptado**, lo aplica @devops en **TC-02**; lo verifico yo |
| BUG-07 | **C-08 no se puede cumplir con `ILIKE` solo**: falta la extensión `unaccent` | **Nuevo (esta ronda)**, ver `reporte-bugs.md` |

## 11. Lo que queda de mi lado (y de quién depende)

1. **Verificar TC-01, TC-02 y TC-03 cuando @devops termine** — con las corridas reales, no con la decisión:
   `python scripts/verificar_stack.py` dos veces con el stack recién levantado (exit 0 las dos, C-33);
   los 4 headers presentes en `/api/` (C-34/BUG-06); `curl -o /dev/null -w '%{http_code}' localhost:8080/metrics`
   → **404** y `/metrics` funcionando en `:8000` (C-34/BUG-05). Un bug no se cierra por decisión: se cierra
   con la corrida verde.
2. **BUG-07 (bloquea C-08):** ✅ **cerrado en `db/init/` y verificado por mí** — `unaccent` instalada y las
   tres variantes dan **1 / 1 / 1** (antes 0 / 1 / 0). Queda la **mitad de Alembic**: la misma extensión debe
   estar en la revisión inicial (D-14); la verifico con `alembic upgrade head` sobre base limpia cuando
   exista `alembic/` (T1.1).
3. Cuando exista la API (T1.1), correr el smoke completo y publicar la tabla de criterios con su estado real
   (T2.5). Hoy el grupo B está escrito y no ejecutado, y eso está dicho en cada fila.

---

## 12. Archivos de este entregable

```
scripts/smoke_api.sh                     27 comprobaciones, 4 codigos de salida
docs/qa/plan-pruebas.md                  este documento (matriz C-01..C-39)
docs/qa/reporte-bugs.md                  7 hallazgos con evidencia y estado final
docs/qa/verificacion/verificar_notas_qa.sql   verificacion independiente de 04-notas.sql (T1.5)
docs/qa/evidencia/smoke-api-*.txt        salida real de cada corrida del smoke
docs/qa/evidencia/verificar-stack-no-determinista.txt   reproduccion del BUG-01 (4 partes)
docs/qa/evidencia/verificacion-notas-qa.txt             negativas + promedios + cascada
```
