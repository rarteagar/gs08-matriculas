# GS08 · Matrículas y Notas — Backlog por sprints y reparto de tareas

**Autor:** @pm · **Fecha:** 21/09/2026 · **Sprint 0** · Repo: `D:\dev\equipo\gs08-matriculas`

**Cómo se lee esto.** El backlog es el **mapa**; en la sala reparto **una tarea por persona y no arranco
la siguiente hasta que llegue la evidencia de la anterior**. Cada tarea tiene: qué se entrega (archivo o
artefacto), con qué se prueba y **qué evidencia hay que pegar** (salida real de comando, exit code, ruta
del archivo o captura). Nada se marca terminado por decir que está hecho.

**Regla de evidencia (la aplico a todos, incluido yo):** el mensaje de cierre de una tarea trae la salida
real pegada, no un resumen de intención. Los dos ejemplos que ya están en el repo son el estándar:
`bash db/verificacion/ejecutar_verificacion.sh` con **exit 0 / 49 OK** (@analista) y
`python scripts/verificar_stack.py` con **9 OK, 0 fallas** (@devops).

**Nota sobre el calendario:** los 4 sprints son **bloques de alcance, sin fechas**, porque todavía no
tengo la fecha de entrega ni de exposición (pregunta abierta de `alcance-mvp.md` §7). Con esa fecha los
convierto en semanas y digo qué se corta primero: el orden de corte es T3.x (notas) → T4.1 (k8s lo último
que se corta, porque es requisito del curso).

---

## Sprint 0 — cerrado (21/09/2026)

| Entregable | Dueño | Estado | Evidencia |
|---|---|---|---|
| Alcance del MVP, «no se hace», criterios de aceptación | @pm | ✅ | `docs/alcance-mvp.md` (este sprint) |
| Backlog y reparto | @pm | ✅ | `docs/backlog-sprints.md` |
| Modelo de datos + migraciones leídas de `legacy/` | @analista | ✅ | `db/init/*.sql`, `db/verificacion/`, 49 OK exit 0 |
| Plan de contenedores, CI y observabilidad | @devops | ✅ | `docker-compose.yml`, `.github/workflows/`, `k8s/`, 9 OK exit 0 |
| Repo con historial en `main` y `legacy/` importado | @devops | ✅ | commits `9ef7c26`, `8d9b3bd`, `c946d81`, `e051d43` |
| Verificación cruzada esquema ↔ imagen del API (4 tablas + vista visibles, reglas rechazadas por la base) | @devops | ✅ | `docs/devops/evidencia-sprint0.md` (§6) |
| Plan de pruebas con matriz de criterios + E2E + 6 bugs; smoke de 27 comprobaciones con 4 códigos de salida | @qa | ✅ | `docs/qa/plan-pruebas.md`, `reporte-bugs.md`, `scripts/smoke_api.sh` (infra 8 OK exit 0) |
| Datos del seed oficiales (12/7/24, códigos, DNI, matrículas por curso) | @analista | ✅ | `docs/analisis/datos-seed.md` |
| **Alcance corregido:** 39 criterios con ID único (`C-01`…`C-39`), correo `admin@horizonte.edu.pe`, DNI `45123456`, salud/métricas (D-17) | @pm | ✅ | `docs/alcance-mvp.md` rev. 2 (BUG-02/03/04/05 cerrados) |
| Tabla de decisiones movida a la raíz de `docs/` y ampliada a 23 decisiones (D-00…D-22) | @pm | ✅ | `docs/decisiones.md` |

**Lo que Sprint 0 deja bloqueado y por qué (dicho sin adornos):** Kubernetes real no existe todavía
(`kubectl` sin `current-context`, minikube/kind/k3s no instalados — lo verifiqué yo mismo) y el push al
repo público no se hizo (no hay remoto). Todo lo demás del sprint 0 está ejecutado y verificado.

---

## Sprint 1 — API núcleo y cluster local

*Criterio de terminado del sprint: la API responde autenticación, estudiantes, cursos y dashboard contra
PostgreSQL real en contenedores, con `pytest` verde y evidencia pegada; y existe un cluster local con la
app desplegada.*

