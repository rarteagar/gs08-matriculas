# ============================================================
# GS08 · Matrículas y Notas | app/main.py
# Autor: @dev | T1.1 | Sprint 1
# La app que arranca la imagen: uvicorn app.main:app (backend/Dockerfile §CMD).
#   /health, /api/v1/health  -> salud + PostgreSQL   (contrato de @devops)
#   /metrics                 -> Prometheus (instrumentator 8.1.0, D-17: se lee
#                               directo del API, no a través del balanceador)
#   /api/v1/...              -> CU-01..CU-15
# ============================================================
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.exc import IntegrityError

from app.config import config
from app.errores import manejador_integridad, manejador_validacion
from app.routers import auth, cursos, dashboard, estudiantes, matriculas, salud, usuarios

logging.basicConfig(
    level=getattr(logging, config.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
)
log = logging.getLogger("gs08")

app = FastAPI(
    title="GS08 · Matrículas y Notas",
    version="0.1.0",
    description=(
        "API del MVP: autenticación, panel, estudiantes, cursos, matrículas, usuarios, "
        "notas y boleta. Esquema de datos: db/init/*.sql y la revisión 0001 de Alembic."
    ),
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.origenes_cors,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Un error de integridad nunca sale como 500 (C-11) y una validación sale con el campo
app.add_exception_handler(IntegrityError, manejador_integridad)
app.add_exception_handler(RequestValidationError, manejador_validacion)

Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

for modulo in (salud, auth, estudiantes, cursos, matriculas, usuarios, dashboard):
    app.include_router(modulo.router)

# routers secundarios del módulo de matrículas (notas sueltas y boleta)
app.include_router(matriculas.router_notas)
app.include_router(matriculas.router_boleta)


@app.get("/", include_in_schema=False)
def raiz() -> dict:
    return {
        "servicio": "GS08 · Matrículas y Notas",
        "entorno": config.environment,
        "api": "/api/v1",
        "salud": "/api/v1/health",
        "metricas": "/metrics",
        "documentacion": "/docs",
    }


@app.exception_handler(Exception)
async def manejador_inesperado(request: Request, exc: Exception) -> JSONResponse:
    """Red de seguridad: se registra el error real y se responde 500 con mensaje corto."""
    log.exception("error inesperado en %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor (revisar el log del API)."})
