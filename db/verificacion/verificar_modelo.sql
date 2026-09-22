-- ============================================================
-- GS08 - Matriculas y Notas | verificar_modelo.sql
-- Consulta de verificacion de 01-schema.sql, 02-view.sql y 03-seed.sql
-- Autor: @analista | Sprint 0
--
-- Como se corre (base con el esquema ya cargado):
--   docker exec -i gs08-analista-verif psql -U postgres -d gs08_matriculas \
--     -v ON_ERROR_STOP=1 -f - < db/verificacion/verificar_modelo.sql
--
-- Salida esperada: una linea "OK >> ..." por comprobacion y el resumen final
-- en "comprobaciones_ok". Cualquier falla aborta con "FALLA >> ..." y psql
-- termina con codigo distinto de cero (por eso -v ON_ERROR_STOP=1).
--
-- Incluye pruebas negativas: se intenta violar cada regla de negocio y se
-- exige que la BASE la rechace (SQLSTATE 23505 unico, 23514 check, 23503 FK).
-- Todo lo que inserta/borra va dentro de una transaccion que termina en ROLLBACK.
-- ============================================================

\pset border 2
SET client_min_messages = notice;

-- ------------------------------------------------------------
-- Utilidades de verificacion
-- ------------------------------------------------------------
CREATE FUNCTION pg_temp.check(ok boolean, msg text) RETURNS text
LANGUAGE plpgsql AS $$
BEGIN
    IF NOT ok THEN
        RAISE EXCEPTION 'FALLA >> %', msg;
    END IF;
    INSERT INTO pg_temp.resultados(valor) VALUES (msg);
    RAISE NOTICE 'OK   >> %', msg;
    RETURN msg;
END $$;

CREATE TABLE pg_temp.resultados (valor text);

CREATE FUNCTION pg_temp.check_error(sql text, esperado text, msg text) RETURNS text
LANGUAGE plpgsql AS $$
DECLARE codigo text;
BEGIN
    BEGIN
        EXECUTE sql;
        RAISE EXCEPTION 'FALLA >> % : la sentencia fue aceptada', msg;
    EXCEPTION
        WHEN OTHERS THEN
            GET STACKED DIAGNOSTICS codigo = RETURNED_SQLSTATE;
            IF codigo = esperado THEN
                INSERT INTO pg_temp.resultados(valor) VALUES (msg);
                RAISE NOTICE 'OK   >> %  (rechazado, SQLSTATE %)', msg, codigo;
                RETURN msg;
            ELSIF codigo = 'P0001' THEN
                RAISE EXCEPTION 'FALLA >> % : la base NO la rechazo (falta la restriccion)', msg;
            ELSE
                RAISE EXCEPTION 'FALLA >> % : rechazada con SQLSTATE % (se esperaba %)', msg, codigo, esperado;
            END IF;
    END;
END $$;

-- ============================================================
-- 1. Objetos creados
-- ============================================================
SELECT pg_temp.check(
    (SELECT string_agg(tablename, ',' ORDER BY tablename) FROM pg_tables WHERE schemaname = 'public')
      = 'cursos,estudiantes,matriculas,notas,usuarios',
    '01-schema.sql + 04-notas.sql: estan las 5 tablas (las 4 del legacy + notas)');

SELECT pg_temp.check(
    (SELECT count(*) FROM pg_views WHERE schemaname = 'public' AND viewname = 'v_matriculas_detalle') = 1,
    '02-view.sql: existe la vista v_matriculas_detalle');

SELECT pg_temp.check(
    (SELECT string_agg(column_name, ',' ORDER BY column_name)
       FROM information_schema.columns
      WHERE table_schema = 'public' AND table_name = 'matriculas')
      = 'creado_en,curso_id,estado,estudiante_id,fecha_matricula,id,periodo',
    '01-schema.sql: matriculas tiene sus 7 columnas (las 6 del legacy + creado_en)');

-- ============================================================
-- 2. Restricciones declaradas (el contrato del modelo)
-- ============================================================
SELECT pg_temp.check(
    (SELECT count(*) FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid
      WHERE c.contype = 'c' AND t.relname IN ('usuarios','estudiantes','cursos','matriculas')) = 16,
    '01-schema.sql: 16 CHECK declarados (4 usuarios, 6 estudiantes, 4 cursos, 2 matriculas)');

