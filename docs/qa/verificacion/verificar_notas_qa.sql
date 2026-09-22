-- ============================================================
-- GS08 - Matriculas y Notas | verificar_notas_qa.sql
-- Verificacion INDEPENDIENTE de @qa sobre 04-notas.sql (T1.5).
-- No reusa el runner del autor: prueba las mismas reglas desde cero.
-- Todo corre dentro de una transaccion y termina en ROLLBACK: no deja datos.
--
--   docker exec -i gs08-analista-verif psql -U gs08 -d gs08_matriculas -f - \
--     < docs/qa/verificacion/verificar_notas_qa.sql
-- ============================================================
\pset pager off
\timing off

BEGIN;

-- 1. Nombre del trigger y de los CHECK/UNIQUE de la tabla notas (lo que existe de verdad)
SELECT 'objetos' seccion,
       (SELECT count(*) FROM pg_class WHERE relname='notas')                     AS tabla,
       (SELECT count(*) FROM pg_class WHERE relname='v_notas_detalle')            AS vista,
       (SELECT count(*) FROM pg_trigger WHERE tgname='tr_notas_matricula_activa') AS trigger_rn14,
       (SELECT count(*) FROM pg_constraint
         WHERE conrelid='notas'::regclass AND contype='u')                       AS uniques,
       (SELECT count(*) FROM pg_constraint
         WHERE conrelid='notas'::regclass AND contype='c')                       AS checks;

-- 2. Pruebas negativas: cada regla intenta violarse y se exige SQLSTATE
DO $$
DECLARE
    ok int := 0; fail int := 0; st text;
    PROCEDURE_LABEL text;
BEGIN
    -- helper local: se repite el patron porque plpgsql no tiene try/finally simple
    BEGIN
        INSERT INTO notas (matricula_id, tipo, numero, nota) VALUES (1, 'practica', 1, 21);
        RAISE NOTICE 'FALLA >> nota 21 ACEPTADA (deberia ser 23514)'; fail := fail + 1;
    EXCEPTION WHEN check_violation THEN RAISE NOTICE 'OK    >> nota 21 rechazada (SQLSTATE %)', SQLSTATE; ok := ok + 1;
    END;

    BEGIN
        INSERT INTO notas (matricula_id, tipo, numero, nota) VALUES (1, 'practica', 2, -1);
        RAISE NOTICE 'FALLA >> nota -1 ACEPTADA'; fail := fail + 1;
    EXCEPTION WHEN check_violation THEN RAISE NOTICE 'OK    >> nota -1 rechazada (SQLSTATE %)', SQLSTATE; ok := ok + 1;
    END;

    BEGIN
        INSERT INTO notas (matricula_id, tipo, numero, nota) VALUES (1, 'examen', 1, 15);
        RAISE NOTICE 'FALLA >> tipo examen ACEPTADO'; fail := fail + 1;
    EXCEPTION WHEN check_violation THEN RAISE NOTICE 'OK    >> tipo examen rechazado (SQLSTATE %)', SQLSTATE; ok := ok + 1;
    END;

    BEGIN
        INSERT INTO notas (matricula_id, tipo, numero, nota) VALUES (1, 'parcial', 0, 15);
        RAISE NOTICE 'FALLA >> numero 0 ACEPTADO'; fail := fail + 1;
    EXCEPTION WHEN check_violation THEN RAISE NOTICE 'OK    >> numero 0 rechazado (SQLSTATE %)', SQLSTATE; ok := ok + 1;
    END;

    -- RN-14: la matricula 13 (estudiante 7, curso 4) esta retirada
    BEGIN
        INSERT INTO notas (matricula_id, tipo, numero, nota) VALUES (13, 'practica', 1, 15);
        RAISE NOTICE 'FALLA >> nota sobre matricula RETIRADA aceptada (RN-14)'; fail := fail + 1;
    EXCEPTION WHEN check_violation THEN RAISE NOTICE 'OK    >> nota sobre matricula retirada rechazada (SQLSTATE %)', SQLSTATE; ok := ok + 1;
    END;

    -- duplicado (matricula, tipo, numero)
    INSERT INTO notas (matricula_id, tipo, numero, nota) VALUES (1, 'practica', 1, 14);
    BEGIN
        INSERT INTO notas (matricula_id, tipo, numero, nota) VALUES (1, 'practica', 1, 18);
        RAISE NOTICE 'FALLA >> duplicado (matricula, tipo, numero) ACEPTADO'; fail := fail + 1;
    EXCEPTION WHEN unique_violation THEN RAISE NOTICE 'OK    >> duplicado rechazado (SQLSTATE %)', SQLSTATE; ok := ok + 1;
    END;

    RAISE NOTICE 'pruebas negativas: OK=% fallas=%', ok, fail;
END $$;

-- 3. RN-15: media aritmetica del curso y promedio ponderado por creditos (C-27)
INSERT INTO notas (matricula_id, tipo, numero, nota) VALUES
  (1, 'parcial', 1, 16), (1, 'final', 1, 18),   -- matricula 1 = curso 1, 4 creditos (ya tiene practica 14)
  (2, 'practica', 1, 10);                        -- matricula 2 = curso 2, 3 creditos

SELECT 'nota del curso (media aritmetica)' seccion, m.curso_id, c.codigo, c.creditos,
       round(avg(n.nota), 2) AS nota_curso
FROM notas n
JOIN matriculas m ON m.id = n.matricula_id
JOIN cursos c     ON c.id = m.curso_id
WHERE m.estudiante_id = 1
GROUP BY m.curso_id, c.codigo, c.creditos
ORDER BY c.codigo;

-- promedio del periodo ponderado por creditos: suma(nota_curso*creditos) / suma(creditos)
WITH por_curso AS (
    SELECT m.curso_id, c.creditos, avg(n.nota) AS nota_curso
    FROM notas n
    JOIN matriculas m ON m.id = n.matricula_id
    JOIN cursos c     ON c.id = m.curso_id
    WHERE m.estudiante_id = 1 AND m.estado = 'activa'
    GROUP BY m.curso_id, c.creditos
)
SELECT 'promedio ponderado del periodo' seccion,
       round(sum(nota_curso * creditos) / sum(creditos), 2) AS promedio,
       sum(creditos) AS creditos_totales
FROM por_curso;

-- 4. C-29: la nota cuelga de la matricula -> borrar la matricula borra sus notas
SELECT 'antes del borrado' seccion, count(*) AS notas_de_la_matricula_1 FROM notas WHERE matricula_id = 1;
SAVEPOINT antes_del_borrado;
DELETE FROM matriculas WHERE id = 1;
SELECT 'despues del borrado' seccion, count(*) AS notas_de_la_matricula_1 FROM notas WHERE matricula_id = 1;
ROLLBACK TO SAVEPOINT antes_del_borrado;

SELECT 'datos intactos tras el rollback' seccion, count(*) AS notas FROM notas;

ROLLBACK;
