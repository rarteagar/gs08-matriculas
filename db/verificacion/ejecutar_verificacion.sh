#!/usr/bin/env bash
# ============================================================
# GS08 - Matriculas y Notas | ejecutar_verificacion.sh
# Levanta un PostgreSQL 16 DESECHABLE (contenedor efimero, puerto 55432),
# carga db/init (01-schema.sql, 02-view.sql, 03-seed.sql, 04-notas.sql) como lo
# hace docker compose, y corre las verificaciones del modelo de datos.
# Autor: @analista | Sprint 0 y Sprint 1 (T1.5)
#
#   bash db/verificacion/ejecutar_verificacion.sh
#
# No toca el stack de @devops (usa otro nombre de contenedor y otro puerto).
# Deja la evidencia en docs/analisis/evidencia/. Para borrar la base:
#   docker rm -f gs08-analista-verif
# ============================================================
set -uo pipefail

CONTENEDOR="${CONTENEDOR:-gs08-analista-verif}"
PUERTO="${PUERTO:-55432}"
IMAGEN="postgres:16.15-alpine3.24"
# Mismos valores que docker-compose.yml (usuario/base de la app), para que la
# verificacion corra con el mismo dueno de las tablas que en el stack real.
USUARIO="${USUARIO:-gs08}"
CLAVE="${CLAVE:-gs08_dev_pwd}"
BASE="${BASE:-gs08_matriculas}"
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
EVID="$RAIZ/docs/analisis/evidencia"
mkdir -p "$EVID"

echo "== 1. PostgreSQL desechable ($IMAGEN) con db/init montado como initdb.d =="
docker rm -f "$CONTENEDOR" >/dev/null 2>&1
docker run -d --name "$CONTENEDOR" \
  -e POSTGRES_USER="$USUARIO" -e POSTGRES_PASSWORD="$CLAVE" -e POSTGRES_DB="$BASE" \
  -v "$RAIZ/db/init:/docker-entrypoint-initdb.d:ro" \
  -p "$PUERTO:5432" "$IMAGEN" >/dev/null || exit 1

echo "== 2. Esperando que el entrypoint ejecute 01-schema, 02-view y 03-seed =="
for i in $(seq 1 60); do
  if docker exec "$CONTENEDOR" psql -U "$USUARIO" -d "$BASE" -tAc \
       "select count(*) from pg_tables where schemaname='public'" 2>/dev/null | grep -q '^4$'; then
    echo "   base lista en ${i}s"
    break
  fi
  sleep 1
done
docker logs "$CONTENEDOR" > "$EVID/inicializacion-contenedor.txt" 2>&1

echo "== 3. verificar_modelo.sql (comprobaciones + pruebas negativas de las reglas) =="
docker exec -i "$CONTENEDOR" psql -U "$USUARIO" -d "$BASE" -v ON_ERROR_STOP=1 -f - \
  < "$RAIZ/db/verificacion/verificar_modelo.sql" > "$EVID/verificacion-modelo.txt" 2>&1
EXIT_MODELO=$?

echo "== 4. verificar_hash_admin.sql (el hash bcrypt del seed) =="
docker exec -i "$CONTENEDOR" psql -U "$USUARIO" -d "$BASE" -v ON_ERROR_STOP=1 -f - \
  < "$RAIZ/db/verificacion/verificar_hash_admin.sql" > "$EVID/verificacion-hash-admin.txt" 2>&1
EXIT_HASH=$?

echo "== 5. diagnostico_hash_legacy.sql (el quirk de pgcrypto con el prefijo \$2y\$) =="
docker exec -i "$CONTENEDOR" psql -U "$USUARIO" -d "$BASE" \
  < "$RAIZ/db/verificacion/diagnostico_hash_legacy.sql" > "$EVID/diagnostico-hash-legacy.txt" 2>&1

echo "== 6. prueba_busqueda_rendimiento.sql (100.000 filas: LIKE vs indice trigram) =="
docker exec -i "$CONTENEDOR" psql -U "$USUARIO" -d "$BASE" \
  < "$RAIZ/db/verificacion/prueba_busqueda_rendimiento.sql" > "$EVID/busqueda-rendimiento.txt" 2>&1

echo "== 7. verificar_notas.sql (04-notas.sql: tabla, vista, RN-14/15/16, boleta) =="
docker exec -i "$CONTENEDOR" psql -U "$USUARIO" -d "$BASE" -v ON_ERROR_STOP=1 -f - \
  < "$RAIZ/db/verificacion/verificar_notas.sql" > "$EVID/verificacion-notas.txt" 2>&1
EXIT_NOTAS=$?

OK=$(grep -c 'NOTICE:  OK' "$EVID/verificacion-modelo.txt")
OK_HASH=$(grep -c 'NOTICE:  OK' "$EVID/verificacion-hash-admin.txt")
OK_NOTAS=$(grep -c 'NOTICE:  OK' "$EVID/verificacion-notas.txt")
FALLAS=$(grep -c 'FALLA' "$EVID/verificacion-modelo.txt" "$EVID/verificacion-hash-admin.txt" "$EVID/verificacion-notas.txt" | awk -F: '{s+=$2} END {print s+0}')

echo
echo "verificar_modelo.sql      exit=$EXIT_MODELO   comprobaciones OK=$OK   fallas=$FALLAS"
echo "verificar_hash_admin.sql  exit=$EXIT_HASH   comprobaciones OK=$OK_HASH"
echo "verificar_notas.sql       exit=$EXIT_NOTAS   comprobaciones OK=$OK_NOTAS"
grep -E 'NOTICE:  (OK|NOTA)|FALLA' "$EVID/verificacion-hash-admin.txt" | sed 's/^psql:<stdin>:[0-9]*: //' || true
echo
echo "mediciones de busqueda (docs/analisis/evidencia/busqueda-rendimiento.txt):"
grep -E 'Execution Time|Seq Scan|Bitmap Index Scan|ERROR' "$EVID/busqueda-rendimiento.txt" | sed 's/^ *//' || true
tail -4 "$EVID/verificacion-modelo.txt"
echo
echo "Evidencia: $EVID"
echo "Apagar la base de verificacion: docker rm -f $CONTENEDOR"

[ "$EXIT_MODELO" -eq 0 ] && [ "$EXIT_HASH" -eq 0 ] && [ "$EXIT_NOTAS" -eq 0 ]