SELECT pg_temp.check(
    (SELECT count(*) FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid
      WHERE c.contype = 'u' AND t.relname IN ('usuarios','estudiantes','cursos','matriculas')) = 6,
    '01-schema.sql: 6 UNIQUE (codigo/dni/email/nombre_usuario + uq_matriculas_estudiante_curso_periodo)');

SELECT pg_temp.check(
    (SELECT count(*) FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid
      WHERE c.contype = 'f' AND t.relname IN ('usuarios','estudiantes','cursos','matriculas')) = 2,
    '01-schema.sql: 2 FK en el esquema base (matriculas -> estudiantes y matriculas -> cursos)');

SELECT pg_temp.check(
    (SELECT confdeltype FROM pg_constraint WHERE conname = 'fk_matriculas_curso') = 'c',
    '01-schema.sql: fk_matriculas_curso es ON DELETE CASCADE (igual que el legacy)');

-- Indices que en MySQL los creaba la FK y en PostgreSQL hay que declarar
SELECT pg_temp.check(
    (SELECT count(*) FROM pg_indexes WHERE schemaname='public' AND tablename='matriculas'
       AND indexname IN ('idx_matriculas_estudiante','idx_matriculas_curso')) = 2,
    '01-schema.sql: existen los indices de las FK de matriculas (MySQL los creaba solo, PostgreSQL no)');

-- ============================================================
-- 3. Datos del seed
-- ============================================================
SELECT pg_temp.check((SELECT count(*) FROM usuarios)    = 1,  '03-seed.sql: 1 usuario (admin)');
SELECT pg_temp.check((SELECT count(*) FROM estudiantes) = 12, '03-seed.sql: 12 estudiantes');
SELECT pg_temp.check((SELECT count(*) FROM cursos)      = 7,  '03-seed.sql: 7 cursos');
SELECT pg_temp.check((SELECT count(*) FROM matriculas)  = 24, '03-seed.sql: 24 matriculas');
SELECT pg_temp.check(
    (SELECT count(*) FROM matriculas WHERE estado = 'retirado') = 1,
    '03-seed.sql: 1 matricula retirada (estudiante 7 / curso 4) y 23 activas');
SELECT pg_temp.check(
    (SELECT apellidos || ' / ' || estudiantes.nombres FROM estudiantes WHERE id = 1)
      = 'Ramírez Torres / Carlos Alberto',
    '03-seed.sql: los acentos se cargaron intactos (UTF-8 de punta a punta)');
SELECT pg_temp.check(
    (SELECT count(*) FROM estudiantes WHERE apellidos ~ '[áéíóúÁÉÍÓÚ]') = 6,
    '03-seed.sql: los 6 apellidos acentuados del legacy llegaron completos');

-- ============================================================
-- 4. Vista v_matriculas_detalle
-- ============================================================
SELECT pg_temp.check(
    (SELECT count(*) FROM v_matriculas_detalle) = 24,
    '02-view.sql: la vista devuelve las 24 matriculas (JOIN completo, sin perdidas)');

SELECT pg_temp.check(
    (SELECT estudiante FROM v_matriculas_detalle WHERE matricula_id = 1)
      = 'Ramírez Torres, Carlos Alberto',
    '02-view.sql: la vista arma "apellidos, nombres" igual que el legacy');

SELECT pg_temp.check(
    (SELECT count(*) FROM v_matriculas_detalle
      WHERE estado_matricula = 'activa' AND creditos IS NOT NULL) = 23,
    '02-view.sql: las 23 activas traen creditos del curso (dato que usa el listado)');

-- ============================================================
-- 5. Numeros del dashboard del legacy (paridad de consultas)
-- ============================================================
SELECT pg_temp.check((SELECT count(*) FROM estudiantes WHERE estado) = 12, 'dashboard: 12 estudiantes activos');
SELECT pg_temp.check((SELECT count(*) FROM cursos      WHERE estado) = 7,  'dashboard: 7 cursos activos');
SELECT pg_temp.check(
    (SELECT count(*) FROM matriculas WHERE estado = 'activa') = 23,
    'dashboard: 23 matriculas activas');
