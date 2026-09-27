#!/bin/sh
# ============================================================
# Aplica el esquema, la vista y los datos iniciales de db/init.
#
# Lo usa el servicio "migraciones" del compose de Coolify: Postgres solo
# ejecuta /docker-entrypoint-initdb.d la PRIMERA vez que crea su volumen, y en
# un servidor donde ese volumen ya existia la base queda vacia (el login
# respondia 500 porque no existia la tabla usuarios).
#
# Es idempotente: si la tabla usuarios ya existe no toca nada, asi que puede
# correr en cada despliegue sin riesgo para los datos.
# ============================================================
set -e

n=$(psql -Atc "select count(*) from information_schema.tables where table_schema='public' and table_name='usuarios'")

if [ "$n" = "0" ]; then
  echo "Base sin esquema: se aplican los .sql de db/init"
  for f in /sql/01-schema.sql /sql/02-view.sql /sql/03-seed.sql /sql/04-notas.sql; do
    echo "  -> $f"
    psql -v ON_ERROR_STOP=1 -q -f "$f"
  done
  echo "Esquema, vista y datos iniciales aplicados."
else
  echo "El esquema ya existe: no se aplica nada."
fi
