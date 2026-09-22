# GS08 · Matrículas y Notas — Alcance final

**Fijado por el dueño el 21/09/2026.** Este documento manda sobre cualquier lista anterior de alcance:
lo entregado antes queda **congelado** y no se reescribe. Una página, sin más archivos.

## 1. Endpoints que sí se implementan (solo listar, crear y editar)

| Grupo | Endpoints |
|---|---|
| **health** | `GET /health` · `GET /api/v1/health` |
| **autenticación** | `POST /api/v1/auth/login` |
| **estudiantes** | `GET /api/v1/estudiantes` · `POST /api/v1/estudiantes` · `PUT /api/v1/estudiantes/{id}` |
| **cursos** | `GET /api/v1/cursos` · `POST /api/v1/cursos` · `PUT /api/v1/cursos/{id}` |
| **matrículas** | `GET /api/v1/matriculas` · `POST /api/v1/matriculas` · `PUT /api/v1/matriculas/{id}` |

Los `GET` devuelven la lista completa: **sin filtros avanzados y sin paginación fina**. Los endpoints de
usuarios, notas, boleta y dashboard que ya existen en el repositorio **quedan fuera del alcance y de la
demo**; no se borran porque no se toca lo entregado.

## 2. Vistas del SPA (una sola página, 4 vistas)

| # | Vista | Qué hace |
|---|---|---|
| 1 | **Login** | entra con `nombre_usuario` o email + contraseña; si falla, muestra el error |
| 2 | **Panel** | KPIs de estudiantes, cursos y matrículas **contados desde las tres listas** (sin endpoint de dashboard) y accesos a las otras vistas |
| 3 | **Estudiantes** | lista + formulario de alta y edición |
| 4 | **Matrículas** | lista + formulario de alta y edición, con selectores de estudiante y curso (los datos salen de `GET /api/v1/estudiantes` y `GET /api/v1/cursos`) |

Sin librería de componentes, sin animaciones y sin diseño elaborado: que funcione y se vea ordenado.

## 3. Infraestructura

1. **Docker Compose** con `db` + `api` + `web`, NGINX balanceando entre las instancias del API, y el
   **stub reemplazado por la API real**.
2. **minikube** con los **3 pods arriba** y el **job de migración Complete**.
3. **Prometheus + Grafana** con el **dashboard que ya existe**.

## 4. Fuera del alcance (definitivo)

Módulo de usuarios · notas · boleta · bajas lógicas con confirmación · borrados (`DELETE`) · filtros
avanzados · paginación fina · pipeline de CD · push al repositorio público (lo hace el dueño al final) ·
cualquier criterio de aceptación nuevo.

## 5. Documentos que quedaron falsos (se anota, no se reescribe)

`README.md`, `docs/manual-tecnico.md`, `docs/arquitectura.md` y el paquete de `docs/informe/` describen como
existentes el módulo de usuarios, las pantallas de cursos y usuarios, y las notas/boleta con sus endpoints;
las láminas 6 y 10 siguen con «28 endpoints» y «4 incumplidos por los dos 500». Por orden del dueño
**no se reescriben**: queda anotado aquí y reportado en la sala.
