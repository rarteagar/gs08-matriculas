# ============================================================
# GS08 · Matrículas y Notas | app/db.py
# Autor: @dev | T1.1 | Sprint 1
# Motor y sesión de SQLAlchemy.
#
# IMPORTANTE (decisión D-14): el DDL NO lo crea SQLAlchemy. El esquema lo aplican
#   * db/init/*.sql  cuando el entrypoint de postgres crea el volumen pgdata, o
#   * alembic upgrade head  (misma DDL, revisión 0001 generada desde db/init/*.sql)
# Si las dos fuentes divergen hay dos verdades del esquema: la revisión inicial
# está generada con backend/herramientas/generar_revision_inicial.py, que copia
# los scripts de @analista tal cual.
# ============================================================
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import config


class Base(DeclarativeBase):
    """Base declarativa: se usa para consultar y para los INSERT/UPDATE, nunca para el DDL."""


engine = create_engine(
    config.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    future=True,
)

SesionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Dependencia de FastAPI: una sesión por petición."""
    db = SesionLocal()
    try:
        yield db
    finally:
        db.close()