| ID | Tarea | Dueño | Entregable | Criterio de terminado (evidencia obligatoria) |
|---|---|---|---|---|
| **T1.1** | Esqueleto del backend + Alembic. `backend/app/main.py` con `uvicorn app.main:app`, `/health`, `/api/v1/health`, `/metrics` (instrumentator), puerto 8000, `requirements.txt` y `package-lock.json` commiteados, versiones del contrato de @devops §3 | @dev | `backend/`, `alembic/` | `curl -s localhost:8000/api/v1/health` → **200** `{"status":"ok"}`; `/metrics` devuelve texto Prometheus; **`alembic upgrade head` sobre base limpia deja las 4 tablas + la vista, y no quedan diferencias contra `db/init/`** (una sola fuente de verdad) |
| **T1.2** | Autenticación: `POST /api/v1/auth/login` con usuario **o** email, bcrypt verificando el `$2y$` del seed, usuario inactivo no entra, nadie se desactiva a sí mismo | @dev | endpoints + `backend/tests/test_auth.py` | test `bcrypt.checkpw(b'Admin123!', hash_seed) → True`; login con clave mala → **401**; usuario inactivo con clave buena → **401**; `PUT`/`DELETE` sobre el propio id → **409** |
| **T1.3** | Estudiantes y cursos: listado paginado, buscador **`ILIKE`** (código, DNI, nombres, apellidos), alta/edición, baja lógica, `422`/`409` | @dev | endpoints + tests | `?q=huaman` = `?q=Huamán` = `?q=HUAMAN` (misma cantidad ≥ 1, con `LIKE` daría 0); DNI de 7 dígitos → **422** y **nunca 500**; `page_size=200` → **422** |
| **T1.4** | Dashboard: 4 KPIs + top 5 cursos + últimos 6 estudiantes, leyendo la vista `v_matriculas_detalle` | @dev | `GET /api/v1/dashboard` | con el seed devuelve **12 / 7 / 23 / 1**; la suma del top 5 ≤ 23; sin matrículas responde **200** con `[]` |
| **T1.5** | Notas: `db/init/04-notas.sql`, `v_notas_detalle`, RN-14 (no se califica matrícula retirada) y RN-15 (media del curso / promedio ponderado por créditos), casos CU-14 y CU-15, y extender la verificación | @analista | `04-notas.sql`, `v_notas_detalle`, §7 y §4 de `modelo-datos.md` actualizados | `bash db/verificacion/ejecutar_verificacion.sh` **exit 0** con las comprobaciones nuevas, incluidas 3 pruebas negativas: `nota=21`, duplicado `(matricula,tipo,numero)`, nota sobre matrícula retirada |
| **T1.6** | **Minikube con driver docker** + addon ingress + desplegar `k8s/` | @devops | cluster local + evidencia | `kubectl get pods -n gs08` → **3/3 Running**; `kubectl get job gs08-migraciones` → **Complete**; `curl` por el ingress → **200**. Si minikube no arranca en Windows: plan B `kind` y me avisas antes de gastar tiempo |
| **T1.7** | Plan de pruebas: un caso por cada criterio de aceptación de `alcance-mvp.md` §4 + la prueba de extremo a extremo del §3, y script de humo de API | @qa | `docs/qa/plan-pruebas.md` + `scripts/smoke_api.sh` | el script corre contra la API real y sale **exit 0**; cada criterio del alcance tiene su caso y su estado (cubierto / no cubierto / bloqueado) |
| **T1.8** | Esqueleto del informe: carátula, índice, arquitectura, modelo de datos, infraestructura, observabilidad | @documentador | `docs/informe/` (DOCX + PDF) | el informe incorpora las tablas y salidas **reales** de @devops, @analista y este sprint; **cero cifras inventadas** (lo que no esté verificado va marcado «pendiente») |

---

## Sprint 2 — Matrículas, usuarios y SPA

*Criterio de terminado: el caso principal (§3) se puede hacer completo desde el navegador, menos las notas.*

