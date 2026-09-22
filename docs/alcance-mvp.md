# GS08 · Matrículas y Notas — Alcance del MVP

**Autor:** @pm · **Fecha:** 21/09/2026 · **Sprint 0** · Repo: `D:\dev\equipo\gs08-matriculas`

**Qué es este documento:** el compromiso de alcance. Lo que sí entra, lo que **no** entra, y cómo se
comprueba cada cosa. Todo criterio está escrito para poder ejecutarse y ver el resultado: una cifra, un
código HTTP o una ruta de evidencia. Si un criterio no se puede verificar, no está aquí.

**Insumos que leí (nada inventado):** `legacy/script.sql.txt` y los 8 módulos PHP del sistema de Web III,
`docs/analisis/modelo-datos.md` (49 comprobaciones, exit 0) y `docs/devops/plan-contenedores-ci.md`.
Verifiqué yo mismo el stack de @devops con `docker ps`: 7 contenedores arriba (6 del profile `obs` +
la base de verificación del analista), y comprobé que `kubectl` existe pero **no hay contexto** y que
minikube, kind y k3s **no están instalados**.

---

## 1. Problema

El área administrativa de una institución educativa matricula estudiantes, mantiene el catálogo de cursos
y registra calificaciones. Hoy lo hace con un sistema PHP+MySQL de 4 tablas que **funciona pero no se
puede sostener**:

| Lo que duele hoy (comprobado en `legacy/`) | Consecuencia |
|---|---|
| No hay API: cada pantalla arma su SQL (`config/database.php` + PDO en cada `.php`) | no se puede integrar ni automatizar; no hay contrato que probar |
| El buscador usa `LIKE '%texto%'` y depende de la collation `utf8mb4_unicode_ci` de MySQL | en PostgreSQL devuelve **0 filas** sin avisar (medido: `ILIKE` 2 filas vs `LIKE` 0) |
| Los listados no paginan (no hay `LIMIT`/`OFFSET` en ningún `index.php`) | se degrada con el volumen |
| Las reglas viven en PHP disperso (`create.php`, `edit.php`, `delete.php`) | borrar un curso arrastra sus matrículas **en silencio**; nadie lo ve antes |
| No hay ninguna prueba automatizada | cada cambio es a ciegas |
| No hay contenedores, ni CI, ni métricas, ni despliegue reproducible | no hay forma de demostrar que funciona en otro lado |
| El sistema se llama "Sistema Administrativo Web" y **no tiene notas** | el nombre del proyecto del curso promete matrículas **y notas** |

**Lo que resuelve el MVP:** el mismo proceso administrativo (estudiantes, cursos, matrículas, usuarios)
más las **notas**, sobre una API con contrato probado, en contenedores, desplegable y observable. No es
un rediseño de escaparate: es el mismo problema con ingeniería verificable detrás.

---

## 2. Usuarios

| Actor | Rol en el sistema | Qué hace |
|---|---|---|
| **Asistente administrativo** | `asistente` | el usuario principal: registra estudiantes, matrículas y notas; consulta el panel y las boletas |
| **Administrador** | `admin` | todo lo del asistente + gestión de usuarios + operaciones destructivas (borrados) |
| **Docente** | — | **fuera del MVP**: en la v1 las notas las carga el área administrativa. Una nota no está atada a un docente porque el legacy no tiene tabla de docentes y no la voy a inventar |
| **Público / estudiante** | — | **fuera del MVP**: no hay portal de estudiantes ni autenticación de alumnos |

---

## 3. Caso de uso principal — «de la matrícula a la nota»

Es el hilo que tiene que funcionar de punta a punta; **es la prueba de aceptación del MVP** y es lo que se
va a mostrar en la sustentación. Cualquiera de estos pasos que falle, el MVP no está listo.

