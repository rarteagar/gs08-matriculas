-- ============================================================
-- GS08 - Matriculas y Notas | verificar_notas.sql
-- Verificacion de 04-notas.sql (T1.5): tabla notas, v_notas_detalle, RN-14,
-- RN-15 y RN-16, con las 3 pruebas negativas que pide T1.5 y el calculo de
-- la boleta (C-27 / C-28) con datos reales.
-- Autor: @analista | Sprint 1
--
--   docker exec -i gs08-analista-verif psql -U gs08 -d gs08_matriculas \
--     -v ON_ERROR_STOP=1 -f - < db/verificacion/verificar_notas.sql
--
-- Todo lo que inserta va dentro de transacciones que terminan en ROLLBACK.
-- ============================================================

\pset border 2
SET client_min_messages = notice;

CREATE TABLE pg_temp.resultados (valor text);

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
                RAISE EXCEPTION 'FALLA >> % : la base NO la rechazo', msg;
            ELSE
                RAISE EXCEPTION 'FALLA >> % : rechazada con SQLSTATE % (se esperaba %)', msg, codigo, esperado;
            END IF;
    END;
END $$;

-- ============================================================
-- 1. Objetos y restricciones de 04-notas.sql
-- ============================================================
SELECT pg_temp.check(
    (SELECT count(*) FROM pg_tables WHERE schemaname='public' AND tablename='notas') = 1,
    '04-notas.sql: existe la tabla notas');

SELECT pg_temp.check(
    (SELECT count(*) FROM pg_views WHERE schemaname='public' AND viewname='v_notas_detalle') = 1,
    '04-notas.sql: existe la vista v_notas_detalle');

SELECT pg_temp.check(
    (SELECT string_agg(column_name, ',' ORDER BY column_name) FROM information_schema.columns
      WHERE table_schema='public' AND table_name='notas')
      = 'creado_en,fecha_registro,id,matricula_id,nota,numero,observacion,tipo',
    '04-notas.sql: notas tiene sus 8 columnas');

SELECT pg_temp.check(
    (SELECT count(*) FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid
      WHERE c.contype='c' AND t.relname='notas') = 3,
    '04-notas.sql: 3 CHECK en notas (tipo, rango de la nota, numero >= 1)');

SELECT pg_temp.check(
    (SELECT count(*) FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid
      WHERE c.contype='u' AND t.relname='notas') = 1,
    '04-notas.sql: UNIQUE (matricula_id, tipo, numero)');

SELECT pg_temp.check(
    (SELECT confdeltype FROM pg_constraint WHERE conname='fk_notas_matricula') = 'c',
    '04-notas.sql: fk_notas_matricula con ON DELETE CASCADE (C-29)');

SELECT pg_temp.check(
    (SELECT count(*) FROM pg_trigger WHERE tgname='tr_notas_matricula_activa' AND NOT tgisinternal) = 1,
    '04-notas.sql: existe el trigger RN-14 (no se califica matricula retirada)');

SELECT pg_temp.check(
    (SELECT count(*) FROM pg_indexes WHERE schemaname='public' AND tablename='notas'
       AND indexname IN ('idx_notas_matricula','idx_notas_orden')) = 2,
    '04-notas.sql: los 2 indices de notas');

-- ============================================================
-- 2. Pruebas negativas (T1.5 pide 3: nota=21, duplicado y matricula retirada)
--    Todas rechazadas por la base; nada queda insertado.
-- ============================================================
SELECT pg_temp.check_error(
    $q$INSERT INTO notas (matricula_id, tipo, numero, nota) VALUES (1, 'practica', 1, 21)$q$,
    '23514',
    'RN-16 (T1.5): nota=21 -> check_violation (rango 0..20)');

SELECT pg_temp.check_error(
    $q$INSERT INTO notas (matricula_id, tipo, numero, nota) VALUES (1, 'practica', 1, -1)$q$,
    '23514',
    'RN-16: nota=-1 -> check_violation');

SELECT pg_temp.check_error(
    $q$INSERT INTO notas (matricula_id, tipo, numero, nota) VALUES (1, 'examen', 1, 15)$q$,
    '23514',
    'RN-16: tipo="examen" -> check_violation (solo practica|parcial|final)');

SELECT pg_temp.check_error(
    $q$INSERT INTO notas (matricula_id, tipo, numero, nota) VALUES (1, 'practica', 0, 15)$q$,
    '23514',
    'RN-16: numero=0 -> check_violation');

