# GS08 · Datos del seed — valores oficiales para citar en documentos y pruebas

**Autor:** @analista · **Fecha:** 21/09/2026 · **Fuente:** `db/init/03-seed.sql` ejecutado en PostgreSQL
16.15, consultado con `psql` (no de memoria).

Sirve para una sola cosa: que ningún documento, criterio de aceptación o caso de prueba cite un dato que
no existe. Si un criterio dice otro correo, otro DNI u otro conteo, **el criterio está mal, no el seed**.

## Credenciales y conteos

| Dato | Valor real | Salida de la consulta |
|---|---|---|
| Usuario admin | `admin` / `Admin123!` | `select nombre_usuario, email, rol from usuarios;` → `admin \| admin@horizonte.edu.pe \| admin` |
| Estudiantes | 12 (todos activos) | `select count(*) from estudiantes;` → 12 |
| Cursos | 7 (todos activos) | `select count(*) from cursos;` → 7 |
| Matrículas | 24 = **23 activas + 1 retirada** | `select count(*) , count(*) filter (where estado='activa') , count(*) filter (where estado='retirado') from matriculas;` → 24 / 23 / 24 − 23 |
| La única retirada | matrícula id 13: estudiante 7 (Castillo Neyra, Jorge Luis) en curso 4 (C202 Base de Datos II), periodo 2026-02 | — |
| Periodo del seed | `2026-02` (uno solo) | `select distinct periodo from matriculas;` → 1 fila |
| KPI del dashboard | estudiantes activos 12 · cursos activos 7 · matrículas activas 23 · usuarios activos 1 | las 4 consultas de `dashboard.php` traducidas |

## Estudiantes del seed (código / DNI) — para ejemplos y casos de prueba

```
 id |  codigo   |   dni    |            estudiante
----+-----------+----------+----------------------------------
  1 | E20260001 | 45123456 | Ramírez Torres, Carlos Alberto
  2 | E20260002 | 46234567 | Quispe Huamán, María Fernanda
  3 | E20260003 | 47345678 | Gutiérrez Salas, Luis Enrique
  4 | E20260004 | 48456789 | Vargas Mendoza, Ana Lucía
  5 | E20260005 | 49567890 | Flores Chávez, Diego Antonio
  6 | E20260006 | 50678901 | Paredes Rojas, Valeria Sofía
  7 | E20260007 | 51789012 | Castillo Neyra, Jorge Luis
  8 | E20260008 | 52890123 | Ríos Delgado, Camila Andrea
  9 | E20260009 | 53901234 | Herrera Palacios, Miguel Ángel
 10 | E20260010 | 54012345 | Torres Vega, Nicole Alessandra
 11 | E20260011 | 55123456 | Salazar Meza, Renato Gabriel
 12 | E20260012 | 56234567 | Cárdenas Ruiz, Fiorella Milagros
```

**Ejemplos correctos para pegar en los documentos:**

| Se quiere mostrar | Usar | Por qué |
|---|---|---|
| Buscar por DNI | `?q=45123456` (Carlos Alberto Ramírez Torres) | **`12345678` no existe** en el seed |
| Buscar por código | `?q=E20260001` | existe y devuelve 1 fila |
| Buscar sin tildes (RN del buscador / C-08) | `?q=huaman`, `?q=Huamán`, `?q=HUAMAN` | las tres deben devolver **la misma cantidad**, y depende del endpoint: **`/api/v1/estudiantes` → 1 fila** (el estudiante 2) y **`/api/v1/matriculas` → 2 filas** (sus 2 matrículas). Precisión de @qa en la sala: el mismo `q` no da lo mismo en un endpoint que en el otro |
| Duplicado para el `409` | estudiante 1 + curso 1 + `2026-02` | choca con `uq_matriculas_estudiante_curso_periodo` |
| Borrado con cascada (T2.3) | curso 5 → **3** matrículas · estudiante 2 → **2** matrículas | conteos verificados |
| Correo del sistema | `admin@horizonte.edu.pe` | el instituto del legacy se llama «Instituto Privado Horizonte»; **no** existe `admin@institucion.edu.pe` |

## Cursos del seed

`C101` Matemática Básica (4 cr.) · `C102` Comunicación Efectiva (3) · `C201` Programación Web III (4) ·
`C202` Base de Datos II (3) · `C203` Inglés Técnico (2) · `C204` Estadística Aplicada (3) ·
`C205` Fundamentos de Administración (3)

Matrículas activas por curso: C101 → 5 · C102 → 4 · C201 → 4 · C203 → 3 · C204 → 3 · C202 → 2 · C205 → 2
(suma 23, el mismo total del KPI).

## Cómo se comprueba (no es de memoria)

```bash
bash db/verificacion/ejecutar_verificacion.sh          # 54 + 2 + 32 comprobaciones, exit 0
docker exec gs08-analista-verif psql -U gs08 -d gs08_matriculas -c "select * from estudiantes order by id;"
```

Evidencia: `docs/analisis/evidencia/verificacion-modelo.txt` (incluye los conteos del seed, los números
del dashboard y las dos cifras de `q=huaman` —1 en estudiantes, 2 en matrículas— como comprobaciones con
nombre y apellido) y `docs/analisis/evidencia/verificacion-notas.txt`.

## Nota de esquema: `unaccent` (BUG-07)

El buscador cumple `C-08` (misma cantidad con `huaman` / `Huamán` / `HUAMAN`) **solo con la extensión
`unaccent`**, que ahora se crea en `01-schema.sql` (`CREATE EXTENSION IF NOT EXISTS unaccent;`).
Sin ella e ILIKE solo: `q=huaman` → **0** filas y `q=Huamán` → **1**; medido en el endpoint de
estudiantes y fijado como comprobación de la verificación. La revisión inicial de Alembic (D-14) debe
incluir la misma línea.
