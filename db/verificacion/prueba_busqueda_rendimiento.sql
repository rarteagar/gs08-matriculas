-- ============================================================
-- GS08 - Matriculas y Notas | prueba_busqueda_rendimiento.sql
-- Medicion del buscador del listado (el LIKE '%texto%' del legacy) con
-- volumen realista, y del indice trigram que lo acelera.
-- Autor: @analista | Sprint 0
--
--   docker exec -i gs08-analista-verif psql -U postgres -d gs08_matriculas \
--     -f - < db/verificacion/prueba_busqueda_rendimiento.sql
--
-- Solo mide: inserta 100.000 estudiantes de prueba (nada de matriculas), corre
-- EXPLAIN ANALYZE con y sin indice y termina con ROLLBACK (no deja datos).
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pg_trgm;

BEGIN;

-- 1. Buscador del legacy: LIKE '%quispe%' -> en PostgreSQL hay que usar ILIKE
INSERT INTO estudiantes (codigo, dni, nombres, apellidos)
SELECT 'X' || lpad(g::text, 8, '0'),
       lpad((10000000 + g)::text, 8, '0'),
       'Nombre' || g,
       CASE WHEN g % 100000 = 77777 THEN 'Quispe Huamán' ELSE 'Apellido' || g END
FROM generate_series(1, 100000) g;

ANALYZE estudiantes;

EXPLAIN (ANALYZE, BUFFERS, TIMING)
SELECT count(*) FROM estudiantes
WHERE codigo ILIKE '%quispe%' OR dni ILIKE '%quispe%'
   OR nombres ILIKE '%quispe%' OR apellidos ILIKE '%quispe%';

-- 2. Indice trigram sobre el texto normalizado que busca el buscador
CREATE INDEX idx_estudiantes_busqueda_trgm ON estudiantes
    USING gin ((lower(apellidos || ' ' || nombres)) gin_trgm_ops);

EXPLAIN (ANALYZE, BUFFERS, TIMING)
SELECT count(*) FROM estudiantes
WHERE lower(apellidos || ' ' || nombres) LIKE '%quispe%';

-- 3. Tildes: el legacy buscaba "huaman" y encontraba "Huamán" porque la collation
--    utf8mb4_unicode_ci de MySQL ignora tildes. En PostgreSQL esto no pasa de gratis:
CREATE EXTENSION IF NOT EXISTS unaccent;

SELECT count(*) AS ilike_sin_unaccent FROM estudiantes WHERE apellidos ILIKE '%huaman%';
SELECT count(*) AS con_unaccent      FROM estudiantes WHERE unaccent(apellidos) ILIKE unaccent('%huaman%');

-- Y ojo: unaccent() es STABLE, no IMMUTABLE, asi que no se puede meter en un indice
-- de expresion directamente. Se deja el intento como prueba (debe fallar):
CREATE INDEX idx_prueba_unaccent ON estudiantes
    USING gin (unaccent(apellidos) gin_trgm_ops);

ROLLBACK;