-- Duplicado: primero una nota real dentro de una transaccion, luego el mismo trio
BEGIN;
INSERT INTO notas (matricula_id, tipo, numero, nota) VALUES (1, 'practica', 1, 14);
SELECT pg_temp.check_error(
    $q$INSERT INTO notas (matricula_id, tipo, numero, nota) VALUES (1, 'practica', 1, 18)$q$,
    '23505',
    'RN-16 (T1.5): duplicado (matricula_id, tipo, numero) -> unique_violation (409 en la API)');
ROLLBACK;

-- RN-14: la matricula 13 del seed es la unica retirada (estudiante 7, curso 4)
SELECT pg_temp.check(
    (SELECT estado FROM matriculas WHERE id = 13) = 'retirado',
    'precondicion RN-14: la matricula 13 del seed esta retirada');

SELECT pg_temp.check_error(
    $q$INSERT INTO notas (matricula_id, tipo, numero, nota) VALUES (13, 'parcial', 1, 15)$q$,
    '23514',
    'RN-14 (T1.5): nota sobre matricula retirada -> check_violation (409 en la API)');

SELECT pg_temp.check_error(
    $q$INSERT INTO notas (matricula_id, tipo, numero, nota) VALUES (999, 'practica', 1, 15)$q$,
    '23503',
    'nota de una matricula inexistente -> foreign_key_violation');

-- ============================================================
-- 3. Bordes que SI deben entrar (0, 20 y redondeo a 2 decimales)
-- ============================================================
BEGIN;
INSERT INTO notas (matricula_id, tipo, numero, nota) VALUES (1, 'final', 2, 0);
INSERT INTO notas (matricula_id, tipo, numero, nota) VALUES (1, 'final', 3, 20);
INSERT INTO notas (matricula_id, tipo, numero, nota) VALUES (1, 'final', 4, 16.005);
SELECT pg_temp.check(
    (SELECT count(*) FROM notas WHERE matricula_id = 1) = 3,
    'RN-16: la nota 0 y la nota 20 se aceptan (bordes del rango)');
SELECT pg_temp.check(
    (SELECT nota FROM notas WHERE matricula_id = 1 AND numero = 4) = 16.01,
    'RN-16: numeric(4,2) redondea 16.005 -> 16.01 (documentado, no silencioso)');
ROLLBACK;

-- ============================================================
-- 4. RN-15: media del curso y promedio del periodo (C-27, C-28)
--    Datos de prueba: el estudiante 1 tiene las matriculas 1 (C101, 4 cr)
--    y 2 (C102, 3 cr); se agrega una tercera (C201, 4 cr) SIN notas.
-- ============================================================
BEGIN;

INSERT INTO matriculas (estudiante_id, curso_id, periodo, fecha_matricula)
VALUES (1, 3, '2026-02', '2026-08-18');

INSERT INTO notas (matricula_id, tipo, numero, nota) VALUES
    (1, 'practica', 1, 14), (1, 'parcial', 1, 16), (1, 'final', 1, 18),
    (2, 'practica', 1, 11);

-- Nota del curso = media aritmetica de sus notas, 2 decimales (14, 16, 18 -> 16.00)
SELECT pg_temp.check(
    (SELECT round(avg(n.nota), 2) FROM notas n WHERE n.matricula_id = 1) = 16.00,
    'RN-15: nota del curso C101 = media aritmetica de 14, 16 y 18 -> 16.00');

-- Boleta (C-28): una fila por curso, el curso sin notas sale con null
SELECT pg_temp.check(
    (SELECT count(*) FROM (
        SELECT m.id, round(avg(n.nota), 2) AS nota_curso
        FROM matriculas m
        JOIN cursos c      ON c.id = m.curso_id
        LEFT JOIN notas n  ON n.matricula_id = m.id
        WHERE m.estudiante_id = 1 AND m.periodo = '2026-02'
        GROUP BY m.id) s) = 3,
    'C-28: la boleta del estudiante 1 en 2026-02 tiene 3 cursos (sus 3 matriculas)');

SELECT pg_temp.check(
    (SELECT count(*) FROM (
        SELECT m.id, round(avg(n.nota), 2) AS nota_curso
        FROM matriculas m
        JOIN cursos c      ON c.id = m.curso_id
        LEFT JOIN notas n  ON n.matricula_id = m.id
        WHERE m.estudiante_id = 1 AND m.periodo = '2026-02'
        GROUP BY m.id) s
     WHERE nota_curso IS NULL) = 1,
    'C-28: el curso sin notas sale con nota null (no 0, y no entra al promedio)');

