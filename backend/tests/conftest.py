# ============================================================
# GS08 · Matrículas y Notas | tests/conftest.py
# Autor: @dev | T1.1 | Sprint 1
# La base de pruebas se deja EXACTAMENTE como la deja la migración:
#   * se borra el esquema public,
#   * se corre `alembic upgrade head` (revisión 0001 = espejo de db/init/*.sql).
# Así las pruebas también comprueban la migración, no solo la API.
#
# DATABASE_URL: si no viene del entorno (CI) se usa gs08_test en localhost, que es
# una base APARTE de gs08_matriculas para no tocar el stack de humo.
# ============================================================
import itertools
import os
from collections.abc import Iterator
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://gs08:gs08_test_pwd@localhost:5432/gs08_test")

from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from alembic import command  # noqa: E402
from app.config import config  # noqa: E402
from app.db import SesionLocal  # noqa: E402
from app.main import app  # noqa: E402

ADMIN_USUARIO = "admin"
ADMIN_CLAVE = "Admin123!"
# hash bcrypt del seed (db/init/03-seed.sql): la contraseña del legacy, sin regenerar
HASH_SEED = "$2y$10$Tzgm/meEuR9o/nxq1ocKBu01ncP.pbnMay7a1aqWsuwXA4Q9Y9nzu"

_contador = itertools.count(1000)


@pytest.fixture(scope="session", autouse=True)
def base_de_datos_migrada() -> Iterator[None]:
    motor = create_engine(config.database_url, isolation_level="AUTOCOMMIT")
    with motor.connect() as conexion:
        conexion.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conexion.execute(text("CREATE SCHEMA public"))
    motor.dispose()

    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    command.upgrade(cfg, "head")
    yield


@pytest.fixture()
def cliente() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def sesion() -> Iterator[Session]:
    s = SesionLocal()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture()
def token(cliente: TestClient) -> str:
    respuesta = cliente.post("/api/v1/auth/login", json={"usuario": ADMIN_USUARIO, "password": ADMIN_CLAVE})
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()["access_token"]


@pytest.fixture()
def cabecera(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def nuevo_codigo():
    """Código de estudiante único por prueba (nunca choca con los del seed)."""

    def _codigo() -> str:
        return f"PZ{next(_contador)}"

    return _codigo


@pytest.fixture()
def nuevo_dni():
    """DNI de 8 dígitos único por prueba (el seed usa 45123456..56234567)."""

    def _dni() -> str:
        return f"7{next(_contador):07d}"

    return _dni
