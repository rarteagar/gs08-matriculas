# GS08 · Matrículas y Notas — Acta de cierre del Sprint 0

**Entregable:** TD-05 de `docs/backlog-sprints.md` · **Redacta:** @documentador · **Fecha del acta:** 21/09/2026
**Reunión:** sala «Developer Team» · **Sprint:** 0 · **Rama:** `main` @ `e051d43`

**Propósito de esta acta:** dejar constancia de qué se entregó en el Sprint 0, con qué evidencia, qué se
decidió y qué queda bloqueado. Nada de lo que figura como entregado está «por decir»: cada fila cita el
archivo o el commit, y las salidas reales viven en los archivos de evidencia de cada dueño.

## Índice

1. [Asistentes y orden del día](#1-asistentes-y-orden-del-día)
2. [Entregables del Sprint 0, con su evidencia](#2-entregables-del-sprint-0-con-su-evidencia)
3. [Decisiones tomadas (D-00…D-22)](#3-decisiones-tomadas-d-00d-22)
4. [Correcciones que salieron de las pruebas](#4-correcciones-que-salieron-de-las-pruebas)
5. [Bloqueos declarados y riesgos abiertos](#5-bloqueos-declarados-y-riesgos-abiertos)
6. [Acuerdos de la sesión](#6-acuerdos-de-la-sesión)
7. [Anexo: cómo reproducir la verificación del Sprint 0](#7-anexo-cómo-reproducir-la-verificación-del-sprint-0)

---

## 1. Asistentes y orden del día

**Fecha:** 21/09/2026 · **Lugar:** sala de grupo «Developer Team» (Hermes) · **Duración:** sesión de trabajo continua.

| Rol | Quién | Aporta en el Sprint 0 |
|---|---|---|
| Alcance, reparto y decisiones | **@pm** | `alcance-mvp.md` rev. 2, `backlog-sprints.md`, `decisiones.md` |
| Modelo de datos y reglas de negocio | **@analista** | `db/init/*.sql`, `db/verificacion/`, `modelo-datos.md`, `datos-seed.md` |
| Contenedores, CI/CD, Kubernetes, observabilidad | **@devops** | `docker-compose.yml`, `.github/workflows/`, `k8s/`, `infra/`, `scripts/`, `plan-contenedores-ci.md`, `COMANDOS.md`, `evidencia-sprint0.md` |
| Pruebas y reporte de bugs | **@qa** | `scripts/smoke_api.sh`, `plan-pruebas.md`, `reporte-bugs.md`, `docs/qa/evidencia/` |
| Documentación de entrega | **@documentador** | este acta, `retrospectiva-sprint-0.md`, `README.md`, `docs/arquitectura.md`, `docs/manual-tecnico.md`, `docs/seguridad-etica-sostenibilidad.md` |
| Implementación del API y el SPA | **@dev** | nada todavía: sus tareas (T1.1, T1.2…) son del Sprint 1 |
| Dueño del proyecto | **@user** | cierre de alcance, aprobación de software nuevo, fecha de entrega |

**Orden del día:** (1) cerrar el alcance y el reparto; (2) revisar la evidencia de cada entregable;
(3) resolver los hallazgos de las pruebas; (4) declarar bloqueos y riesgos; (5) cerrar con acuerdos.

---

## 2. Entregables del Sprint 0, con su evidencia

Fuente de la tabla: `docs/backlog-sprints.md` §«Sprint 0 — cerrado (21/09/2026)». Todos **✅**, con la
evidencia que se indica. Ninguna fila se marca por intención.

| # | Entregable | Dueño | Evidencia concreta |
|---|---|---|---|
| 1 | Alcance del MVP, «no se hace», criterios de aceptación | @pm | `docs/alcance-mvp.md` — **39 criterios `C-01`…`C-39`**, rev. 2 |
| 2 | Backlog por sprints y reparto | @pm | `docs/backlog-sprints.md` |
| 3 | Modelo de datos + migraciones traducidas de `legacy/` | @analista | `db/init/01-schema.sql`, `02-view.sql`, `03-seed.sql` + `bash db/verificacion/ejecutar_verificacion.sh` → **49 OK, exit 0** |
| 4 | Plan de contenedores, CI y observabilidad | @devops | `docker-compose.yml`, `.github/workflows/`, `k8s/`, `infra/` + `python scripts/verificar_stack.py` → **9 OK, exit 0** |
| 5 | Repo con historial en `main` y `legacy/` importado | @devops | commits `9ef7c26` (import del legacy), `8d9b3bd` (infra), `c946d81` (.gitattributes), `e051d43` (evidencia) |
| 6 | Verificación cruzada esquema de @analista ↔ imagen del API | @devops | `docs/devops/evidencia-sprint0.md` §7: 4 tablas + 1 vista visibles; las 4 reglas **rechazadas por la base** (`uq_matriculas_estudiante_curso_periodo`, `ck_estudiantes_dni`, `ck_cursos_creditos`, `ck_matriculas_periodo`) |
| 7 | Plan de pruebas + smoke de API | @qa | `docs/qa/plan-pruebas.md`, `reporte-bugs.md`, `scripts/smoke_api.sh` (27 comprobaciones; infra **8 OK, exit 0**) |
| 8 | Datos oficiales del seed | @analista | `docs/analisis/datos-seed.md`: 12 / 7 / 24 (23 activas + 1 retirada), 12 códigos y DNI |
| 9 | Alcance corregido: 39 criterios con ID, correo y DNI reales | @pm | `docs/alcance-mvp.md` rev. 2 — cierra BUG-02/03/04/05 |
| 10 | Tabla de decisiones en `docs/decisiones.md`, 23 decisiones | @pm | `docs/decisiones.md` — D-00…D-22 + abiertas A-01/A-02 |
| 11 | Documentación de entrega (this batch) | @documentador | `README.md`, `docs/arquitectura.md`, `docs/manual-tecnico.md`, `docs/actas/`, `docs/seguridad-etica-sostenibilidad.md` |

**Salidas reales del Sprint 0** (los dos estándares que @pm fijó como referencia):

```
$ bash db/verificacion/ejecutar_verificacion.sh
verificar_modelo.sql      exit=0   comprobaciones OK=49   fallas=0
verificar_hash_admin.sql  exit=0   comprobaciones OK=2

$ python scripts/verificar_stack.py
9 comprobaciones OK, 0 fallas        (exit 0)

$ python scripts/validar_infra.py
21 comprobaciones OK, 0 fallas
```

---

## 3. Decisiones tomadas (D-00…D-22)

Registradas en **`docs/decisiones.md`** (ese archivo manda; acá va el índice para el acta). Todas cerradas
salvo lo que se indica:

| Decisión | En una línea |
|---|---|
| **D-00** | Stack: FastAPI + PostgreSQL 16 + Vue 3 (Vite) + Tailwind; reimplementar el legacy, no migrarlo |
| **D-01** | Las notas **sí** entran al MVP (Sprint 3), como esquema aditivo |
| **D-02** | Borrar con matrículas: `409` con el conteo; `204` solo con `?confirmar=true` |
| **D-03** | Nota del curso = media aritmética; promedio del periodo = ponderado por créditos |
| **D-04** | Kubernetes local con minikube y driver `docker` · **instalación pendiente de aprobación (A-02)** |
| **D-05** | La rama es `main`; se ajusta el workflow, no la rama |
| **D-06** | No se califica una matrícula `retirado` (RN-14); retirar no borra notas |
| **D-07** | Se pagina de a 25 (aunque el legacy mostraba todo) |
| **D-08** | Sin auditoría (`creado_por`, triggers) en la v1 |
| **D-09** | Usuarios: baja lógica como camino normal; nunca sobre la propia cuenta (`409`) |
| **D-10** | Sin portal de estudiante ni rol docente |
| **D-11** | Buscador con `ILIKE` (+ `unaccent` si se quieren tildes), nunca `LIKE` |
| **D-12** | El hash `$2y$` del seed se deja tal cual; nadie lo «arregla» por el quirk de pgcrypto |
| **D-13** | Los `id` con huecos son correctos: no se tocan las secuencias |
| **D-14** | Una sola fuente de verdad del esquema: la migración inicial de Alembic se genera desde `db/init/` |
| **D-15** | Entregables finales en `OneDrive\RAR\ISAM\<periodo>`; el código en `D:\dev\equipo\gs08-matriculas` |
| **D-16** | Sin Pinia ni librería de componentes: composables + Tailwind |
| **D-17** | Salud por `/api/v1/health`; `/metrics` directo en `:8000`; nginx `404` en `/health` y `/metrics` |
| **D-18** | El alcance tiene **39** criterios `C-01`…`C-39`: único denominador de T4.2 |
| **D-19** | `verificar_stack.py`: serie de Prometheus ausente = **ADVERTENCIA**, no falla |
| **D-20** | La documentación vive en `docs/` (raíz) y `docs/decisiones.md` se **cita**, no se reescribe |
| **D-21** | Ante discrepancia entre criterio y seed, **manda el seed** y se corrige el criterio |
| **D-22** | El DOCX y el PPTX de entrega académica los **cierra el dueño**; @documentador entrega el borrador |

---

## 4. Correcciones que salieron de las pruebas

Se trabajó con la regla de que **una prueba vale por su salida, no por su descripción**, y eso hizo aparecer
cosas en los tres frentes. El detalle completo, con la evidencia de cada uno, está en
`docs/actas/retrospectiva-sprint-0.md` §2-§4.

| Origen | Hallazgos | Resultado |
|---|---|---|
| Infraestructura (@devops) | Round-robin desparejo; sin reintento al caer una instancia; `http_requests_inprogress` no existe en el instrumentator 8.1.0; job de Prometheus hacia nginx en `down`; nginx corriendo como root; `--dry-run=client` no valida sin cluster | **6 corregidos** dentro del Sprint 0 (`docs/devops/evidencia-sprint0.md` §8) |
| Modelo de datos (@analista) | `LIKE` → 0 filas; el `$2y$` no se valida con pgcrypto; los `id` con huecos | **3 documentados como decisión** (D-11, D-12, D-13) |
| Pruebas (@qa) | **7 bugs**: `verificar_stack` no determinista (BUG-01), correo del criterio (BUG-02), DNI del criterio (BUG-03), 35 vs 39 (BUG-04), `/metrics` por el proxy (BUG-05), cabeceras en `/api/` (BUG-06), falta `unaccent` (BUG-07) | 3 cerrados por decisión, 3 asignados a TC-01/02/03, 1 nuevo (BUG-07) asignado a @dev + @analista |
| Pruebas del propio @qa | **4 bugs en `smoke_api.sh`**, encontrados al validarlo contra una API falsa con 2 defectos plantados | **4 corregidos** (`docs/qa/plan-pruebas.md` §8) |

---

## 5. Bloqueos declarados y riesgos abiertos

**Bloqueos (hechos, no temores):**

| Bloqueo | Comprobación | Dueño de destrabarlo |
|---|---|---|
| **Kubernetes real no existe** | `kubectl config current-context` → `error: current-context is not set`; `which minikube kind k3d k3s` → ninguno | **@user** (A-02: autorizar la instalación) · después @devops (T1.6/T4.1) |
| **El repo no tiene remoto**, así que CI/CD no ha corrido nunca en GitHub | Los workflows existen y validan offline (`python scripts/validar_infra.py`), pero no hay push | @devops (T4.1) |
| **La API real no existe** | `POST /api/v1/auth/login` → **404**; `docker compose build api` falla en `COPY requirements.txt` | @dev (T1.1, Sprint 1) |
| **El SPA no existe** | `frontend/` solo tiene `Dockerfile` y la config de nginx | @dev (T2.4, Sprint 2) |
| **Se desconoce la fecha de entrega y de exposición** | No hay dato | **@user** (A-01): sin ella los 4 sprints no se pueden fechar |

**Riesgos abiertos** (de `docs/alcance-mvp.md` §6, con lo que ya cambió en el Sprint 0):

| Riesgo | Estado real al cierre |
|---|---|
| No hay cluster local y el entregable lo exige | **Alta y es un hecho.** Manifiestos validados con `kustomize` (11 objetos), cluster pendiente de A-02. Plan B: `kind` |
| Repo público y credenciales llegan al final | Sin cambios: el repo local ya está en `main` y los workflows disparan con `push`/`pull_request`/`workflow_dispatch` |
| Dos fuentes de verdad del esquema | **Mitigado por decisión** (D-14): Alembic se genera desde `db/init/`. Se verifica en Sprint 1 |
| `ILIKE`/`unaccent` olvidados y el buscador mudo | **Materializado en BUG-07**: sin `CREATE EXTENSION unaccent` el criterio `C-08` no se puede cumplir. Asignado a @dev + @analista |
| Números del seed «corregidos» a mano | **Mitigado**: `docs/analisis/datos-seed.md` es la fuente única y el alcance se corrigió a los datos reales (D-21) |
| Disco `C:` al 94 % | Declarado por @devops; el stack completo ocupa ~2,5 GB y `D:` tiene 187 GB libres |

---

## 6. Acuerdos de la sesión

1. **Alcance cerrado:** 39 criterios `C-01`…`C-39` con ID único; es el **único denominador** de «100 % de
   cobertura» (D-18). Los criterios se corrigen **a favor del seed** cuando hay discrepancia (D-21).
2. **Nada se cierra por decisión:** un bug pasa a *Cerrado* con la corrida verde pegada. @qa re-verifica
   TC-01, TC-02 y TC-03 cuando @devops los aplique.
3. **Regla de documentación** (pedido del dueño): cada documento lleva **índice y fecha**, **cita el archivo
   o el comando del que sale cada afirmación**, y **no documenta funcionalidad que no exista**: lo bloqueado
   se escribe como *«pendiente — bloqueado por T\<xx\>»*.
4. **La documentación vive en `docs/`** y `docs/decisiones.md` es la tabla vigente: se cita, no se duplica
   (D-20). `docs/manual-usuario.md` se escribe **después de T2.4** (necesita el SPA real).
5. **Nada destructivo sin aprobación explícita** del dueño: `docker compose down -v` borra los datos locales,
   e instalar minikube cambia software del sistema (A-02).
6. **Los entregables académicos finales** (DOCX + PPTX: portada, formato, normas de la facultad y firma) los
   cierra el dueño sobre el borrador que arma @documentador (D-22).

---

## 7. Anexo: cómo reproducir la verificación del Sprint 0

```bash
cd /d/dev/equipo/gs08-matriculas

# 1. Infraestructura sin Docker (lo mismo que corre el CI): 21 OK, exit 0
python scripts/validar_infra.py

# 2. Stack en marcha: 9 OK, exit 0   (requiere los contenedores arriba)
python scripts/verificar_stack.py

# 3. Humo de infraestructura por el proxy: 8 OK, exit 0
bash scripts/smoke_api.sh --infra

# 4. Modelo de datos (PostgreSQL desechable, puerto 55432): 49 OK, exit 0
bash db/verificacion/ejecutar_verificacion.sh

# 5. Manifiestos de Kubernetes: 11 objetos
kubectl kustomize k8s/
```

Corrida de referencia hecha por @documentador el **21/09/2026 22:44**: los 5 pasos anteriores en verde
(7 contenedores arriba según `docker ps`). Salidas pegadas en `README.md` §7.
