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

from app import graphql, observabilidad
from app.config import config
from app.errores import manejador_integridad, manejador_validacion
from app.errores_oauth import ErrorOAuth, manejador_oauth
from app.routers import auditoria, auth, cursos, dashboard, estudiantes, matriculas, salud, usuarios

observabilidad.configurar_logs()
log = logging.getLogger("gs08")

app = FastAPI(
    title="GS08 · Matrículas y Notas",
    version="0.3.0",
    description=(
        "API del MVP: autenticación, panel, estudiantes, cursos, matrículas, usuarios, "
        "notas, boleta y bitácora. Esquema de datos: db/init/*.sql y la revisión 0001 de Alembic. "
        "La misma información se puede consultar por REST (/api/v1) o por GraphQL (/graphql). "
        "Autenticación: OAuth2 password grant (/api/v1/auth/token) con scopes por rol; los errores "
        "del endpoint de token siguen el formato del RFC 6749."
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

# Id de petición + log estructurado + bitácora documental + invalidación de la caché.
app.add_middleware(observabilidad.ContextoPeticion)

# Un error de integridad nunca sale como 500 (C-11) y una validación sale con el campo
app.add_exception_handler(IntegrityError, manejador_integridad)
app.add_exception_handler(RequestValidationError, manejador_validacion)
# Los errores de OAuth2 salen con la forma del estándar (RFC 6749 §5.2)
app.add_exception_handler(ErrorOAuth, manejador_oauth)

Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

for modulo in (salud, auth, estudiantes, cursos, matriculas, usuarios, dashboard, auditoria):
    app.include_router(modulo.router)

# routers secundarios del módulo de matrículas (notas sueltas y boleta)
app.include_router(matriculas.router_notas)
app.include_router(matriculas.router_boleta)

# Segunda puerta de entrada al mismo modelo, para el ítem "REST y GraphQL" de la rúbrica.
app.include_router(graphql.router)


@app.get("/", include_in_schema=False)
def raiz() -> dict:
    return {
        "servicio": "GS08 · Matrículas y Notas",
        "entorno": config.environment,
        "api": "/api/v1",
        "graphql": "/graphql",
        "oauth2_token": "/api/v1/auth/token",
        "salud": "/api/v1/health",
        "metricas": "/metrics",
        "documentacion": "/docs",
    }


@app.exception_handler(Exception)
async def manejador_inesperado(request: Request, exc: Exception) -> JSONResponse:
    """Red de seguridad: se registra el error real y se responde 500 con mensaje corto."""
    log.exception("error inesperado en %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor (revisar el log del API)."})