1. El asistente abre el SPA, entra con `admin` / `Admin123!` y ve el panel.
2. El panel muestra **12 estudiantes activos, 7 cursos activos, 23 matrículas activas, 1 usuario activo**,
   el top 5 de cursos con más matrículas activas y los últimos 6 estudiantes (`docs/analisis/modelo-datos.md` §4.1).
3. Busca `huaman` en estudiantes → encuentra a los que se apellidan **Huamán** (tildes incluidas).
4. Registra un estudiante nuevo: la API responde `201` y el estudiante aparece en el listado.
5. Crea (o elige) un curso de 3 créditos para el periodo `2026-02`.
6. Matricula al estudiante → `201`; lo intenta matricular otra vez en el mismo curso y periodo → `409`
   con el mensaje «Ese estudiante ya está matriculado en ese curso para el periodo indicado».
7. Filtra el listado de matrículas por periodo `2026-02` y ve la suya con nombre de estudiante y curso.
8. Le registra tres notas: `practica` 1 = 14, `parcial` 1 = 16, `final` 1 = 18.
9. Abre la boleta del estudiante en `2026-02`: ve la nota del curso y el promedio del periodo ponderado
   por créditos.
10. Grafana muestra las peticiones de ese recorrido (`http_requests_total` con el path del SPA) y
    `/api/v1/health` responde `200` por el proxy.

---

## 4. Alcance del MVP (lo que SÍ se hace)

Seis bloques funcionales + uno transversal. Cada criterio tiene **ID único** (`C-01`…`C-39`): **39 criterios**, y ese es **el único denominador** de T4.2 («100 %» = estos 39 con evidencia) y el número que @qa usa en su matriz (un caso por criterio; si un criterio necesita dos casos, se citan los dos bajo el mismo `C-xx`).

### AP-01 · Autenticación y sesión
- El usuario entra con **nombre_usuario o email** + contraseña (igual que `login.php`: `WHERE nombre_usuario = :u1 OR email = :u2`).
  - **C-01** ✅ `POST /api/v1/auth/login` con `{"usuario":"admin","password":"Admin123!"}` → **200** y token; con `{"usuario":"admin@horizonte.edu.pe", ...}` → **200** también.
- Un usuario con `estado = false` **no entra**, ni con la contraseña correcta.
  - **C-02** ✅ Con el usuario desactivado, el login responde **401** con mensaje; no se emite token.
- El hash `$2y$10$...` del seed **se usa tal cual** (no se regenera).
  - **C-03** ✅ `pytest` con un test que hace `bcrypt.checkpw(b'Admin123!', hash_del_seed) → True`.
- Ningún usuario puede desactivar ni eliminar su propia cuenta (regla `usuarios/edit.php` del legacy).
  - **C-04** ✅ `PUT`/`DELETE` sobre el propio `id` → **409** con mensaje; la fila queda intacta.

### AP-02 · Panel (dashboard)
- **C-05** ✅ Con el seed: `GET /api/v1/dashboard` → **200** con `estudiantes_activos=12`, `cursos_activos=7`,
  `matriculas_activas=23`, `usuarios_activos=1`, top 5 cursos y últimos 6 estudiantes.
- **C-06** ✅ La suma de matrículas activas del top 5 por curso es **≤ 23** y el listado de cursos coincide con la
  vista (`v_matriculas_detalle`), no con un conteo paralelo.
- **C-07** ✅ Panel vacío no es error: sin matrículas, el top devuelve `[]` y la API responde **200**.

### AP-03 · Estudiantes
- Buscar por código, DNI, nombres o apellidos, **sin distinguir mayúsculas ni tildes** (`ILIKE`).
  - **C-08** ✅ `GET /api/v1/estudiantes?q=huaman`, `?q=Huamán` y `?q=HUAMAN` devuelven **la misma cantidad** de filas (≥ 1); con `q=` como el legacy (`LIKE`) devolvería **0** — el test lo deja fijado.
  - **C-09** ✅ `?q=E20260001` (código) y `?q=45123456` (DNI, del seed) devuelven exactamente 1 fila.