SELECT pg_temp.check((SELECT count(*) FROM usuarios WHERE estado) = 1, 'dashboard: 1 usuario activo');
SELECT pg_temp.check(
    (SELECT sum(total) FROM (SELECT count(*) AS total FROM v_matriculas_detalle
                              WHERE estado_matricula = 'activa' GROUP BY curso) s) = 23,
    'dashboard: el agrupado por curso suma 23 (mismo total que el KPI)');

-- ============================================================
-- 6. Consultas del API (buscador y filtro de periodo del listado legacy)
-- ============================================================
-- OJO, hallazgo con impacto en el API: en MySQL el LIKE del legacy era insensible a
-- mayusculas (collation utf8mb4_unicode_ci). En PostgreSQL LIKE SI distingue mayusculas
-- (y tambien acentos): la misma consulta devuelve 0 filas. El API debe usar ILIKE.
SELECT pg_temp.check(
    (SELECT count(*) FROM v_matriculas_detalle
      WHERE estudiante LIKE '%quispe%' OR curso LIKE '%quispe%'
         OR codigo_estudiante LIKE '%quispe%' OR codigo_curso LIKE '%quispe%') = 0,
    'trampa MySQL->PostgreSQL: LIKE %quispe% devuelve 0 (el legacy devolvia 2 por la collation _ci)');

SELECT pg_temp.check(
    (SELECT count(*) FROM v_matriculas_detalle
      WHERE estudiante ILIKE '%quispe%' OR curso ILIKE '%quispe%'
         OR codigo_estudiante ILIKE '%quispe%' OR codigo_curso ILIKE '%quispe%') = 2,
    'buscador del listado con ILIKE (q=quispe): las 2 matriculas del legacy');

-- ILIKE ignora mayusculas pero NO tildes: el criterio C-08 no se cumple sin unaccent.
-- (BUG-07 de @qa: medido sobre el seed, en el endpoint de estudiantes)
SELECT pg_temp.check(
    (SELECT count(*) FROM estudiantes WHERE apellidos ILIKE '%huaman%') = 0
    AND (SELECT count(*) FROM estudiantes WHERE apellidos ILIKE '%Huamán%') = 1,
    'BUG-07: sin unaccent, q=huaman da 0 y q=Huamán da 1 (ILIKE no quita tildes)');

SELECT pg_temp.check(
    (SELECT count(*) FROM pg_extension WHERE extname = 'unaccent') = 1,
    '01-schema.sql: la extension unaccent esta instalada (requisito de C-08)');

-- C-08 con unaccent: las tres variantes devuelven la misma cantidad (y no cero).
SELECT pg_temp.check(
    (SELECT count(DISTINCT s.n)
       FROM (VALUES ('huaman'), ('Huamán'), ('HUAMAN')) AS q(texto),
            LATERAL (SELECT count(*) AS n FROM estudiantes
                      WHERE unaccent(apellidos || ' ' || nombres) ILIKE unaccent('%' || q.texto || '%')) s) = 1
    AND (SELECT count(*) FROM estudiantes
          WHERE unaccent(apellidos || ' ' || nombres) ILIKE unaccent('%huaman%')) >= 1,
    'C-08 (estudiantes): huaman / Huamán / HUAMAN devuelven la MISMA cantidad de filas');

-- Precision de endpoints (precision de @qa en la sala): el mismo q no da lo mismo
-- en /estudiantes que en /matriculas, porque uno cuenta estudiantes y el otro matriculas.
SELECT pg_temp.check(
    (SELECT count(*) FROM estudiantes
      WHERE unaccent(apellidos || ' ' || nombres) ILIKE unaccent('%huaman%')) = 1,
    'C-08 endpoint /estudiantes con q=huaman: 1 fila (Quispe Huamán)');

SELECT pg_temp.check(
    (SELECT count(*) FROM v_matriculas_detalle
      WHERE unaccent(estudiante) ILIKE unaccent('%huaman%')) = 2,
    'C-08 endpoint /matriculas con q=huaman: 2 filas (las 2 matriculas de Quispe Huamán)');