| ID | Tarea | Dueño | Entregable | Criterio de terminado |
|---|---|---|---|---|
| **T2.1** | Matrículas: listado con la vista + filtro por texto y periodo, alta, edición, **retirar** (baja lógica), `409` por duplicado, `404` por FK | @dev | endpoints + tests | duplicado → **409** con el mensaje del legacy; `2026-13` → **422**; retirar baja el KPI en **exactamente 1** y la fila sigue en el historial |
| **T2.2** | Usuarios: listar/crear/editar/desactivar, `nombre_usuario` único, `403` para rol `asistente` | @dev | endpoints + tests | `asistente` llamando `/api/v1/usuarios` → **403**; contraseña de 7 → **422**; clave ≥ 8 → hash bcrypt guardado |
| **T2.3** | Borrados destructivos con confirmación (decisión D-02) | @dev | endpoints | `DELETE` sin `?confirmar` con matrículas → **409** con `{"matriculas":N}` y **no borra**; con `?confirmar=true` → **204** y el conteo baja N; comprobado con el seed (curso 5 = 3, estudiante 2 = 2) |
| **T2.4** | SPA Vue 3 + Vite + Tailwind: login, layout con menú por rol, panel con KPIs y barras, listados + formularios de estudiantes, cursos, matrículas y usuarios, buscador, paginación, badges de estado | @dev | `frontend/src/` | recorrido §3 pasos 1–7 completo en el navegador sobre `http://localhost:8080`; errores de la API mostrados en la pantalla con el mensaje del backend (409/422), **sin diálogos nativos** |
| **T2.5** | Ejecutar el plan de pruebas de T1.7 sobre la API + SPA y reportar bugs | @qa | `docs/qa/reporte-bugs.md` | cada bug con pasos, esperado, obtenido y evidencia; los criterios no cubiertos quedan marcados como tal |
| **T2.6** | Retirar el stub de humo e integrar la API real al compose; reverificar balanceo, failover y paneles con datos reales | @devops | compose + evidencia | `verificar_stack.py` **exit 0** con la API de @dev; balanceo alternando instancias y failover **200** con `gs08-api-b` apagado; paneles de Grafana con tráfico del SPA real |

---

## Sprint 3 — Notas y boleta

*Criterio de terminado: el caso principal completo (pasos 1–10), incluida la boleta.*

| ID | Tarea | Dueño | Entregable | Criterio de terminado |
|---|---|---|---|---|
| **T3.1** | Notas: registrar/editar/eliminar nota por matrícula activa (`practica\|parcial\|final`, `numero ≥ 1`, `nota` 0–20) y boleta por estudiante+periodo con nota del curso y promedio ponderado por créditos | @dev | endpoints + pantalla de boleta | nota 21 → **422**; duplicado → **409**; matrícula retirada → **409**; boleta 14/16/18 → nota **16.00**; curso sin notas → `null` y no cuenta como 0 |
| **T3.2** | Tests de notas y promedios, incluidos redondeo a 2 decimales y boleta sin notas | @dev | `backend/tests/test_notas.py` | `pytest` verde; el caso de la boleta del seed coincide con lo que devuelve `psql` calculado a mano |
| **T3.3** | Regresión + casos nuevos de notas/boleta + cronometrar el recorrido completo | @qa | reporte actualizado | el recorrido §3 (10 pasos) se completa con evidencia; se anota cuánto tarda (dato para la sustentación) |
| **T3.4** | Verificar que las reglas RN-14/15 se cumplen **en la API**, no solo en la base, y actualizar `modelo-datos.md` | @analista | doc actualizado | tabla de reglas con la columna «dónde se aplica» completa; cada regla con su prueba |
| **T3.5** | Manual de instalación y de uso + sección de notas del informe | @documentador | manual + informe | instalación reproducible desde cero en una máquina limpia, con los pasos que realmente funcionaron |

---

## Sprint 4 — Cierre, Kubernetes y entregables

*Criterio de terminado: todo criterio de `alcance-mvp.md` §4 tiene evidencia, el stack arranca de cero con
un comando y los entregables del curso están listos.*

| ID | Tarea | Dueño | Entregable | Criterio de terminado |
|---|---|---|---|---|
| **T4.1** | Cluster con la **app real** desplegada + observabilidad apuntando al cluster; push al repo público y CI verde | @devops | k8s en minikube + Actions | `kubectl get pods -n gs08` 3/3, ingress respondiendo, CI verde en `main` con las dos imágenes construidas |
| **T4.2** | Prueba de regresión final sobre compose **y** sobre k8s, con la tabla de criterios cubiertos | @qa | `docs/qa/reporte-cierre.md` | **100 % de los 39 criterios `C-01`…`C-39`** de `alcance-mvp.md` §4 con estado y evidencia (ese es el único denominador, decisión D-18); ningún criterio marcado «ok» sin salida real |
| **T4.3** | Informe final, PPT de sustentación, guion de demo y acta de Sprint 0 | @documentador | DOCX/PDF/PPTX | el PPT sigue el guion §3 paso a paso; el informe tiene todas las tablas con datos reales |
| **T4.4** | Ensayo de la demo con el entorno limpio (`down -v` + `up`) y guion de comandos | @dev + @devops | `docs/devops/COMANDOS.md` | en un entorno recién borrado, todo el recorrido funciona sin pasos manuales ocultos |
| **T4.5** | Revisión final: decisiones cerradas, criterios con evidencia y entregables en `OneDrive\RAR\ISAM\<periodo>` | @pm | `docs/decisiones.md` actualizado | ninguna decisión abierta salvo las que dependan del dueño; entrega al usuario con las rutas |