- **C-10** ✅ Listado paginado:  `GET /api/v1/estudiantes?page=1&page_size=25` → 25 filas + `total`; `page_size=0` o `200` → **422**.
- **C-11** ✅ Alta y edición:  `POST` válido → **201**; DNI de 7 dígitos, DNI repetido, código repetido, email con
  formato inválido → **422** con el campo en el mensaje. **Nunca 500.**
- **C-12** ✅ Baja lógica (no borra):  `estado=false` → desaparece del selector de matrícula y baja el KPI de
  estudiantes activos en exactamente 1; sigue visible en `?estado=inactivo`.
- Eliminar con matrículas: ver AP-08.

### AP-04 · Cursos
- **C-13** ✅ `creditos=0` u `11` → **422**; `horas=0` → **422**; `creditos` sin enviar → se guarda **3** (default del legacy).
- **C-14** ✅ Código repetido → **409**.
- **C-15** ✅ Baja lógica igual que estudiantes; el curso inactivo no aparece en el selector de matrícula.

### AP-05 · Matrículas
- **C-16** ✅ Crear matrícula válida → **201**; aparece en `GET /api/v1/matriculas?periodo=2026-02`.
- **C-17** ✅ Mismo estudiante + mismo curso + mismo periodo → **409** (regla central del legacy, `UNIQUE uq_matricula`).
- **C-18** ✅ Periodo `2026-13`, `2026/02` o `26-02` → **422**.
- **C-19** ✅ Estudiante o curso inexistente → **404**.
- **C-20** ✅ **Retirar** (no borrar): `PUT` con `estado="retirado"` → **200**; el KPI de matrículas activas baja
  exactamente **1**, la fila sigue en el listado con el badge «Retirado» y sigue en el historial.
- **C-21** ✅ Filtro por texto (`q`, busca por estudiante y curso) y por periodo, combinables.

### AP-06 · Usuarios (solo `admin`)
- **C-22** ✅ Crear/editar/desactivar; `nombre_usuario` repetido → **409**; contraseña de 7 caracteres → **422**;
  rol distinto de `admin`/`asistente` → **422**.
- **C-23** ✅ Un `asistente` que llama a `/api/v1/usuarios` recibe **403**.

### AP-07 · Notas y boleta *(entra al MVP — decisión D-01)*
- **C-24** ✅ Registrar nota de una **matrícula activa**: `tipo` ∈ {`practica`,`parcial`,`final`}, `numero ≥ 1`,
  `nota` entre **0 y 20** → **201**.
- **C-25** ✅ `nota=21`, `nota=-1`, `tipo="examen"` → **422**; duplicar (`matricula_id`,`tipo`,`numero`) → **409**.
- **C-26** ✅ Registrar nota sobre una matrícula `retirado` → **409** con mensaje (no se califica a quien se retiró).
- **C-27** ✅ **Nota del curso** = media aritmética de las notas registradas, redondeada a 2 decimales
  (14, 16, 18 → **16.00**). **Promedio del periodo** = media ponderada por créditos de los cursos con notas.
- **C-28** ✅ `GET /api/v1/estudiantes/{id}/boleta?periodo=2026-02` → detalle por curso con sus notas, nota del
  curso y promedio; un curso **sin notas** sale con `nota: null` y **no** cuenta como 0 en el promedio.
- **C-29** ✅ La nota cuelga de la **matrícula**, no del estudiante: borrar el estudiante borra sus notas (cascada);
  retirar la matrícula **no** borra las notas ya registradas.

### AP-08 · Integridad y borrados destructivos *(decisión D-02)*
- **C-30** ✅ `DELETE /api/v1/estudiantes/{id}` o `/api/v1/cursos/{id}` con matrículas → **409** con el conteo
  exacto: `{"detail":"...","matriculas":N}`. **No borra nada.**
