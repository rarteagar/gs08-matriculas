# GS08 · Matrículas y Notas — Seguridad, ética y sostenibilidad

**Entregable:** TD-08 de `docs/backlog-sprints.md` · **Redacta:** @documentador · **Fecha:** 21/09/2026
**Rama:** `main` @ `e051d43` · **Repo:** `D:\dev\equipo\gs08-matriculas`

**Qué es este documento y qué no es.** Es un **mapa de lo que el sistema hace hoy** en seguridad, tratamiento
de datos y costo/sostenibilidad, con la cita del archivo o del comando del que sale cada afirmación. **No es
un dictamen legal**: lo que depende de interpretación normativa está marcado como *«a verificar con asesoría»*.

**Estado general:** la infraestructura de seguridad que se describe acá **existe y está verificada** (hash
del seed, contenedores sin privilegios, secretos fuera de git, escaneo de vulnerabilidades). Lo que depende
del código de la aplicación (roles, tokens, `403` por rol) es **contrato, no implementación**: el API es T1.1.

## Índice

1. [Seguridad](#1-seguridad)
2. [Ética y datos personales](#2-ética-y-datos-personales)
3. [Sostenibilidad](#3-sostenibilidad)
4. [Lo que todavía NO está protegido (dicho de frente)](#4-lo-que-todavía-no-está-protegido-dicho-de-frente)
5. [Marco legal a verificar con asesoría](#5-marco-legal-a-verificar-con-asesoría)
6. [Declaración de uso de IA](#6-declaración-de-uso-de-ia)
7. [Resumen en una tabla](#7-resumen-en-una-tabla)

---

## 1. Seguridad

### 1.1 Contraseñas: bcrypt con coste 10 y el hash `$2y$` heredado

| Punto | Realidad verificada | Fuente |
|---|---|---|
| Algoritmo y coste | **bcrypt coste 10** (`$2y$10$…`) — el coste está en el propio prefijo del hash del seed | `db/init/03-seed.sql`, `docs/analisis/modelo-datos.md` §1.1 |
| ¿El hash del seed sirve? | **Sí:** `bcrypt.checkpw(b'Admin123!', hash) → True` con `bcrypt==4.2.1` (la librería que usará el API) | `docs/analisis/evidencia/hash-legacy-python-bcrypt.txt` |
| ¿Se regenera el hash? | **No** (D-12): conserva la trazabilidad con el legacy y está verificado que funciona | `docs/decisiones.md` D-12 |
| El hash no viaja en claro a ningún lado | La base solo lo guarda; la API lo compara con `bcrypt`. El hash de pgcrypto es solo diagnóstico | `docs/analisis/evidencia/diagnostico-hash-legacy.txt` |
| Longitud mínima | 8 caracteres, validada por la API → `422` con menos (criterio `C-22`); la BD no lo valida porque no puede ver el texto plano | `docs/alcance-mvp.md` `C-22`, `docs/analisis/modelo-datos.md` RN-01 |

> **Quirk documentado a propósito:** `pgcrypto` **no** valida un hash `$2y$` (calcula otro digest; solo
> coincide normalizando el prefijo a `$2a$`). Es un quirk de pgcrypto, **no** del hash: por eso la
> verificación de contraseñas es responsabilidad del API y no de la base. Nadie «arregla» el prefijo.

### 1.2 Tokens, roles y permisos

| Punto | Contrato | Estado |
|---|---|---|
| Autenticación | `POST /api/v1/auth/login` con **usuario o email** + contraseña → JWT; usa la regla del legacy `WHERE nombre_usuario = :u1 OR email = :u2` | ⬜ contrato (T1.1/T1.2). Hoy **404**, medido por @qa |
| Duración del token | `ACCESS_TOKEN_EXPIRE_MINUTES` = **60** por defecto | `.env.example` |
| Firma | `SECRET_KEY` obligatoria (`cambiar-esta-clave-en-produccion` como default de desarrollo) | `.env.example`, `docker-compose.yml` |
| Usuario inactivo | `estado = false` **no entra** ni con la contraseña correcta → `401` sin token | criterio `C-02` |
| Roles | `admin` \| `asistente` (CHECK en la base). Un `asistente` que llama a `/api/v1/usuarios` → **`403`** | criterio `C-23`, `docs/analisis/modelo-datos.md` RN-01 |
| Autoprotección | Nadie desactiva ni elimina **su propia cuenta** → `409` y fila intacta | criterio `C-04`, RN-11 (necesita el usuario de la sesión: **solo la API lo puede aplicar**, la base no) |
| Operaciones destructivas | `DELETE` con matrículas → `409` con el **conteo**; `204` solo con `?confirmar=true` (segunda llamada explícita) | D-02, criterios `C-30`-`C-32` |

**Nota honesta:** todo lo de esta tabla es **contrato con @dev** (`docs/devops/plan-contenedores-ci.md` §3)
y criterio de aceptación, **no** funcionalidad verificada. Se marca cerrado cuando `pytest` y el smoke de
@qa lo demuestren (`C-38`, T4.2).

### 1.3 Cabeceras de seguridad: 3 + 1

`frontend/nginx/default.conf.template` declara en el bloque `server`:

```
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
server_tokens off;        # la cabecera Server no filtra la versión de nginx
```

| Ruta | Hoy (medido) | Después de TC-02 |
|---|---|---|
| `/healthz` y el SPA | las **3** cabeceras + `Server: nginx` sin versión | igual |
| `/api/` (proxy) | **ninguna**: `add_header X-Upstream-Addr` en la `location` **corta la herencia** de los `add_header` del `server` (BUG-06) | las **4** (las 3 + `X-Upstream-Addr`) |

Evidencia: `docs/qa/reporte-bugs.md` BUG-06, con los dos `curl -D -` comparados. El arreglo es **TC-02**
(@devops) y lo verifica @qa con `curl -s -o /dev/null -D - http://localhost:8080/api/v1/health`.

**Endurecimiento adicional ya presente:** `server_tokens off` (no revela la versión de nginx) y `gzip`
declarado con `gzip_vary` — sin `ETag` ni listados de directorio.

### 1.4 Secretos: ninguno de verdad entra al repositorio

| Control | Cómo se garantiza | Fuente |
|---|---|---|
| Variables de entorno locales | `.env` está en `.gitignore` (con `!.env.example`) | `.gitignore` |
| Secret de Kubernetes | `k8s/02-secret.yaml` está en `.gitignore`; lo que se versiona es la **plantilla** `k8s/02-secret.example.yaml` con valores `CAMBIAR_…` | `.gitignore`, `k8s/02-secret.example.yaml` |
| Kubeconfig | `kubeconfig*` en `.gitignore` | `.gitignore` |
| Creación del secret real | Por comando, con `--dry-run=client`, para que no quede en el historial: `kubectl -n gs08 create secret generic gs08-secrets --from-literal=SECRET_KEY="$(openssl rand -hex 32)" …` | `k8s/02-secret.example.yaml` |
| Credenciales de demo | Están **declaradas como de desarrollo** (`admin` / `Admin123!`, `gs08_dev_pwd`, `gs08_grafana`): son datos de prueba del legacy, no credenciales reales, y se cambian antes de cualquier entrega | `.env.example`, `docs/devops/plan-contenedores-ci.md` §6 |

### 1.5 Cadena de suministro: SBOM, provenance y escaneo

| Control | Detalle | Fuente |
|---|---|---|
| **SBOM + provenance** | El CD construye con `docker/build-push-action` con `provenance: true` y `sbom: true` al publicar en GHCR | `.github/workflows/cd.yml` |
| **Escaneo de vulnerabilidades** | `trivy-action` en CI sobre `gs08-api:local`, severidad `CRITICAL,HIGH`, `ignore-unfixed: true` | `.github/workflows/ci.yml` |
| **El escaneo no bloquea** | `exit-code: "0"`: es **informativo** a propósito, para que una vulnerabilidad sin parche disponible no tumbe el CI. **Consecuencia:** hoy el CI puede quedar verde con hallazgos críticos; es una decisión declarada, no un descuido | `.github/workflows/ci.yml` |
| **Lint de Dockerfile** | `hadolint` con `failure-threshold: error` sobre los dos Dockerfiles | `.github/workflows/ci.yml` |
| **Imágenes fijadas por versión** | Nada de `:latest`; lo verifica `scripts/validar_infra.py` (21 comprobaciones) | `docs/devops/plan-contenedores-ci.md` §1 |
| **Contenedores sin privilegios** | API: `USER app` (uid 10001, sin login). Web: `USER nginx` (antes corría como root: hallazgo corregido). En k8s: `runAsNonRoot`, `allowPrivilegeEscalation: false`, `capabilities: drop: [ALL]` | `backend/Dockerfile`, `frontend/Dockerfile`, `k8s/20-api.yaml` |
| **Healthchecks** | Los dos Dockerfiles definen `HEALTHCHECK`; k8s usa `startup`/`readiness`/`liveness` probes en `/health` y `/healthz` | `backend/Dockerfile`, `frontend/Dockerfile`, `k8s/*.yaml` |

### 1.6 Superficie expuesta

**Puertos publicados al host** (todos **solo en local**, ninguno abierto a internet):

| Puerto | Servicio | Necesario para | ¿Debería exponerse fuera de local? |
|---|---|---|---|
| **8080** | nginx (SPA + proxy) | uso normal y demo | No sin TLS |
| **8000** | API directa (Swagger en `/docs`) | pruebas y `/metrics` (D-17) | No |
| **5432** | PostgreSQL | `psql` y las verificaciones del modelo | **No**: en el cluster **no** se publica (`Service` ClusterIP) |
| **9090** | Prometheus | targets y consultas | No |
| **3000** | Grafana | paneles | No |
| **55432** | PostgreSQL desechable de @analista | verificación del modelo (contenedor `gs08-analista-verif`) | No; se apaga con `docker rm -f gs08-analista-verif` |

> **Corrección de un dato del backlog:** TD-08 decía «superficie expuesta (4000/8080/3000/9090)». Verifiqué
> los puertos contra `docker-compose.yml` y **no existe ningún 4000**: los publicados son **8080, 8000, 5432,
> 9090 y 3000** (más el 55432 del contenedor de verificación). Dejé la lista real.

**Decisiones de exposición que ya están tomadas:** `/metrics` se lee **directo del API** y nginx responde
**404** en `/health` y `/metrics` (D-17) — así un chequeo de monitoreo no puede dar por bueno un endpoint que
no trae métricas. `/healthz` queda como healthcheck **del contenedor** nginx (lo usa Docker y `k8s`).
El `server_name` de nginx es `_` y en el cluster el Ingress solo enruta el host `gs08.local`.

---

## 2. Ética y datos personales

### 2.1 Qué datos personales maneja el sistema

| Dato | Dónde | Naturaleza | Tratamiento hoy |
|---|---|---|---|
| **DNI** (`char(8)`, UNIQUE) | `estudiantes` | **dato personal identificatorio** | Validado y único. No se publica en ningún listado abierto; viaja solo en la API autenticada |
| Nombres y apellidos | `estudiantes` | dato personal | indexados para el buscador |
| Email y teléfono (nullable) | `estudiantes`, `usuarios` | dato personal de contacto | opcionales; el email de estudiantes **es nullable** porque el legacy lo permite |
| Fecha de nacimiento, dirección (nullable) | `estudiantes` | dato personal | CHECK de fecha real; no se usan para ningún cálculo |
| **Notas** | `notas` (Sprint 3) | **dato sensible en el contexto educativo** | el DDL está escrito **sin aplicar**; entra cuando el alcance lo aprobó (D-01) |
| Contraseña | `usuarios.password_hash` | credencial | **nunca en texto plano**: sólo el hash bcrypt |
| Datos de salud o de menores | — | — | **no existen** en el modelo: no hay tabla de salud, ni de apoderados, ni de menores de edad |

**Minimización (principio aplicado, no declarado):** el esquema se limita a lo que el legacy necesitaba para
matricular y calificar. **No** se agregaron campos «por si acaso»: no hay dirección de salud, ni documentos
adjuntos, ni fotos, ni geolocalización, ni datos biométricos. Los tres datos que el legacy permitía dejar
vacíos (email, teléfono, fecha de nacimiento, dirección) siguen siendo **nullable** en PostgreSQL
(`docs/analisis/modelo-datos.md` §1.1).

**Trazabilidad del dato:** no se audita quién creó o editó cada registro (`creado_por`, triggers): decisión
**D-08**, porque el legacy tampoco lo hacía y no había requisito detrás. **Consecuencia ética declarada:** si
un DNI se carga mal, el sistema no puede decir quién lo hizo. Está anotado como supuesto en
`docs/analisis/modelo-datos.md` §9, no escondido.

### 2.2 Origen de los datos: son ficticios, no reales

| Dato | Origen | Por qué es éticamente correcto usarlo |
|---|---|---|
| 12 estudiantes, 7 cursos, 24 matrículas | **seed traducido del legacy** (`db/init/03-seed.sql`, del `legacy/script.sql.txt` del curso Web III) | Son **datos de prueba del sistema académico del curso**: nombres genéricos peruanos y DNI con estructura válida pero de ejemplo. **No** provienen de ningún estudiante real ni de una institución real |
| `admin` / `Admin123!` | idem | credencial de demo del legacy, público en el repositorio de origen |
| Instituto «Horizonte» | nombre del legacy | es el nombre ficticio que ya traía el material del curso |

**Compromiso explícito:** si en el Sprint 1+ se cargan datos reales (por ejemplo, en una prueba con el área
administrativa), esos datos **no** se versionan, no se pegan en la evidencia y el volumen local se destruye
después (`docker compose down -v`).

### 2.3 Ética de la ingeniería: lo que se declara en la sustentación

- **Lo que no existe, se dice que no existe.** El login responde `404` hoy y así está escrito en el README,
  en el manual técnico y en la matriz de pruebas: el criterio aparece como *bloqueado por T1.1*, nunca como
  cumplido. Lo mismo con Kubernetes (manifiestos listos, cluster no desplegado) y con el CI (sin remoto).
- **Nada de cifras inventadas.** Los números que aparecen en los documentos salen de `psql`, de `curl` o de
  un script con salida pegada. La regla se aplica al equipo completo (`docs/backlog-sprints.md`, regla de
  evidencia), no solo a los documentos.
- **Los bugs se publican con nombre y apellido.** El reporte incluye 4 bugs del **propio script de pruebas**
  de @qa y 3 defectos de infraestructura de @devops, además de las correcciones de los documentos de @pm.
  Una retrospectiva sin autocrítica no sirve para el sprint siguiente.
- **La demo no se maquilla.** Si el tiempo aprieta, el orden de corte está fijado de antemano (primero notas,
  después la regresión en k8s) y **se anuncia en la sustentación**, no se descubre al final
  (`docs/backlog-sprints.md` §«Orden de corte»).

---

## 3. Sostenibilidad

### 3.1 Costo: cero soles, cero nube

| Concepto | Realidad | Fuente |
|---|---|---|
| Infraestructura en la nube | **ninguna**: todo corre en la laptop de desarrollo (ASUS M1502YA, Docker Desktop local) | `docs/devops/evidencia-sprint0.md` §1 |
| Costo de licencias | **S/ 0**: Docker Desktop (uso personal), PostgreSQL, nginx, Prometheus, Grafana, Python, Node, FastAPI, Vue: todo open source | `docker-compose.yml`, los `Dockerfile` |
| Costo del cluster | minikube es **local**; Kubernetes es requisito del curso y no se contrata ningún cluster gestionado (ni EKS/GKE/AKS: fuera de alcance, §5 ítem 16) | `docs/alcance-mvp.md` §5 |
| Costo de CI/CD | GitHub Actions con minutos gratuitos; GHCR para las imágenes | `.github/workflows/` |
| Costo por dejar el stack encendido | El stack completo son 6 contenedores e imágenes de ~2,5 GB; se apaga con `docker compose down` (conserva datos) | `docs/devops/plan-contenedores-ci.md` §8 |

### 3.2 Consumo y huella técnica

| Práctica | Detalle |
|---|---|
| **Imágenes base mínimas** | `postgres:16.15-alpine3.24`, `nginx:1.31.6-alpine`, `node:22.23.2-alpine`: variantes **alpine**, sin paquetes innecesarios. La imagen del API es **multi-etapa** (`deps` → `runtime`, sin compiladores en la imagen final) |
| **Perfiles de compose** | Prometheus y Grafana van en el perfil `obs`: el arranque normal de la aplicación **no** arrastra ~1,5 GB de observabilidad |
| **Un contenedor por servicio** | 4 para la aplicación (db, api, api-b, web) + 2 opcionales de observabilidad: se puede apagar lo que no se usa |
| **Datos desechables** | El volumen `pgdata` es de desarrollo y se recrea con `down -v`; no hay backups automáticos (fuera de alcance, §5 ítem 17) y **eso está declarado** |
| **Observabilidad con retención acotada** | Prometheus con `--storage.tsdb.retention.time=15d` y logs de Docker con `max-size: 10m`, `max-file: 3` — el crecimiento del disco está limitado por configuración, no por disciplina |
| **Sin recursos desperdiciados en k8s** | Los deployments declaran `requests`/`limits` de CPU y memoria (API 100m/256Mi → 1/512Mi; web 50m/64Mi → 500m/256Mi) y `revisionHistoryLimit: 3` |
| **Escaneo que no bloquea el pipeline** | Trivy es informativo (`exit-code: 0`): decisión declarada en §1.5. **Deuda asumida:** endurecerlo a bloqueante cuando las imágenes estén estabilizadas |

### 3.3 Mantenibilidad: lo que hace barato seguir

| Práctica | Herramienta | Comando / archivo |
|---|---|---|
| Verificación del esquema | 49 comprobaciones automáticas, **incluidas 15 pruebas negativas** | `bash db/verificacion/ejecutar_verificacion.sh` |
| Verificación del stack | 9 comprobaciones HTTP, con **un solo comando** | `python scripts/verificar_stack.py` |
| Humo de la API | 27 comprobaciones, **4 códigos de salida** (`0` ok · `1` fallas · `2` sin stack · `3` API sin implementar) | `bash scripts/smoke_api.sh` |
| Validación sin Docker | 21 comprobaciones de YAML, dashboard, Dockerfile y versiones fijadas (es lo que corre el CI en `pull_request`) | `python scripts/validar_infra.py` |
| Configuración del dashboard | **provisionado desde el repositorio**: editar el JSON del host y Grafana lo refleja en 30 s (verificado: versión 2 → 3). No hay que importar nada a mano | `infra/grafana/dashboards/gs08-matriculas.json` |
| Runbook | Levantar, ver logs, consola SQL, reconstruir una imagen, k8s y **problemas frecuentes con su causa** | `docs/devops/COMANDOS.md` |
| Documentación con fuente | Cada documento cita el archivo o el comando (regla de la casa) | `docs/` |
| Entorno reproducible | Imágenes fijadas por versión: no hay deriva silenciosa por un `:latest` | `scripts/validar_infra.py` |

**Deuda técnica declarada** (para que no se confunda con olvido): Prometheus sin exporter de PostgreSQL ni de
nginx; CI sin haber corrido nunca en GitHub; `pytest` inexistente hasta T1.1; ausencia de pruebas de carga
fuera de alcance (§5 ítem 18).

---

## 4. Lo que todavía NO está protegido (dicho de frente)

| Falta | Riesgo real hoy | Estado |
|---|---|---|
| **HTTPS/TLS en todas las capas** | El tráfico local va en HTTP plano (aceptable en `localhost`; **inaceptable** fuera de la máquina) | **Fuera de alcance** declarado (§5 ítem 15): el `k8s/` es un entorno de demostración |
| **Rate limiting y bloqueo por intentos fallidos** | Nada impide probar contraseñas en bucle contra `/api/v1/auth/login` | **Fuera de alcance** (§5 ítem 11) |
| **2FA, SSO, recuperación de contraseña** | No existen | Fuera de alcance (§5 ítem 11) |
| **Secretos «de verdad»** (Vault/SealedSecrets) | Los secretos de k8s son un `Secret` Opaque normal; en el cluster local es aceptable | Fuera de alcance (§5 ítem 15) |
| **Puerto 5432 publicado al host** | Cualquiera con acceso a `localhost` entra a la base con las credenciales de demo | Aceptable en local; en k8s el `Service` es ClusterIP (no se publica) |
| **`/docs` (Swagger) abierto** | Documenta el contrato completo sin autenticación | Aceptable en local; a decidir con TLS en un entorno público |
| **Sin auditoría de cambios** | No se sabe quién editó qué (D-08) | Decidido así (§5 ítem 10) |
| **Sin cifrado en reposo ni backups** | El volumen es desechable | Fuera de alcance (§5 ítem 17) |
| **Escaneo de dependencias del APK/npm** | Trivy escanea la imagen; no hay `npm audit`/`pip-audit` dedicados y el escaneo no bloquea | Deuda asumida (§3.2) |

---

## 5. Marco legal a verificar con asesoría

> **Esto no es un dictamen legal.** Es el mapa de puntos que hay que **confirmar con asesoría** antes de
> tratar datos de personas reales. El sistema del curso trabaja con datos ficticios y en una máquina local,
> así que hoy el riesgo es nulo; el mapa existe para que el día que se use con datos reales no se improvise.

| Punto | Qué dice el criterio razonable | Qué hay que verificar |
|---|---|---|
| **Ley 29733 (Protección de Datos Personales, Perú)** y su reglamento | El DNI, nombres, email, teléfono, fecha de nacimiento y dirección son **datos personales**; las **notas** pueden considerarse datos sensibles en el contexto educativo | Si corresponde **inscripción del banco de datos** ante la ANPD, y si el proyecto es «tratamiento» alcanzado por la norma aun siendo académico |
| **Consentimiento y finalidad** | Los datos se usan solo para matrícula y calificación (finalidad legítima del servicio educativo) | Cómo se documenta el consentimiento del titular y si alcanza con el reglamento interno de la institución |
| **Derechos ARCO** (acceso, rectificación, cancelación, oposición) | El sistema permite **rectificar** (edición) y **cancelar lógicamente** (baja lógica) | Quién atiende el pedido, en qué plazo y con qué constancia; hoy **no hay exportación de datos del titular** (fuera de alcance, §5 ítem 19) |
| **Seguridad de la información (art. 5 del reglamento)** | Medidas razonables: bcrypt, roles, mínimo privilegio, secretos fuera del código | Si el nivel de seguridad implementado es **proporcional** y qué falta documentar formalmente (política de seguridad) |
| **Menores de edad** | El sistema **no** guarda datos de menores ni de apoderados | Si el rubro educativo obliga a alguna salvaguarda adicional aunque no haya menores en el modelo |
| **Retención y destrucción** | Los datos del volumen local se destruyen con `docker compose down -v` | Plazo de conservación exigible para registros académicos (suele ser mayor que el del proyecto) |
| **Propiedad del código y del material del curso** | `legacy/` es material del curso Web III; el código nuevo es del autor | Licencia de uso del material original y si su reutilización académica requiere autorización |
| **Accesibilidad y no discriminación (uso ético)** | La UI debe ser usable con teclado y con foco visible; los mensajes de error son del backend, en español | Si se requiere un estándar formal (p. ej. WCAG) para la entrega |

---

## 6. Declaración de uso de IA

Se declara explícitamente, porque un jurado tiene derecho a saberlo:

| Punto | Declaración |
|---|---|
| **Cómo se construyó el proyecto** | El trabajo se desarrolló en una **sala de equipo con agentes de IA** (Hermes Agent), cada uno con un rol —alcance, análisis de datos, infraestructura, pruebas, documentación—, **bajo la dirección y validación del dueño del proyecto**, que aprueba el alcance, autoriza lo destructivo y cierra los entregables |
| **Qué hizo cada parte** | Los agentes escribieron el código, los scripts y los documentos; **el dueño decide** lo que entra al alcance y lo que se corta, aprueba instalar software nuevo (A-02) y cierra el DOCX y el PPTX académicos (D-22) |
| **Los datos y las salidas son reales** | Ninguna evidencia de este proyecto es generada por IA en el sentido de inventada: cada salida pegada sale de un `docker`, `curl`, `psql` o `pytest` corrido en la máquina. El seed viene del legacy del curso, no se inventó un dato |
| **Los números se verifican a mano** | Los conteos (12/7/24, los 39 criterios, los 4 bugs del propio script) se verificaron con un método explícito —`psql`, conteo por ID, comparación de dos corridas— justamente porque la IA puede equivocarse: el Sprint 0 documenta **cuatro correcciones de documentos escritos por el equipo** |
| **Lo que la IA no hizo** | No se usaron imágenes ni audio generados para la entrega, no se inventaron resultados de pruebas, no se simularon capturas, y ninguna evidencia se pegó «de ejemplo» |
| **Riesgo declarado** | Un texto escrito por IA puede sonar seguro de más. La defensa adoptada: **cada afirmación de los documentos cita el archivo o el comando del que sale**, y todo lo que no existe se escribe como *pendiente / bloqueado* |

---

## 7. Resumen en una tabla

| Dimensión | Qué hay hoy | Qué falta y cuándo |
|---|---|---|
| **Seguridad · contraseñas** | bcrypt coste 10, hash `$2y$` del seed verificado con `bcrypt` 4.2.1, sin regenerar (D-12) | Nada pendiente de esta parte |
| **Seguridad · acceso** | Roles `admin`/`asistente` en la base; `403` y `409` como contrato y criterio | Implementación del API (**T1.1/T1.2**) y su `pytest` (**C-38**) |
| **Seguridad · cabeceras** | 3 cabeceras en el SPA y `server_tokens off` | Las 4 en `/api/` (**TC-02**, @devops) con verificación de @qa |
| **Seguridad · secretos** | Nada real en git: `.env` y `k8s/02-secret.yaml` ignorados; plantilla versionada | Secretos gestionados (Vault) — fuera de alcance |
| **Seguridad · cadena de suministro** | SBOM + provenance en GHCR, trivy (informativo), hadolint, versiones fijadas, contenedores no root | CI corriendo de verdad en GitHub (**T4.1**); trivy bloqueante: deuda asumida |
| **Superficie** | 5 puertos, todos en local; `/metrics` directo y nginx 404 en `/health` y `/metrics` (D-17) | TLS — fuera de alcance |
| **Ética · datos** | Datos **ficticios** del legacy; minimización aplicada; sin datos de salud ni de menores; DNI y notas identificados como datos personales/sensibles | Mapa legal a verificar con asesoría (§5) |
| **Ética · ingeniería** | Lo bloqueado se declara; bugs propios publicados; cero cifras inventadas; orden de corte fijado de antemano | Se mantiene en cada sprint |
| **Sostenibilidad · costo** | S/ 0: todo open source y local, sin nube, CI en el plan gratuito | — |
| **Sostenibilidad · consumo** | Alpine, multi-etapa, perfiles de compose, retención acotada de métricas y logs, requests/limits en k8s | Exporters de PostgreSQL/nginx (Sprint 1, si alcanza) |
| **Sostenibilidad · mantenibilidad** | 49 + 27 + 21 + 9 comprobaciones con un comando cada una, dashboard provisionado, runbook y documentación con fuente | Pruebas del API (T1.1/T1.2) y suite de notas (T3.2) |

---

**Archivos de los que sale este documento:** `.gitignore`, `.env.example`, `docker-compose.yml`,
`frontend/nginx/default.conf.template`, `backend/Dockerfile`, `frontend/Dockerfile`, `k8s/02-secret.example.yaml`,
`k8s/20-api.yaml`, `.github/workflows/ci.yml`, `.github/workflows/cd.yml`, `infra/prometheus/prometheus.yml`,
`db/init/03-seed.sql`, `docs/analisis/modelo-datos.md` §1 y §9, `docs/analisis/datos-seed.md`,
`docs/analisis/evidencia/hash-legacy-python-bcrypt.txt`, `docs/devops/plan-contenedores-ci.md` §1-3 y §8,
`docs/devops/evidencia-sprint0.md` §1, `docs/qa/reporte-bugs.md` BUG-06, `docs/alcance-mvp.md` §4-§5,
`docs/decisiones.md` (D-01, D-02, D-08, D-12, D-17, D-22).
