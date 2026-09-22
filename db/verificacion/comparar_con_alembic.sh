#!/usr/bin/env bash
# ============================================================
# GS08 - Matriculas y Notas | comparar_con_alembic.sh
# D-14: compara, linea por linea, el esquema que deja db/init/*.sql con el que
# deja `alembic upgrade head` (revision inicial de @dev, backend/alembic/).
# Autor: @analista | Sprint 1 (T1.5 / T3.4)
#
#   bash db/verificacion/comparar_con_alembic.sh
#
# Levanta DOS bases limpias en una red propia (no toca el stack de @devops ni la
# base de verificacion): una con los scripts de db/init montados, otra vacia a la
# que se le aplica la migracion. Despues saca la foto del catalogo de las dos
# (db/verificacion/catalogo_esquema.sql) y las compara.
#
# Necesita la imagen gs08-api:local (trae alembic y las dependencias del backend).
# exit 0 = identicas. Deja la evidencia en docs/analisis/evidencia/.
# ============================================================
set -uo pipefail

RED="${RED:-gs08-d14-net}"
INIT="${INIT:-gs08-d14-init}"
MIG="${MIG:-gs08-d14-alembic}"
IMAGEN_DB="${IMAGEN_DB:-postgres:16.15-alpine3.24}"
IMAGEN_API="${IMAGEN_API:-gs08-api:local}"
USUARIO="${USUARIO:-gs08}"
CLAVE="${CLAVE:-gs08_dev_pwd}"
BASE="${BASE:-gs08_matriculas}"
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
EVID="$RAIZ/docs/analisis/evidencia"
mkdir -p "$EVID"

echo "== 1. Red y dos bases limpias: una con db/init, otra vacia =="
docker rm -f "$INIT" "$MIG" >/dev/null 2>&1
docker network create "$RED" >/dev/null 2>&1
docker run -d --name "$INIT" --network "$RED" \
  -e POSTGRES_USER="$USUARIO" -e POSTGRES_PASSWORD="$CLAVE" -e POSTGRES_DB="$BASE" \
  -v "$RAIZ/db/init:/docker-entrypoint-initdb.d:ro" "$IMAGEN_DB" >/dev/null || exit 2
docker run -d --name "$MIG" --network "$RED" \
  -e POSTGRES_USER="$USUARIO" -e POSTGRES_PASSWORD="$CLAVE" -e POSTGRES_DB="$BASE" \
  "$IMAGEN_DB" >/dev/null || exit 2

echo "== 2. Esperando las dos bases (la primera tiene que haber corrido 01 a 04) =="
for i in $(seq 1 60); do
  TABLAS=$(docker exec "$INIT" psql -U "$USUARIO" -d "$BASE" -tAc \
    "select count(*) from pg_tables where schemaname='public'" 2>/dev/null)
  [ "$TABLAS" = "5" ] && { echo "   db/init lista con 5 tablas en ${i}s"; break; }
  sleep 1
done
for i in $(seq 1 60); do
  docker exec "$MIG" psql -U "$USUARIO" -d "$BASE" -tAc "select 1" >/dev/null 2>&1 && break
  sleep 1
done

echo "== 3. alembic upgrade head sobre la base vacia (imagen $IMAGEN_API) =="
docker run --rm --network "$RED" -v "$RAIZ/backend:/app" \
  -e DATABASE_URL="postgresql+psycopg://$USUARIO:$CLAVE@$MIG:5432/$BASE" \
  --entrypoint alembic "$IMAGEN_API" upgrade head 2>&1 | tail -5
echo "   revision aplicada: $(docker exec "$MIG" psql -U "$USUARIO" -d "$BASE" -tAc 'select version_num from alembic_version')"

echo "== 4. Foto del catalogo de las dos bases =="
# docker cp NO entiende rutas MSYS (/d/dev/...): hay que darle ruta nativa
RUTA_CAT="$(cygpath -w "$RAIZ/db/verificacion/catalogo_esquema.sql" 2>/dev/null || echo "$RAIZ/db/verificacion/catalogo_esquema.sql")"
docker cp "$RUTA_CAT" "$INIT:/tmp/cat.sql"
docker cp "$RUTA_CAT" "$MIG:/tmp/cat.sql"
docker exec "$INIT" psql -U "$USUARIO" -d "$BASE" -tA -f /tmp/cat.sql > "$EVID/catalogo-dbinit.txt" 2>&1
docker exec "$MIG"  psql -U "$USUARIO" -d "$BASE" -tA -f /tmp/cat.sql > "$EVID/catalogo-alembic.txt" 2>&1
wc -l "$EVID/catalogo-dbinit.txt" "$EVID/catalogo-alembic.txt"

# Guarda: si la foto salio vacia o con error, NO se puede declarar "identicas"
for F in catalogo-dbinit catalogo-alembic; do
  LINEAS=$(wc -l < "$EVID/$F.txt")
  if [ "$LINEAS" -lt 100 ] || grep -qE '^(ERROR|GetFileAttributes)' "$EVID/$F.txt"; then
    echo "   FALLA: la foto del catalogo $F salio mal ($LINEAS lineas):"
    head -3 "$EVID/$F.txt"
    exit 2
  fi
done

echo "== 5. Comparacion linea por linea =="
if diff -u "$EVID/catalogo-dbinit.txt" "$EVID/catalogo-alembic.txt" > "$EVID/catalogo-diff.txt"; then
  echo "   IDENTICOS: los dos caminos dejan el mismo esquema y los mismos datos"
  DIF=0
else
  echo "   HAY DIFERENCIAS (estan en catalogo-diff.txt):"
  head -40 "$EVID/catalogo-diff.txt"
  DIF=1
fi

echo "== 6. Secuencias: el catalogo compara que existan, no su last_value =="
for t in usuarios estudiantes cursos matriculas; do
  A=$(docker exec "$INIT" psql -U "$USUARIO" -d "$BASE" -tAc "select last_value from ${t}_id_seq")
  B=$(docker exec "$MIG"  psql -U "$USUARIO" -d "$BASE" -tAc "select last_value from ${t}_id_seq")
  if [ "$A" = "$B" ]; then E=OK; else E=DIFERENTE; DIF=1; fi
  printf "   %-12s db/init=%-4s alembic=%-4s %s\n" "$t" "$A" "$B" "$E"
done

echo
echo "Evidencia: catalogo-dbinit.txt, catalogo-alembic.txt, catalogo-diff.txt"
echo "Apagar: docker rm -f $INIT $MIG && docker network rm $RED"
exit $DIF