---

## Correcciones de Sprint 0 (salidas de los 6 bugs de @qa)

*Son de cierre: se hacen antes de arrancar en serio el Sprint 1, porque dos de ellas afectan lo que se
documenta y lo que se mide.*

| ID | Tarea | Dueño | Entregable | Criterio de terminado |
|---|---|---|---|---|
| **TC-01** | **BUG-01**: `verificar_stack.py` no es determinista en un entorno recién levantado (la serie `status=~"5.."` no existe y Prometheus devuelve vacío, no 0) | @devops | script corregido | con `down -v` + `up` y sin ningún 500: **ADVERTENCIA** por serie ausente y **exit 0**; repetido **2 veces seguidas** en entorno limpio, ambas exit 0. Propuesta de @qa aceptada: serie ausente = advertencia, no falla |
| **TC-02** | **BUG-06**: `/api/` pierde los 3 headers de seguridad del `server` (nginx no hereda `add_header` si la location declara el suyo) | @devops | `frontend/nginx/default.conf.template` | `curl -I http://localhost:8080/api/v1/health` devuelve **las 4**: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` y `X-Upstream-Addr` |
| **TC-03** | **BUG-05**: `/health` y `/metrics` por el proxy devuelven 200 con el `index.html` del SPA | @devops | nginx | `curl -o /dev/null -w '%{http_code}' http://localhost:8080/metrics` → **404** (igual `/health`); `/api/v1/health` → **200**; `/metrics` directo en `:8000` sigue dando texto Prometheus. Detalle en **D-17** |
| **TC-04** | Actualizar la matriz de pruebas a los **39 criterios con ID** (`C-01`…`C-39`), corregir el DNI del caso de búsqueda a `45123456` y marcar BUG-02/03/04 como cerrados citando la revisión 2 del alcance | @qa | `docs/qa/plan-pruebas.md` rev. 2 | cada fila declara su `C-xx`; **39/39 criterios mapeados** (si un criterio lleva dos casos, los dos citan el mismo `C-xx`); el reporte de bugs tiene los 6 con su estado final |
| **TC-05** | Alcance corregido y con denominador único | @pm | `docs/alcance-mvp.md` rev. 2 | ✅ hecho: 39 criterios numerados, `admin@horizonte.edu.pe`, DNI `45123456`, salud/métricas reescrito |

---

## Documentación de entrega (transversal a S1–S4) — dueño: @documentador

**Regla de la casa para estos documentos** (pedido del dueño, 21/09/2026): cada documento lleva **índice y
fecha**, **cita el archivo o el comando del que sale cada afirmación**, y **no documenta funcionalidad que
todavía no existe**: lo que está bloqueado se escribe como *«pendiente — bloqueado por T<xx>»*, nunca como
hecho. Todo se redacta sobre la evidencia ya en el repo (`docs/devops/evidencia-sprint0.md`,
`docs/analisis/modelo-datos.md` y `datos-seed.md`, `docs/qa/plan-pruebas.md` y `reporte-bugs.md`,
14 salidas reales en `docs/qa/evidencia/` y 7 en `docs/analisis/evidencia/`).

