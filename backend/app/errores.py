# ============================================================
# GS08 · Matrículas y Notas | app/errores.py
# Autor: @dev | T1.1 | Sprint 1
# Traducción de errores a respuestas útiles para el SPA (C-11 exige «422 con el
# campo en el mensaje») y última línea de defensa: un error de integridad de la
# base NUNCA sale como 500.
#
# Las reglas se validan primero en la API (mensaje claro, con el campo) y la base
# las vuelve a rechazar; aquí se traduce lo que llegue de PostgreSQL:
#   uq_*   -> 409 / 422   |  fk_* -> 404  |  ck_* -> 422  |  RN-14 -> 409
# ============================================================
import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

log = logging.getLogger("gs08.errores")

# constraint -> (código HTTP, mensaje)
CONSTRAINTS = {
    "uq_estudiantes_codigo": (422, "Ya existe un estudiante con ese código."),
    "uq_estudiantes_dni": (422, "Ya existe un estudiante con ese DNI."),
    "uq_cursos_codigo": (409, "Ya existe un curso con ese código."),
    "uq_usuarios_nombre_usuario": (409, "Ya existe un usuario con ese nombre de usuario."),
    "uq_usuarios_email": (409, "Ya existe un usuario con ese email."),
    "uq_matriculas_estudiante_curso_periodo": (
        409,
        "Ese estudiante ya está matriculado en ese curso para el periodo indicado",
    ),
    "uq_notas_matricula_tipo_numero": (
        409,
        "Ya existe una nota de ese tipo y número para esa matrícula.",
    ),
    "fk_matriculas_estudiante": (404, "El estudiante indicado no existe."),
    "fk_matriculas_curso": (404, "El curso indicado no existe."),
    "fk_notas_matricula": (404, "La matrícula indicada no existe."),
}

MENSAJE_RN14 = "No se registran notas de una matrícula retirada (RN-14)."


def _mensaje_de_campo(loc: tuple, error: dict) -> str:
    campo = ".".join(str(p) for p in loc[1:]) or "cuerpo"
    mensaje = str(error.get("msg", "")).removeprefix("Value error, ")
    return f"{campo}: {mensaje}" if mensaje else campo


async def manejador_validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
    """422 con el campo y un mensaje en español (lo que muestra el SPA, T2.4)."""
    errores = [
        {"campo": ".".join(str(p) for p in e.get("loc", ())[1:]) or "cuerpo", "mensaje": _mensaje_de_campo(e.get("loc", ()), e)}
        for e in exc.errors()
    ]
    detalle = errores[0]["mensaje"] if errores else "La petición no es válida."
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": detalle, "errores": errores})


async def manejador_integridad(request: Request, exc: IntegrityError) -> JSONResponse:
    origen = getattr(exc, "orig", None)
    diagnostico = getattr(origen, "diag", None)
    constraint = (getattr(diagnostico, "constraint_name", None) or "").strip()
    sqlstate = (getattr(origen, "sqlstate", None) or "").strip()
    mensaje_base = (getattr(diagnostico, "message_primary", None) or "").strip()
    log.warning("integridad: constraint=%s sqlstate=%s detalle=%s", constraint or "-", sqlstate or "-", mensaje_base or "-")

    if constraint in CONSTRAINTS:
        codigo, mensaje = CONSTRAINTS[constraint]
        return JSONResponse(status_code=codigo, content={"detail": mensaje, "constraint": constraint})

    if sqlstate == "23514" and "RN-14" in mensaje_base:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": MENSAJE_RN14})

    if sqlstate == "23505":
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": "Ya existe un registro con esos datos."})
    if sqlstate == "23503":
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "La referencia indicada no existe."})
    if sqlstate in {"23514", "22P02", "22007", "22003"}:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Alguno de los datos no cumple una regla del sistema."},
        )

    # Desconocido: 409 con mensaje genérico, nunca 500 (el detalle queda en el log)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "No se pudo guardar: la base rechazó la operación."},
    )