-- Promedio del periodo = media ponderada por creditos de los cursos CON notas
-- (16.00 * 4 + 11.00 * 3) / 7 = 13.857 -> 13.86
SELECT pg_temp.check(
    (SELECT round(sum(nota_curso * creditos) / sum(creditos), 2) FROM (
        SELECT m.id, c.creditos, round(avg(n.nota), 2) AS nota_curso
        FROM matriculas m
        JOIN cursos c      ON c.id = m.curso_id
        JOIN notas n       ON n.matricula_id = m.id
        WHERE m.estudiante_id = 1 AND m.periodo = '2026-02'
        GROUP BY m.id, c.creditos) s) = 13.86,
    'RN-15: promedio del periodo (ponderado por creditos: 16x4 + 11x3 sobre 7) -> 13.86');

-- La misma cuenta sin ponderar daria 13.50: se comprueba que NO es eso
SELECT pg_temp.check(
    (SELECT round(avg(nota_curso), 2) FROM (
        SELECT m.id, round(avg(n.nota), 2) AS nota_curso
        FROM matriculas m
        JOIN cursos c      ON c.id = m.curso_id
        JOIN notas n       ON n.matricula_id = m.id
        WHERE m.estudiante_id = 1 AND m.periodo = '2026-02'
        GROUP BY m.id) s) = 13.50,
    'RN-15: se distingue del promedio simple (13.50): el ponderado por creditos es 13.86');

-- ============================================================
-- 5. v_notas_detalle y las reglas de borrado (C-29)
-- ============================================================
SELECT pg_temp.check(
    (SELECT count(*) FROM v_notas_detalle WHERE matricula_id = 1) = 3,
    'v_notas_detalle: las 3 notas de la matricula 1 con estudiante y curso');

SELECT pg_temp.check(
    (SELECT estudiante FROM v_notas_detalle WHERE matricula_id = 1 LIMIT 1)
      = 'Ramírez Torres, Carlos Alberto',
    'v_notas_detalle: trae el estudiante con el formato "apellidos, nombres"');

SELECT pg_temp.check(
    (SELECT curso FROM v_notas_detalle WHERE matricula_id = 1 LIMIT 1) = 'Matemática Básica',
    'v_notas_detalle: trae el nombre del curso y su periodo');

-- Retirar la matricula NO borra las notas ya registradas (D-06)
UPDATE matriculas SET estado = 'retirado' WHERE id = 2;
SELECT pg_temp.check(
    (SELECT count(*) FROM notas WHERE matricula_id = 2) = 1,
    'RN-14/D-06: retirar la matricula conserva las notas ya registradas');

-- Borrar la matricula SI borra sus notas (cascada, C-29)
DELETE FROM matriculas WHERE id = 1;
SELECT pg_temp.check(
    (SELECT count(*) FROM notas WHERE matricula_id = 1) = 0,
    'C-29: borrar la matricula borra sus notas por cascada');

-- Y borrar al estudiante borra sus matriculas y sus notas
DELETE FROM estudiantes WHERE id = 1;
SELECT pg_temp.check(
    (SELECT count(*) FROM notas n JOIN matriculas m ON m.id = n.matricula_id
      WHERE m.estudiante_id = 1) = 0,
    'C-29: borrar el estudiante borra sus matriculas y sus notas (cascada en dos saltos)');

ROLLBACK;

-- ============================================================
-- 6. Intactos despues del ROLLBACK
-- ============================================================
SELECT pg_temp.check((SELECT count(*) FROM notas) = 0,      'ROLLBACK: la tabla notas quedo vacia (no se dejo basura)');
SELECT pg_temp.check((SELECT count(*) FROM matriculas) = 24, 'ROLLBACK: las 24 matriculas del seed siguen ahi');
SELECT pg_temp.check(
    (SELECT estado FROM matriculas WHERE id = 13) = 'retirado',
    'ROLLBACK: la unica matricula retirada del seed sigue siendo la 13');

-- ============================================================
-- Resumen (las comprobaciones dentro de las transacciones no quedan en la tabla)
-- ============================================================
SELECT count(*) AS comprobaciones_ok_fuera_de_la_transaccion FROM pg_temp.resultados;
