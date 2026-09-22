-- ============================================================
-- GS08 - Matriculas y Notas | verificar_hash_admin.sql
-- Comprueba que el hash bcrypt del seed (copiado del legacy) corresponde a
-- la contrasena documentada: admin / Admin123!
-- Autor: @analista | Sprint 0
--
--   docker exec -i gs08-analista-verif psql -U postgres -d gs08_matriculas \
--     -v ON_ERROR_STOP=1 -f - < db/verificacion/verificar_hash_admin.sql
--
-- Usa pgcrypto (ya viene en la imagen oficial de PostgreSQL).
--
-- OJO, quirk encontrado probando: pgcrypto NO digiere el prefijo $2y$ que usa
-- PHP (acepta la cadena pero calcula otro digest); con el prefijo $2a$ SI coincide
-- (con $2b$ tampoco). El hash del seed se deja tal cual porque es un bcrypt valido
-- y la libreria que usara el API (bcrypt 4.2.1 de PyPI) lo verifica tal cual:
--   bcrypt.checkpw(b'Admin123!', b'$2y$10$Tzgm...') -> True
-- (evidencia: docs/analisis/evidencia/hash-legacy-python-bcrypt.txt).
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

SELECT
    u.nombre_usuario,
    u.rol,
    length(u.password_hash) AS largo_hash,
    crypt('Admin123!', u.password_hash) = u.password_hash                       AS verifica_2y_pgcrypto,
    crypt('Admin123!', replace(u.password_hash, '$2y$', '$2a$'))
        = replace(u.password_hash, '$2y$', '$2a$')                              AS verifica_2a_pgcrypto
FROM usuarios u
WHERE u.nombre_usuario = 'admin';

DO $$
DECLARE
    h      text;
    ok_2a  boolean;
    ok_2y  boolean;
    ok_mal boolean;
BEGIN
    SELECT password_hash INTO h FROM usuarios WHERE nombre_usuario = 'admin';

    IF h IS NULL THEN
        RAISE EXCEPTION 'FALLA >> no existe el usuario admin en la tabla';
    END IF;

    ok_2a  := crypt('Admin123!', replace(h, '$2y$', '$2a$')) = replace(h, '$2y$', '$2a$');
    ok_2y  := crypt('Admin123!', h) = h;
    ok_mal := crypt('clave_equivocada', replace(h, '$2y$', '$2a$')) = replace(h, '$2y$', '$2a$');

    IF NOT ok_2a THEN
        RAISE EXCEPTION 'FALLA >> el hash del seed NO corresponde a Admin123!';
    END IF;
    IF ok_mal THEN
        RAISE EXCEPTION 'FALLA >> el hash del seed acepta una clave equivocada';
    END IF;

    RAISE NOTICE 'OK   >> el hash del seed corresponde a Admin123! (bcrypt valido, coste 10)';
    RAISE NOTICE 'OK   >> el hash del seed rechaza una clave equivocada';
    IF ok_2y THEN
        RAISE NOTICE 'OK   >> pgcrypto lo verifica tambien con el prefijo $2y$ original';
    ELSE
        RAISE NOTICE 'NOTA >> pgcrypto necesita normalizar el prefijo a $2a$ (quirk de pgcrypto, no del hash); la libreria del API lo verifica con el $2y$ tal cual';
    END IF;
END $$;
