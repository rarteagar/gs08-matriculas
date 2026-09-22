# GS08 · Matrículas y Notas — Retrospectiva del Sprint 0

**Entregable:** TD-06 de `docs/backlog-sprints.md` · **Redacta:** @documentador · **Fecha:** 21/09/2026
**Sprint:** 0 (alcance + infraestructura + modelo de datos + plan de pruebas) · **Rama:** `main` @ `e051d43`

**Cómo se lee esta retrospectiva:** cada hallazgo cita **de dónde sale** (archivo, comando o mensaje de la
sala) y termina en **una acción con dueño**: o ya está cerrada dentro del Sprint 0, o queda asignada a una
tarea con nombre (`T<xx>`/`TC-<xx>`). Los hallazgos salieron **probando**, no leyendo: esa es la conclusión
principal del sprint.

## Índice

1. [Qué salió bien](#1-qué-salió-bien)
2. [Qué no salió bien](#2-qué-no-salió-bien)
3. [Hallazgos y correcciones: evidencia → acción](#3-hallazgos-y-correcciones-evidencia--acción)
4. [Acciones con dueño, al cierre](#4-acciones-con-dueño-al-cierre)
5. [Lecciones que se llevan al Sprint 1](#5-lecciones-que-se-llevan-al-sprint-1)

---

## 1. Qué salió bien

| Qué | Por qué se considera un acierto | Evidencia |
|---|---|---|
| **El stack completo se levantó y quedó sano antes de que exista el código** | Se probó la infraestructura con un stub (arnés `D:\dev\_tmp\gs08-smoke`) y así se descubrieron 6 defectos de infra que, con el código ya encima, habrían costado el doble | `docs/devops/evidencia-sprint0.md` §2, §8 · `python scripts/verificar_stack.py` → **9 OK, 0 fallas** |
| **El esquema del legacy se tradujo y se verificó corriendo** | 49 comprobaciones automáticas, con **15 pruebas negativas** que exigen que la base rechace cada regla violada: las reglas viven en la base, no en la buena voluntad del código | `bash db/verificacion/ejecutar_verificacion.sh` → **49 OK, exit 0** · `docs/analisis/modelo-datos.md` §5 |
| **Verificación cruzada entre dos dueños distintos** | @devops corrió la imagen del API contra el esquema de @analista, sin tocar datos: 4 tablas + 1 vista visibles y las 4 reglas **rechazadas por la base** | `docs/devops/evidencia-sprint0.md` §7 |
| **El arnés de pruebas se validó contra una API falsa con defectos plantados** | Una prueba que nunca falla no prueba nada: el smoke detectó **exactamente** los 2 defectos escondidos (KPI 22 en vez de 23 y DNI de 7 dígitos aceptado con 201) | `docs/qa/plan-pruebas.md` §8 |
| **Las pruebas se corrieron de forma independiente** | @qa **re-corríó** el modelo de datos de @analista y **verificó el failover él mismo** (apagó `gs08-api-b` y las 6 peticiones siguieron dando 200), en vez de copiar el reporte ajeno | `docs/qa/plan-pruebas.md` §8 · `docs/qa/reporte-bugs.md` §«Lo que verifiqué y sí está bien» |
| **Datos oficiales del seed separados en un archivo propio** | Cortó de raíz la discusión «¿el dato o el criterio?»: si un criterio cita otro correo, otro DNI u otro conteo, **el criterio está mal** | `docs/analisis/datos-seed.md` (D-21) |
| **Los criterios quedaron con ID único** | Sin denominador único no se puede afirmar «100 % de cobertura» | `docs/alcance-mvp.md` §4, rev. 2 (D-18) |

---

## 2. Qué no salió bien

Dicho sin adornos, con quién y con qué se corrige:

| Qué falló | Consecuencia real (no teórica) | Corrección |
|---|---|---|
| **Se escribió un criterio de aceptación contra datos que no existen** (`admin@institucion.edu.pe`, DNI `12345678`) | Un test escrito literalmente contra el criterio habría dado 401 y 0 filas, y el criterio parecería roto **por el dato, no por el código** | BUG-02/BUG-03, cerrados con D-21: manda el seed, se corrige el alcance. Fuente única: `datos-seed.md` |
| **El conteo de criterios estaba mal (35 vs 39)** | Con dos denominadores, «100 % de cobertura» (T4.2) es inverificable, y los 4 criterios de diferencia se cuelan sin dueño | BUG-04, cerrado con D-18: 39 criterios con ID |
| **La causa del conteo mal:** un `grep` que no veía los criterios escritos en línea (`Listado paginado: ✅ …`) | Un número que se reporta sin contarlo con un método confiable | `docs/qa/plan-pruebas.md` §3 cuenta los 39 uno por uno; ese es el número cruzado |
| **El verificador de infraestructura no era determinista** | En un entorno recién levantado (`down -v` + `up`) salía **exit 1 sin ningún error real**: el jurado habría visto un rojo que no era del sistema | BUG-01 → D-19 (serie ausente = ADVERTENCIA) → **TC-01** (@devops), verifica @qa |
| **Un criterio de salud/métricas se podía cumplir sin cumplirse** | `/metrics` por el proxy devolvía **200 con el `index.html`**: un chequeo de código de estado daba por bueno un endpoint sin métricas | BUG-05 → D-17 → **TC-03** (@devops), verifica @qa |
| **Las cabeceras de seguridad no llegaban a `/api/`** | Se declararon en el bloque `server` y no se heredaban: el endurecimiento existía en el papel, no en las respuestas del API | BUG-06 → **TC-02** (@devops), verifica @qa |
| **Faltaba la extensión `unaccent` y nadie lo había notado hasta probar el criterio** | `?q=huaman` y `?q=HUAMAN` devuelven **0** e `?q=Huamán` **1**: el criterio `C-08` («la misma cantidad en las tres») **no se puede cumplir hoy** | BUG-07 (nuevo, Alto) → asignado a **@dev** (buscador) + **@analista** (DDL en `db/init/` **y** en Alembic, D-14) |
| **El propio arnés de pruebas tenía 4 bugs** | Contaba filas sobre el cuerpo recortado a 500 caracteres, leía el código HTTP después de una segunda petición, mostraba el cuerpo anterior cuando `curl` fallaba, y comparaba `16.00` contra un JSON que devuelve `16.0` | Los 4 corregidos por @qa dentro del sprint (`plan-pruebas.md` §8) |
| **El round-robin de nginx estaba «funcionando» mal** | Todas las peticiones caían en una instancia: el balanceo era decorativo | Corregido con `zone gs08_api 64k;` → reparto 1 a 1 |
| **No había reintento si una instancia estaba caída al arrancar** | nginx penalizaba a `api-b` y todo el tráfico quedaba en `api`, sin tolerancia a fallos | Corregido con `max_fails=3 fail_timeout=10s` + `proxy_next_upstream error timeout` |
| **Se documentó un panel de Grafana con una métrica que no existe** | `http_requests_inprogress` **no** está en `prometheus-fastapi-instrumentator` 8.1.0: el panel salía vacío | Corregido: panel 4 reemplazado por «Errores 4xx (%)»; el hallazgo queda anotado en la retrospectiva |
| **El job de Prometheus hacia nginx estaba en `down`** | Prometheus marcaba un target caído que nunca iba a levantarse (`ok\n` no es formato Prometheus) | Job eliminado + nota en `prometheus.yml`: nginx necesita su exporter |
| **Kubernetes quedó sin evidencia de despliegue** | El criterio `C-37` está bloqueado y la sección de k8s de los documentos dice «manifiestos listos, cluster no desplegado»: es un hueco **declarado**, no escondido | A-02 (@user autoriza instalar minikube) → **T1.6/T4.1** (@devops) |
| **El CI nunca corrió en GitHub** | Los workflows están escritos y validados offline, pero sin remoto no hay corrida real: `C-39` bloqueado | Push final → **T4.1** (@devops) |

---

## 3. Hallazgos y correcciones: evidencia → acción

### 3.1 Infraestructura y observabilidad (@devops) — 6 correcciones hechas dentro del sprint

Fuente: `docs/devops/evidencia-sprint0.md` §8 y `docs/devops/plan-contenedores-ci.md` §7.

| Hallazgo | Evidencia que lo destapó | Corrección | Estado |
|---|---|---|---|
| Round-robin desparejo (todo a una instancia) | 6 peticiones seguidas con la misma `X-Upstream-Addr` | `zone gs08_api 64k;` en el `upstream` | ✅ cerrado (reparto 12/12) |
| Sin reintento al caer una instancia | `X-Upstream-Addr: .6, .5` con código **200** | `max_fails=3 fail_timeout=10s` + `proxy_next_upstream error timeout` | ✅ cerrado |
| `http_requests_inprogress` no existe en el instrumentator 8.1.0 | `dir(metrics)` en el contenedor: `['combined_size','default','latency','request_size','response_size','requests',…]` | Panel 4 reemplazado por «Errores 4xx (%)» | ✅ cerrado |
| Job de Prometheus hacia nginx en `down` | `lastError: expected value after metric, got "\n" ("INVALID")` | Job eliminado + nota: nginx necesita su exporter | ✅ cerrado (exporter = Sprint 1) |
| `frontend/Dockerfile` dejaba nginx corriendo como root | `scripts/validar_infra.py` lo marcaba como FALLA | `USER nginx` + escucha en 8080 + directorios escribibles | ✅ cerrado y **verificado por el validador** |
| `kubectl apply --dry-run=client` no valida sin cluster | `failed to download openapi` | La validación offline es `kubectl kustomize k8s/` (11 objetos) | ✅ cerrado (documentado en README y manual técnico) |
| `verificar_stack.py` no determinista (BUG-01 de @qa) | Reproducción en 4 partes: `docs/qa/evidencia/verificar-stack-no-determinista.txt` | Decisión D-19: serie ausente = ADVERTENCIA | ⬜ **TC-01** (@devops); verifica @qa |
| Cabeceras de seguridad fuera de `/api/` (BUG-06) | `curl -D -` a `/healthz` vs `/api/v1/health` | Repetir los `add_header` en la `location /api/` | ⬜ **TC-02** (@devops); verifica @qa |
| `/health` y `/metrics` por el proxy devolvían el SPA (BUG-05) | `curl -o /dev/null -w '%{http_code} %{content_type}'` → `200 text/html 371 bytes` | nginx **404** en esas rutas; `/metrics` directo en `:8000` (D-17) | ⬜ **TC-03** (@devops); verifica @qa |

### 3.2 Modelo de datos y reglas de negocio (@analista) — 2 hallazgos medidos + 1 quirk

Fuente: `docs/analisis/modelo-datos.md` §6 y §7, con las salidas reales en `docs/analisis/evidencia/`.

| Hallazgo | Medición (salida real) | Decisión / acción | Estado |
|---|---|---|---|
| **El buscador del legacy no se puede copiar literal:** `LIKE '%quispe%'` → **0 filas** e `ILIKE` → **2** sobre los mismos datos. Con `ILIKE` sin `unaccent`, `q=huaman` → **0** porque el dato es `Huamán` | `docs/analisis/evidencia/busqueda-rendimiento.txt` (100.000 filas: `Seq Scan` 112 ms con `ILIKE` vs `Bitmap Index Scan` 0,09 ms con índice trigram) | **D-11** (`ILIKE`, `unaccent` si se quieren tildes). Con BUG-07 encima, `unaccent` pasó de «si se quieren tildes» a **exigido** por `C-08` | ✅ decidido · ⬜ DDL pendiente (@analista, T1.5) |
| **El hash bcrypt del seed funciona pero no se valida con pgcrypto:** `$2y$` calcula un digest distinto; solo coincide normalizando a `$2a$` | `bcrypt==4.2.1` (PyPI) → `checkpw(b'Admin123!', hash) → True`; `docs/analisis/evidencia/diagnostico-hash-legacy.txt` y `hash-legacy-python-bcrypt.txt` | **D-12**: el hash se deja tal cual; la API lo verifica con `bcrypt` y nadie lo «arregla» | ✅ cerrado |
| **Los `id` no son consecutivos y está bien:** `nextval` no se revierte con `ROLLBACK` y un INSERT rechazado consume el id (tras 3 fallos, el siguiente curso válido fue 11) | Medición en `verificar_modelo.sql` (comprobaciones 4 dentro de transacción + 3 después del `ROLLBACK`) | **D-13**: no se tocan las secuencias; el seed cierra con `setval` | ✅ cerrado |
| Las notas **no** estaban en el esquema aunque el proyecto se llama «Matrículas **y Notas**» | El legacy no tiene tabla de notas (`legacy/script.sql.txt`) | @analista dejó el DDL propuesto **sin aplicarlo** hasta que @pm fijara el alcance → **D-01**: entran, aditivas, Sprint 3 | ✅ decidido (T1.5/T3.1) |

### 3.3 Pruebas (@qa) — 7 bugs + 4 bugs propios

Fuente: `docs/qa/reporte-bugs.md` y `docs/qa/plan-pruebas.md` §8.

| Bug | Gravedad | Evidencia | Acción / dueño | Estado |
|---|---|---|---|---|
| BUG-01 · `verificar_stack.py` falla en entorno limpio | Alta | `docs/qa/evidencia/verificar-stack-no-determinista.txt` (4 partes; hipótesis «5 minutos sin 5xx» **descartada** probándola) | **D-19** → TC-01 (@devops) | Aceptado, en arreglo |
| BUG-02 · criterio cita `admin@institucion.edu.pe` | Media | `select nombre_usuario,email from usuarios;` → `admin@horizonte.edu.pe`; `legacy/script.sql.txt` línea 122 | **D-21** → alcance rev. 2 (`C-01`) | ✅ cerrado |
| BUG-03 · criterio cita DNI `12345678` | Media | Los DNI del seed son `45123456`, `46234567`, … | **D-21** → alcance rev. 2 (`C-09`), smoke `SM-16` | ✅ cerrado |
| BUG-04 · 35 vs 39 criterios | Media | Conteo por bloque: 4+3+5+3+6+2+6+3+7 = **39** | **D-18** → alcance rev. 2 con ID | ✅ cerrado |
| BUG-05 · `/metrics` por el proxy devolvía el `index.html` con 200 | Alta | `curl … -w '%{http_code} %{content_type} %{size_download}'` → `200 text/html 371` | **D-17** → TC-03 (@devops) | Aceptado, en arreglo |
| BUG-06 · cabeceras de seguridad ausentes en `/api/` | Baja | Dos `curl -D -` comparados | → TC-02 (@devops) | Aceptado, en arreglo |
| BUG-07 · sin `unaccent` el criterio `C-08` no se puede cumplir | Alta | Medido contra la base: `huaman` → 0, `Huamán` → 1, `HUAMAN` → 0; con la extensión instalada, 1/1/1 (la instaló, midió y la **desinstaló** para dejar la base como estaba) | **@dev** (`unaccent(apellidos) ILIKE unaccent(%q%)`) + **@analista** (`CREATE EXTENSION` en `db/init/` **y** en la migración inicial de Alembic, D-14) | ⬜ nuevo, sin arreglo asignado a fecha |
| **4 bugs del propio script** (`smoke_api.sh`): contaba sobre el cuerpo recortado, leía el código HTTP tras una segunda petición, mostraba el cuerpo anterior cuando `curl` fallaba, comparaba `16.00` contra `16.0` | — | Aparecieron validando el arnés contra una API falsa con 2 defectos plantados | Corregidos por @qa dentro del sprint | ✅ cerrado |

**Nota de precisión que dejó la retrospectiva** (vale para todos los documentos): la cifra «`q=huaman` → **2
filas**» de `docs/analisis/datos-seed.md` es de **`/matriculas?q=`** (el estudiante 2 tiene 2 matrículas); en
`/api/v1/estudiantes` el mismo `q` devuelve **1 fila**. Las dos cifras son correctas, pero citadas en el
endpoint equivocado no lo son.

### 3.4 Documentos y criterios (@pm) — 4 correcciones en la rev. 2 del alcance

| Corrección | Qué cambió | Cita |
|---|---|---|
| **Denominador único** | 39 criterios con ID `C-01`…`C-39`; «100 %» = esos 39 | D-18 · `alcance-mvp.md` §4 |
| **Correo real del seed** | `admin@institucion.edu.pe` → `admin@horizonte.edu.pe` | D-21 · `C-01` |
| **DNI real del seed** | `12345678` → `45123456` | D-21 · `C-09` |
| **Criterio de salud y métricas reescrito** | `/api/v1/health` por el proxy; `/metrics` directo en `:8000`; nginx **404** en `/health` y `/metrics` | D-17 · `C-34` |
| *(y la decisión que salió de un bug ajeno)* | Serie de Prometheus ausente = **ADVERTENCIA**, no falla | D-19 |
| **Criterios en arreglo, escritos como tales** | `C-33` y `C-34` figuran como *«FALLA→EN ARREGLO, TC-01 / TC-03»*, **no** como incumplidos ni como resueltos | `docs/qa/plan-pruebas.md` §3 |

**El error de conteo, explicado por el propio @pm:** su `grep` no veía los criterios escritos en línea
(ejemplo: `Listado paginado: ✅ …`), razón por la cual reportó 35. La corrección de fondo no es el número
sino el método: ahora cada criterio tiene un ID y el conteo se hace por ID, no por formato del texto.

---

## 4. Acciones con dueño, al cierre

| # | Acción | Dueño | Tarea | Criterio de terminado |
|---|---|---|---|---|
| 1 | `verificar_stack.py` determinista: serie ausente = ADVERTENCIA | @devops | **TC-01** | `down -v` + `up`, **dos corridas exit 0** sin provocar 5xx; verifica @qa |
| 2 | Los 4 headers (incluido `X-Upstream-Addr`) también en `/api/` | @devops | **TC-02** | `curl -D - http://localhost:8080/api/v1/health` trae los 4; verifica @qa |
| 3 | nginx **404** en `/health` y `/metrics`; `/api/v1/health` **200** | @devops | **TC-03** | `curl -w '%{http_code}'` → 404, 404, 200; `/metrics` sigue en `:8000`; verifica @qa |
| 4 | `CREATE EXTENSION unaccent` en `db/init/` **y** en la migración inicial de Alembic | @analista + @dev | **BUG-07** / D-14 | `\dx unaccent` presente por las **dos** rutas (base nueva y `alembic upgrade head`) |
| 5 | Matriz de pruebas a los 39 `C-xx` | @qa | **TC-04** | ✅ hecho en esta ronda (`plan-pruebas.md` rev. 2) |
| 6 | 39 criterios con ID y datos del seed | @pm | **TC-05** | ✅ hecho (`alcance-mvp.md` rev. 2) |
| 7 | API núcleo (`/auth/login`, estudiantes, cursos, dashboard) + Alembic | @dev | **T1.1-T1.4** | `/api/v1/health` 200, `pytest` verde, `alembic upgrade head` sin diferencias contra `db/init/` |
| 8 | `db/init/04-notas.sql` + `v_notas_detalle` + RN-14/RN-15 | @analista | **T1.5** | verificación con **exit 0** y 3 pruebas negativas nuevas |
| 9 | Documentación de entrega (README, arquitectura, manual técnico, actas, seguridad) | @documentador | **TD-01…TD-08** | ✅ los de esta tanda, citando comando/archivo; `manual-usuario.md` espera T2.4 |
| 10 | Instalar minikube (driver docker) — **requiere autorización** | @user → @devops | **A-02 / T1.6** | `kubectl get pods -n gs08` → **3/3 Running** y `kubectl get job gs08-migraciones` → **Complete** |
| 11 | Fechar los 4 sprints | @user | **A-01** | fecha de entrega y de exposición; con eso el calendario y el orden de corte |

---

## 5. Lecciones que se llevan al Sprint 1

1. **Probar la infraestructura sin el código funcionó y se repite.** Los 6 defectos de contenedores,
   balanceo y observabilidad aparecieron antes de que exista una línea de `app/`, cuando arreglarlos costaba
   minutos. Mientras @dev implementa, @devops siguiere verificando con el mismo arnés.
2. **Toda cifra de un documento se saca de la base o del comando, no del documento anterior.** Los tres
   bugs de datos (`BUG-02`, `BUG-03`, `BUG-04`) fueron exactamente eso: un criterio que citaba algo que
   nunca se comprobó contra el seed.
3. **Un verificador que falla en el camino limpio es peor que no tener verificador.** BUG-01 sale a la luz
   justo porque @qa reprodujo la ruta de la demo (`down -v` + `up`) y no la ruta cómoda.
4. **Un «200 OK» no es una prueba de nada.** El legacy ya lo enseñaba con el `LIKE` (buscador mudo sin
   error) y el `/metrics` del proxy repitió la lección: hay que mirar el **contenido** y el **tipo**, no solo
   el código de estado.
5. **El arnés de pruebas se valida con defectos plantados.** Los 4 bugs del propio smoke se encontraron así;
   sin la API falsa habrían llegado al Sprint 1 como falsos verdes.
6. **Lo bloqueado se escribe como bloqueado.** `C-33`/`C-34` figuran como *en arreglo* y `C-37` como
   *bloqueado por A-02*: un criterio «ok» sin salida real no se marca nunca, y así la tabla de cobertura
   dice la verdad aunque duela.

---

**Archivos de los que sale esta retrospectiva:** `docs/devops/evidencia-sprint0.md` §8,
`docs/devops/plan-contenedores-ci.md` §7, `docs/analisis/modelo-datos.md` §5-§7,
`docs/analisis/evidencia/*`, `docs/qa/plan-pruebas.md` §8 y §11, `docs/qa/reporte-bugs.md`,
`docs/qa/evidencia/verificar-stack-no-determinista.txt`, `docs/decisiones.md` (D-11, D-12, D-13, D-17 a D-21),
`docs/alcance-mvp.md` rev. 2 y `docs/backlog-sprints.md`.
