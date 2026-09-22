# ============================================================
# GS08 · Matrículas y Notas | app/routers/salud.py
# Autor: @dev | T1.1 | Sprint 1
# Contrato de @devops (plan-contenedores-ci.md §3):
#   GET /health         -> 200 {"status":"ok"} comprobando PostgreSQL (HEALTHCHECK)
#   GET /api/v1/health  -> lo mismo, para entrar por nginx (C-34)
#   GET /metrics        -> formato Prometheus (lo expone main.py con el instrumentator)
# ============================================================
import logging
import socket

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import config
from app.db import get_db
from app.schemas import SaludSalida

log = logging.getLogger("gs08.salud")
router = APIRouter(tags=["salud"])


def _estado_base_de_datos(db: Session) -> dict:
    try:
        version = db.execute(text("SELECT version()")).scalar_one()
    except SQLAlchemyError as exc:  # la API responde, pero sin base de datos
        log.error("PostgreSQL no responde: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La API está arriba pero PostgreSQL no responde.",
        ) from exc
    return {
        "status": "ok",
        # "PostgreSQL 16.15 on x86_64..." -> se publica solo el motor y la version
        "motor": str(version).split(" on ")[0],
        "instancia": socket.gethostname(),
        "entorno": config.environment,
    }


@router.get("/health", response_model=SaludSalida)
@router.get("/api/v1/health", response_model=SaludSalida)
def salud(db: Session = Depends(get_db)) -> dict:
    return _estado_base_de_datos(db)
