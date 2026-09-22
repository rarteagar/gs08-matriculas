-- ============================================================
-- GS08 - Matriculas y Notas | catalogo_esquema.sql
-- Foto textual y ordenada del esquema + los datos, para comparar dos bases
-- linea por linea (D-14: db/init/*.sql vs la revision inicial de Alembic).
-- Autor: @analista | Sprint 1
--
--   docker exec gs08-analista-verif psql -U gs08 -d gs08_matriculas -tA -f - \
--     < db/verificacion/catalogo_esquema.sql > catalogo-dbinit.txt
--
-- Salida: una linea por objeto (EXTENSION / TABLA / COLUMNA / CONSTRAINT /
-- INDICE / VISTA / FUNCION / TRIGGER / SECUENCIA) y una por tabla con su conteo
-- de filas. Se ignoran a proposito: la tabla y el indice de alembic_version
-- (solo existen en la base migrada) y el valor de las secuencias (los ids con
-- huecos son normales, D-13: se compara que existan, no su last_value).
-- ============================================================

SELECT linea FROM (
    SELECT 1 AS orden, 'EXTENSION ' || extname || ' v' || extversion AS linea
      FROM pg_extension WHERE extname <> 'plpgsql'

    UNION ALL
    SELECT 2, 'TABLA ' || c.relname
      FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public' AND c.relkind = 'r' AND c.relname <> 'alembic_version'

    UNION ALL
    SELECT 3, 'COLUMNA ' || c.relname || '.' || a.attname || ' ' || format_type(a.atttypid, a.atttypmod)
              || CASE WHEN a.attnotnull THEN ' NOT NULL' ELSE ' NULL' END
              || ' DEFAULT ' || coalesce(pg_get_expr(d.adbin, d.adrelid), '-')
      FROM pg_attribute a
      JOIN pg_class c     ON c.oid = a.attrelid
      JOIN pg_namespace n ON n.oid = c.relnamespace
      LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
     WHERE n.nspname = 'public' AND c.relkind IN ('r', 'v')
       AND a.attnum > 0 AND NOT a.attisdropped AND c.relname <> 'alembic_version'

    UNION ALL
    SELECT 4, 'CONSTRAINT ' || c.relname || ' ' || con.conname || ' ' || pg_get_constraintdef(con.oid)
      FROM pg_constraint con
      JOIN pg_class c     ON c.oid = con.conrelid
      JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public' AND c.relname <> 'alembic_version'

    UNION ALL
    SELECT 5, 'INDICE ' || indexdef
      FROM pg_indexes
     WHERE schemaname = 'public' AND indexname <> 'alembic_version_pkc'

    UNION ALL
    SELECT 6, 'VISTA ' || viewname FROM pg_views WHERE schemaname = 'public'

    UNION ALL
    SELECT 7, 'FUNCION ' || p.proname || '(' || pg_get_function_arguments(p.oid) || ') md5=' || md5(p.prosrc)
      FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = 'public'

    UNION ALL
    SELECT 8, 'TRIGGER ' || pg_get_triggerdef(t.oid)
      FROM pg_trigger t
      JOIN pg_class c     ON c.oid = t.tgrelid
      JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE NOT t.tgisinternal AND n.nspname = 'public'

    UNION ALL
    SELECT 11, 'COMENTARIO ' || c.relname || ' ' || coalesce(obj_description(c.oid, 'pg_class'), '-')
      FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public' AND c.relkind IN ('r', 'v') AND c.relname <> 'alembic_version'

    UNION ALL
    SELECT 12, 'COMENTARIO ' || c.relname || '.' || a.attname || ' ' || coalesce(col_description(c.oid, a.attnum), '-')
      FROM pg_attribute a
      JOIN pg_class c     ON c.oid = a.attrelid
      JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public' AND c.relkind IN ('r', 'v') AND a.attnum > 0 AND NOT a.attisdropped
       AND col_description(c.oid, a.attnum) IS NOT NULL AND c.relname <> 'alembic_version'

    UNION ALL
    SELECT 9, 'SECUENCIA ' || c.relname
      FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public' AND c.relkind = 'S'

    UNION ALL
    SELECT 10, 'DATOS ' || c.relname || '=' ||
               (xpath('/row/c/text()',
                      query_to_xml('SELECT count(*) AS c FROM public.' || quote_ident(c.relname),
                                   false, true, '')))[1]::text
      FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public' AND c.relkind = 'r'
       AND c.relname IN ('usuarios', 'estudiantes', 'cursos', 'matriculas', 'notas')
) s
ORDER BY orden, linea;
