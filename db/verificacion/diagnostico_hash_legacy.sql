-- ============================================================
-- GS08 - Matriculas y Notas | diagnostico_hash_legacy.sql
-- HALLAZGO: el hash bcrypt que trae el seed del legacy NO corresponde a la
-- contrasena que documenta el propio legacy (admin / Admin123!).
-- Autor: @analista | Sprint 0
--
--   docker exec -i gs08-analista-verif psql -U postgres -d gs08_matriculas \
--     -v ON_ERROR_STOP=1 -f - < db/verificacion/diagnostico_hash_legacy.sql
--
-- Este script deja la prueba: control positivo (pgcrypto si calcula bcrypt),
-- prueba de prefijos $2y$/$2a$, y una lista de contrasenas candidatas.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1. Control positivo: pgcrypto sabe generar y verificar bcrypt
CREATE TEMP TABLE control AS SELECT crypt('Admin123!', gen_salt('bf', 10)) AS h;
SELECT
    (SELECT h FROM control)                                          AS hash_generado_2a,
    crypt('Admin123!', (SELECT h FROM control)) = (SELECT h FROM control) AS verifica_roundtrip,
    crypt('otra_clave',(SELECT h FROM control)) = (SELECT h FROM control) AS verifica_clave_mala;

-- 2. El hash del seed, tal cual y con el prefijo cambiado a $2a$
CREATE TEMP TABLE semilla AS SELECT password_hash AS h FROM usuarios WHERE nombre_usuario = 'admin';
SELECT
    (SELECT h FROM semilla) AS hash_del_seed,
    length((SELECT h FROM semilla)) AS largo,
    crypt('Admin123!', (SELECT h FROM semilla)) = (SELECT h FROM semilla) AS verifica_con_2y,
    crypt('Admin123!', replace((SELECT h FROM semilla), '$2y$', '$2a$'))
        = replace((SELECT h FROM semilla), '$2y$', '$2a$')                AS verifica_con_2a;

-- 3. Contrasenas candidatas (por si la documentada esta desactualizada).
--    Se comparan contra el hash normalizado a $2a$, que es con el unico prefijo
--    que pgcrypto calcula el digest correcto.
SELECT cand AS candidata,
       crypt(cand, replace((SELECT h FROM semilla), '$2y$', '$2a$'))
           = replace((SELECT h FROM semilla), '$2y$', '$2a$') AS coincide
FROM unnest(ARRAY[
    'Admin123!', 'Admin123', 'admin123!', 'Admin1234!', 'Admin2026!',
    'admin', 'Admin', 'Horizonte123!', 'Horizonte2026!', 'Admin123! '
]) AS cand;
