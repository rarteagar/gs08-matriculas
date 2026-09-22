# Carpeta de inicializacion de PostgreSQL

Los archivos `*.sql`, `*.sql.gz` y `*.sh` de esta carpeta los ejecuta la imagen
`postgres` (entrypoint) **una sola vez**, cuando se crea el volumen `pgdata`.
Se ejecutan en orden alfabetico; por eso se numeran.

Convencion para este proyecto:

| Archivo | Contenido | Responsable |
|---|---|---|
| `01-schema.sql` | DDL traducido del legacy MySQL a PostgreSQL 16 (tablas, PK/FK, indices, CHECK) | @analista |
| `02-view.sql` | Vista `v_matriculas_detalle` (equivalente al JOIN del legacy) | @analista |
| `03-seed.sql` | Datos de prueba: 1 admin, 12 estudiantes, 7 cursos, 24 matriculas | @analista |

Notas:
- `legacy/script.sql.txt` es MySQL (ENGINE=InnoDB, TINYINT(1), backticks): **no** se copia aqui,
  hay que traducirlo. El modelo de datos y los datos semilla sirven tal cual.
- Para volver a ejecutar los scripts hay que recrear el volumen:
  `docker compose down -v && docker compose up -d db` (borra datos locales).
- Este README no lo ejecuta PostgreSQL (solo toma `*.sql`, `*.sql.gz`, `*.sh`).
