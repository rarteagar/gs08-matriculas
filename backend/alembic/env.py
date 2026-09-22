# ============================================================
# GS08 · Matrículas y Notas | alembic/env.py
# Autor: @dev | T1.1 | Sprint 1
# La conexión sale de DATABASE_URL (app.config), igual que en el API: una sola
# variable para los dos caminos. No hay `target_metadata` porque el DDL no se
# autogenera: la revisión inicial está generada desde db/init/*.sql (D-14) y las
# siguientes migraciones se escriben a mano.
# ============================================================
from sqlalchemy import create_engine, pool

from alembic import context
from app.config import config as configuracion

config = context.config


def run_migrations_offline() -> None:
    context.configure(
        url=configuracion.database_url,
        target_metadata=None,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    motor = create_engine(configuracion.database_url, poolclass=pool.NullPool)
    with motor.connect() as conexion:
        context.configure(connection=conexion, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()
    motor.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