| ID | Documento | Cuándo | Criterio de terminado |
|---|---|---|---|
| **TD-01** | `README.md` (raíz del repo) | **ahora** | qué es el proyecto, stack con versiones reales, mapa de carpetas, arranque en 5 min (`docs/devops/COMANDOS.md`), estado real por sprint y enlaces a todos los docs. **Probado por @qa en entorno limpio**: siguiendo solo el README, el stack queda arriba y `verificar_stack.py` da exit 0 |
| **TD-02** | `docs/arquitectura.md` **con diagramas** | **ahora** | diagramas Mermaid que renderizan: (a) componentes SPA/nginx → 2×API → PostgreSQL, (b) flujo de una petición con balanceo y failover, (c) modelo de datos ER con las 5 tablas/vista de `modelo-datos.md`, (d) despliegue k8s (11 objetos de `k8s/kustomization.yaml`), (e) observabilidad Prometheus/Grafana. Fuentes: `docs/devops/evidencia-sprint0.md` §1-2 y §5 + `modelo-datos.md` §1 |
| **TD-03** | `docs/manual-usuario.md` | **después de T2.4** (necesita el SPA) | pantalla por pantalla siguiendo el recorrido de `alcance-mvp.md` §3, con capturas propias (no del legacy) y el mensaje de error que muestra cada `4xx`. Cada paso verificado por @qa en el entorno real; lo que aún no exista (hoy el login, T1.1) va como *pendiente bloqueado* |
| **TD-04** | `docs/manual-tecnico.md` | **ahora** (crece con S1–S3) | contrato de la API (endpoint, códigos, ejemplo real de request/response), versiones del stack con la fuente, contenedores y red, CI/CD, k8s (**manifiestos listos, cluster no desplegado en esta máquina** mientras @user no decida minikube), y problemas conocidos: `minikube image load` con imágenes locales, quirk `$2y$` de pgcrypto (D-12), `LIKE`→`ILIKE` (D-11), ids con huecos (D-13). Cada comando pegado con su salida real |
| **TD-05** | `docs/actas/acta-sprint-0.md` | **ahora** | asistentes y fecha, entregables con su evidencia (tabla de Sprint 0 de este backlog), decisiones D-00…D-22, riesgos abiertos, bloqueos (Kubernetes, push, fecha de entrega A-01) y acuerdos. Cada entregable cita archivo/commit |
| **TD-06** | `docs/actas/retrospectiva-sprint-0.md` | **ahora** | qué salió bien / qué no / acciones con dueño: las 3 correcciones de @devops (round-robin con `zone`, `max_fails` + `proxy_next_upstream`, el gauge que no existe en el instrumentator 8.1.0), los hallazgos de @analista (LIKE vs ILIKE, `$2y$`, ids con huecos), los 6 bugs de @qa (incluidos los 4 de su propio script) y las 5 correcciones del PM (BUG-02/03/04 y mi conteo: dije 35, el real es **39**). Cada hallazgo con su evidencia y su acción cerrada o asignada a T<xx> |
| **TD-07** | `docs/decisiones.md` | **ahora** (mantenido por @pm) | tabla con fecha, motivo y estado; stack (D-00), minikube driver docker (D-04), rama `main` (D-05) y las abiertas (A-01/A-02). **@documentador lo cita tal cual, no lo reescribe ni lo duplica en `docs/`** |
| **TD-08** | `docs/seguridad-etica-sostenibilidad.md` | **ahora** (crece con S2–S3) | **Seguridad:** bcrypt coste 10 y hash `$2y$` del seed, tokens/roles y `403` por rol, 4 headers de nginx (TC-02), ningún secreto en git (`k8s/02-secret.example.yaml`), SBOM/provenance de GHCR, superficie expuesta (4000/8080/3000/9090 solo en local). **Ética:** DNI y datos del estudiante = dato personal (Ley 29733), minimización (no se guarda nada de salud ni de menores), notas como dato sensible, notas del legacy como datos de prueba ficticios, IA usada declarada. **Sostenibilidad:** imágenes alpine, un contenedor por servicio, `k8s` en una laptop sin nube, costo 0, mantenibilidad (tests + verificación reproducible). Lo legal se escribe como **mapa a verificar con asesoría**, no como dictamen |
| **TD-09** | **DOCX + PPTX de entrega académica** | antes de la exposición | **Español, firma grupal, 3 integrantes en la carátula y docente Dr. Jack Peralta (D-23).** @documentador arma el **borrador** de los dos a partir de los documentos de arriba, con las mismas tablas y salidas reales; el **PPTX son 10 láminas exactas, una idea por lámina**, con el reparto de la sección «Entregable académico» y el recorrido de `docs/alcance-mvp.md` §3 en la lámina de demo. **La versión académica final —portada, formato, normas de la facultad y firma— la cierra el dueño** (@user). Ningún dato que no esté ya en los documentos con su evidencia |
| **TD-10** | Actualizar `docs/actas/acta-sprint-0.md` y `retrospectiva-sprint-0.md` (ya escritas) con los **datos del grupo y del docente** (D-23) y con el reparto por integrante | **ahora** | el acta lista a los 3 integrantes con su rol y acredita la asistencia al Sprint 0; la retrospectiva mantiene sus hallazgos y agrega el reparto por bloques. Ninguna cifra cambia |