- **C-31** ✅ Con `?confirmar=true` → **204** y el conteo de matrículas baja exactamente **N** (verificado con el
  seed: borrar el curso 5 elimina sus 3 matrículas; borrar el estudiante 2, sus 2).
- **C-32** ✅ La confirmación es una segunda llamada explícita: **nada** se borra en cascada por accidente.

### AP-09 · Transversal (infra, observabilidad y entrega)
- **C-33** ✅ `docker compose --profile obs up -d` deja **6 contenedores** arriba y
  `python scripts/verificar_stack.py` sale con **exit 0** (9 comprobaciones). *Ya cumplido por @devops.*
- **C-34** ✅ Salud y métricas (decisión **D-17**): `http://localhost:8080/api/v1/health` → **200** del API
  real (hoy responde el stub de humo; la prueba se repite cuando @dev integre). `/metrics` se lee **directo
  del API** en `http://localhost:8000/metrics`: Prometheus no scrapea a través del balanceador, porque
  mezclaría las métricas de las dos instancias. Y nginx responde **404** —no el `index.html`— en
  `http://localhost:8080/health` y `http://localhost:8080/metrics`, para que ningún chequeo de código HTTP
  dé por bueno un `/metrics` que no trae métricas (BUG-05 de @qa).
  Prueba: `curl -o /dev/null -w '%{http_code}' http://localhost:8080/metrics` → **404**.
- **C-35** ✅ Balanceo visible: `for i in $(seq 1 6); do curl -s -o /dev/null -D - http://localhost:8080/api/v1/health | grep -i x-upstream-addr; done`
  alterna las dos instancias; y con `gs08-api-b` apagado la petición igual responde **200** (failover).
- **C-36** ✅ Grafana `http://localhost:3000/d/gs08-matriculas` muestra tráfico **del SPA real** (no del stub).
- **C-37** ⛔ **Kubernetes real** (bloqueado hoy): `kubectl get pods -n gs08` → **3/3 Running** y la app responde
  por el ingress de minikube. Hoy no existe cluster: `current-context is not set`, y minikube/kind/k3s
  **no están instalados** (verificado por @pm). Los 11 objetos de `k8s/` ya validan con
  `kubectl kustomize` (21 OK en `scripts/validar_infra.py`), pero eso **no es** un cluster.
- **C-38** ✅ `pytest` en verde en `backend/tests/` con **al menos 15 pruebas negativas** (una por regla
  RN-01…RN-15 de `docs/analisis/modelo-datos.md` §3) y una prueba de extremo a extremo del caso principal (§3).
- **C-39** ✅ CI verde en el push a `main` del repo público: lint + tests + build de las dos imágenes.

---

## 5. Lo que NO se hace en esta versión (v1)

Lista cerrada. Si algo de acá aparece en la sustentación como «faltó», esta es la respuesta: fue decisión,
no olvido.

**Fuera por alcance funcional**
1. **Portal del estudiante** y cualquier autenticación de alumnos: no existe tabla de usuarios-estudiante.
2. **Rol docente** y asignación de docentes a cursos: el legacy no tiene tabla de docentes.
3. **Pagos, cobranza, matrícula con recibo o caja**.
4. **Horarios, aulas, secciones, turnos y cupos/vacantes**.
5. **Asistencia y justificaciones**.
6. **Actas oficiales, cierre de periodo, orden de mérito, certificados o constancias** (PDF imprimible).
7. **Historial académico multi-periodo consolidado**, reincorporaciones y convalidaciones.
8. **Pesos por tipo de evaluación** (práctica 30 %, parcial 30 %, final 40 %) — la v1 usa media aritmética
   por curso; ver decisión D-03. Cambiarlo es un cambio de una función, no de esquema.

**Fuera por alcance técnico (y por qué no hace falta para aprobar)**
9. **Migración automática de datos del MySQL legacy**: se reusa el **seed tal cual** (12/7/24). No hay
   ETL ni script de migración de datos reales.