SELECT pg_temp.check(
    (SELECT count(*) FROM v_matriculas_detalle WHERE periodo = '2026-02') = 24,
    'filtro de periodo (2026-02): 24 filas');
SELECT pg_temp.check(
    (SELECT count(DISTINCT periodo) FROM matriculas) = 1,
    'selectores de periodo del SPA: 1 periodo distinto en el seed');

-- ============================================================
-- 7. Reglas de negocio: la base tiene que rechazar lo invalido
-- ============================================================
SELECT pg_temp.check_error(
    $q$INSERT INTO matriculas (estudiante_id, curso_id, periodo, fecha_matricula)
       VALUES (1, 1, '2026-02', '2026-08-20')$q$,
    '23505',
    'RN-08: estudiante 1 ya matriculado en curso 1 / 2026-02 -> unique_violation');

SELECT pg_temp.check_error(
    $q$INSERT INTO matriculas (estudiante_id, curso_id, periodo, fecha_matricula)
       VALUES (1, 7, '2026-13', '2026-08-20')$q$,
    '23514',
    'RN-06: periodo 2026-13 (mes inexistente) -> check_violation');

SELECT pg_temp.check_error(
    $q$INSERT INTO matriculas (estudiante_id, curso_id, periodo, fecha_matricula)
       VALUES (1, 7, '2026/02', '2026-08-20')$q$,
    '23514',
    'RN-06: periodo 2026/02 (formato no AAAA-MM) -> check_violation');

SELECT pg_temp.check_error(
    $q$INSERT INTO matriculas (estudiante_id, curso_id, periodo, fecha_matricula, estado)
       VALUES (1, 7, '2026-02', '2026-08-20', 'anulada')$q$,
    '23514',
    'RN-07: estado de matricula fuera de activa/retirado -> check_violation');

SELECT pg_temp.check_error(
    $q$INSERT INTO matriculas (estudiante_id, curso_id, periodo, fecha_matricula)
       VALUES (999, 7, '2026-02', '2026-08-20')$q$,
    '23503',
    'RN-09: matricula de un estudiante inexistente -> foreign_key_violation');

SELECT pg_temp.check_error(
    $q$INSERT INTO estudiantes (codigo, dni, nombres, apellidos) VALUES ('E20260099','1234567','Prueba','Uno')$q$,
    '23514',
    'RN-04: DNI de 7 digitos -> check_violation');

SELECT pg_temp.check_error(
    $q$INSERT INTO estudiantes (codigo, dni, nombres, apellidos) VALUES ('E20260099','45123456','Prueba','Uno')$q$,
    '23505',
    'RN-04: DNI repetido -> unique_violation');

SELECT pg_temp.check_error(
    $q$INSERT INTO estudiantes (codigo, dni, nombres, apellidos) VALUES ('E20260001','70000001','Prueba','Uno')$q$,
    '23505',
    'RN-03: codigo de estudiante repetido -> unique_violation');

SELECT pg_temp.check_error(
    $q$INSERT INTO estudiantes (codigo, dni, nombres, apellidos, email)
       VALUES ('E20260099','70000001','Prueba','Uno','correo-sin-arroba')$q$,
    '23514',
    'RN-05: correo con formato invalido -> check_violation');

SELECT pg_temp.check_error(
    $q$INSERT INTO cursos (codigo, nombre, creditos, horas) VALUES ('C999','Curso malo', 0, 48)$q$,
    '23514',
    'RN-02: creditos 0 (fuera de 1..10) -> check_violation');

SELECT pg_temp.check_error(
    $q$INSERT INTO cursos (codigo, nombre, creditos, horas) VALUES ('C999','Curso malo', 11, 48)$q$,
    '23514',
    'RN-02: creditos 11 (fuera de 1..10) -> check_violation');

SELECT pg_temp.check_error(
    $q$INSERT INTO cursos (codigo, nombre, creditos, horas) VALUES ('C999','Curso malo', 3, 0)$q$,
    '23514',
    'RN-02: horas 0 -> check_violation');