**Bloqueos declarados de esta tanda:** TD-03 espera T2.4 (SPA), TD-09 espera TD-01…TD-08 y la fecha de
exposición (A-01), y el despliegue de k8s de TD-04/TD-02 espera la decisión del dueño sobre instalar
minikube (A-02).

---

## Entregable académico — grupo, reparto y 10 láminas

**Datos del entregable (decisión D-23, dados por el dueño el 21/09/2026):** grupo de **3 integrantes**,
informe y exposición **en español**, **con firma grupal**, **10 láminas concisas con una idea por lámina**,
docente **Dr. Jack Peralta**. **Cada integrante documenta y expone su bloque.**

| Integrante (persona real) | Rol académico | Rol en la sala | Documenta | Expone |
|---|---|---|---|---|
| **Arteaga Rullier, Roberto** | Scrum Master + DevOps | @pm + @devops | alcance, backlog, decisiones, contenedores, CI, Kubernetes, observabilidad | láminas 1, 3, 7, 8, 10 |
| **Díaz Cárdenas, Jorge Luis** | Backend | @dev | modelo de datos, reglas de negocio, API, pruebas de API | láminas 4, 5, 9 |
| **Inocencio Gargate, Dalcir** | Frontend + Documentador | @dev (SPA) + @documentador | SPA/UX, manual de usuario, actas, informe y PPTX | láminas 2, 6 |

### Las 10 láminas (una idea por lámina, en español)

| # | Idea única | Se apoya en | Expone |
|---|---|---|---|
| 1 | Carátula: proyecto, curso, docente, los 3 integrantes y firma grupal | `docs/actas/acta-sprint-0.md` | Roberto |
| 2 | El problema y el alcance del MVP: qué entra y qué NO entra | `docs/alcance-mvp.md` §1 y §5 | Dalcir |
| 3 | Arquitectura y stack: FastAPI + PostgreSQL 16 + Vue 3 + Tailwind, Docker, k8s, Prometheus/Grafana | `docs/arquitectura.md` | Roberto |
| 4 | Modelo de datos y reglas: 4 tablas + 16 CHECK / 6 UNIQUE / 2 FK + notas, 49 comprobaciones | `docs/analisis/modelo-datos.md` | Jorge |
| 5 | API: contrato y comportamiento (`200/201/204/401/403/404/409/422/500`) | `docs/manual-tecnico.md` | Jorge |
| 6 | La SPA: el recorrido del usuario en pantalla, de la matrícula a la nota | `docs/manual-usuario.md` + `alcance-mvp.md` §3 | Dalcir |
| 7 | Contenedores y CI: 6 contenedores, balanceo y failover, GitHub Actions | `docs/devops/plan-contenedores-ci.md` | Roberto |
| 8 | Kubernetes local y observabilidad: 11 objetos, Prometheus, Grafana | `docs/devops/evidencia-sprint0.md` | Roberto |
| 9 | Calidad: los 39 criterios `C-01`…`C-39` y los 6 bugs que aparecieron probando | `docs/qa/plan-pruebas.md`, `reporte-bugs.md` | Jorge |
| 10 | Sprint 0 → Sprint 4: lo entregado, lo bloqueado y la retrospectiva | `docs/actas/retrospectiva-sprint-0.md` | Roberto |

**Cómo se verifica el PPTX (criterio de terminado de TD-09):** ① exactamente **10 láminas**; ② **una idea
por lámina** (sin viñetas apiladas); ③ en **español**; ④ la carátula lleva los **3 nombres, el curso y al
docente Dr. Jack Peralta**; ⑤ **firma grupal** en el informe; ⑥ cada lámina cita el documento o la salida
real de la que sale; ⑦ la lámina 8 muestra **el estado real** de Kubernetes: si el dueño no aprueba
instalar minikube (A-02), va con los manifiestos validados y la etiqueta *«no desplegado en esta máquina»*,
nunca como si estuviera corriendo.

---

## Orden de corte si el tiempo aprieta

1. Se corta **T3.x (notas y boleta)** → la app queda como «sistema preparado para notas» (§5, ítem 8 y
   `modelo-datos.md` §7) y se dice en la sustentación, no se esconde.
2. Después se corta **T4.2** (regresión sobre k8s) → solo compose.
3. **No se corta**: T1.6/T4.1 (Kubernetes es requisito del curso), la observabilidad ni la tabla de
   criterios con evidencia.