10. **Auditoría** de quién creó/editó cada registro (`creado_por`, triggers): el legacy tampoco la tenía.
11. **Recuperación de contraseña por email, 2FA, SSO, bloqueo por intentos fallidos**.
12. **Notificaciones** por correo/SMS/WhatsApp.
13. **App móvil** y PWA: el SPA es responsive en el navegador, nada más.
14. **Multi-institución / multisede / multi-tenant** e i18n.
15. **HPA (autoescalado), TLS/HTTPS en el ingress, secrets gestionados por Vault/SealedSecrets**:
    el `k8s/` es un entorno local de demostración, no producción.
16. **Despliegue en nube o cluster gestionado** (EKS/GKE/AKS): el requisito es Kubernetes **local**.
17. **Backups automáticos y cifrado en reposo** de la base: el volumen de Docker es desechable.
18. **Pruebas de carga formales** (k6/JMeter): las mediciones de `ILIKE` vs índice trigram (112 ms vs
    0,09 ms con 100.000 filas) están hechas con `EXPLAIN ANALYZE`, no con una prueba de carga.
19. **Impresión / exportación** a Excel o PDF de cualquier listado.
20. **Frontend con gestor de estado global** (Pinia) o librería de componentes: se resuelve con
    composables + Tailwind, que es lo que el curso pide.

---

## 6. Riesgos y mitigación

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| No hay cluster Kubernetes local y el entregable lo exige | Alta (hoy es un hecho) | **Instalar minikube con driver docker** (decisión D-04) en paralelo al Sprint 1. Si minikube no arranca en Windows, plan B: `kind`. Los manifiestos y el kustomize ya están validados, así que el trabajo restante es arrancar el cluster y desplegar |
| Repo público y credenciales de GitHub llegan al final | Alta | El repo local ya tiene historial con la rama `main` (D-05) y los workflows disparan con `push`, `pull_request` y `workflow_dispatch`; el primer push corre CI sin tocar nada. CD se autodesactiva si falta `KUBE_CONFIG_B64`/`DEPLOY_ENABLED` |
| Las notas entran al final del cronograma y el tiempo aprieta | Media | Corte planificado: si se corta, la app queda con el esquema de notas documentado y verificable (`docs/analisis/modelo-datos.md` §7) y se declara como «sistema preparado para notas». El corte se anuncia en Sprint 3, no se improvisa el último día |
| Dos fuentes de verdad del esquema (`db/init/*.sql` vs Job de migraciones Alembic) | Media | @dev genera la **revisión inicial de Alembic desde `db/init/`** y la verificación de @analista compara ambos DDL (Sprint 1) |
| `ILIKE` + `unaccent` se olvida y el buscador devuelve 0 filas | Media | Prueba negativa en `pytest` que exige el mismo resultado para `huaman`/`Huamán`/`HUAMAN`; sin ella el sprint no cierra |
| Números del seed «corregidos» a mano (ids con huecos, hash `$2y$`) | Media | Los números 12/7/24 y `admin`/`Admin123!` son el contrato de prueba; cualquier otro número es bug (dicho por @analista). Nadie «arregla» el hash ni las secuencias |
| El entorno de demostración no queda disponible el día de la sustentación | Baja | Guion de arranque en `docs/devops/COMANDOS.md` + verificación de un comando (`verificar_stack.py`, exit 0) antes de exponer |

---

## 7. Pregunta abierta (una sola)

**¿Cuál es la fecha de entrega y la fecha de exposición del GS08?** El alcance, los criterios y el
reparto ya están cerrados sin ese dato, pero **el calendario de los 4 sprints no lo puedo fechar**: no
sé cuántas semanas tengo hasta la entrega ni si la exposición es la misma semana. Con la fecha, convierto
los bloques de `backlog-sprints.md` en semanas con fecha límite y te digo qué se corta si el tiempo no
alcanza.