SELECT pg_temp.check_error(
    $q$INSERT INTO usuarios (nombre_usuario, email, password_hash, nombre_completo, rol)
       VALUES ('ab', 'x@y.pe', 'hash', 'Prueba', 'admin')$q$,
    '23514',
    'RN-01: nombre de usuario de 2 caracteres -> check_violation');

SELECT pg_temp.check_error(
    $q$INSERT INTO usuarios (nombre_usuario, email, password_hash, nombre_completo, rol)
       VALUES ('jperez', 'x@y.pe', 'hash', 'Prueba', 'superadmin')$q$,
    '23514',
    'RN-01: rol distinto de admin/asistente -> check_violation');

SELECT pg_temp.check_error(
    $q$INSERT INTO usuarios (nombre_usuario, email, password_hash, nombre_completo)
       VALUES ('admin', 'otro@horizonte.edu.pe', 'hash', 'Prueba')$q$,
    '23505',
    'RN-01: nombre de usuario repetido -> unique_violation');

-- ============================================================
-- 8. Comportamiento transaccional: cascada y secuencias IDENTITY
--    (todo dentro de una transaccion que termina en ROLLBACK)
-- ============================================================
BEGIN;

-- Borrar un curso debe arrastrar sus matriculas (ON DELETE CASCADE del legacy)
CREATE TEMP TABLE antes AS SELECT count(*) AS n FROM matriculas WHERE curso_id = 5;
DELETE FROM cursos WHERE id = 5;
SELECT pg_temp.check(
    (SELECT count(*) FROM matriculas WHERE curso_id = 5) = 0
      AND (SELECT n FROM antes) = 3,
    'RN-10: eliminar el curso 5 borro sus 3 matriculas por cascada');

-- Y al reves: borrar un estudiante arrastra las suyas
DELETE FROM estudiantes WHERE id = 2;
SELECT pg_temp.check(
    (SELECT count(*) FROM matriculas WHERE estudiante_id = 2) = 0,
    'RN-10: eliminar el estudiante 2 borro sus 2 matriculas por cascada');

-- La secuencia sigue despues del seed con ids explicitos (setval de 03-seed.sql).
-- Se exige id >= 13 y no = 13 a proposito: nextval NO se revierte con el ROLLBACK,
-- asi que al re-ejecutar esta verificacion sobre la misma base el id avanza.
CREATE TEMP TABLE nuevo AS
  WITH t AS (INSERT INTO estudiantes (codigo, dni, nombres, apellidos)
             VALUES ('E20260013', '60000013', 'Alumno', 'Nuevo') RETURNING id)
  SELECT id FROM t;
SELECT pg_temp.check(
    (SELECT id FROM nuevo) >= 13,
    '03-seed.sql: la secuencia quedo por encima del max(id) del seed (el INSERT no choca con la PK)');

CREATE TEMP TABLE nuevo_curso AS
  WITH t AS (INSERT INTO cursos (codigo, nombre, creditos)
             VALUES ('C206', 'Curso Nuevo', 3) RETURNING id)
  SELECT id FROM t;
SELECT pg_temp.check(
    (SELECT id FROM nuevo_curso) >= 8,
    '03-seed.sql: la secuencia de cursos continua por encima de 7 (ids con huecos: los INSERT rechazados tambien consumen el nextval)');

ROLLBACK;

-- ============================================================
-- 9. Vista y datos intactos despues del ROLLBACK
-- ============================================================
SELECT pg_temp.check((SELECT count(*) FROM matriculas) = 24, 'ROLLBACK: las 24 matriculas siguen ahi');
SELECT pg_temp.check((SELECT count(*) FROM cursos)     = 7,  'ROLLBACK: los 7 cursos siguen ahi');
SELECT pg_temp.check((SELECT count(*) FROM estudiantes) = 12, 'ROLLBACK: los 12 estudiantes siguen ahi');

-- ============================================================
-- Resumen
-- OJO al leer este numero: las comprobaciones de la seccion 8 corren dentro de una
-- transaccion que termina en ROLLBACK, asi que sus resultados NO quedan en la tabla.
-- El total real es el de las lineas "NOTICE:  OK   >>" de toda la salida.
-- ============================================================
SELECT count(*) AS comprobaciones_ok_fuera_de_la_transaccion FROM pg_temp.resultados;
