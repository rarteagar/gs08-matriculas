# ============================================================
# GS08 · Matrículas y Notas | app/errores_oauth.py
# Autor: @dev | Rúbrica: OAuth2
# Los errores del endpoint de token se responden con la forma que manda el estándar
# (RFC 6749 §5.2): {"error": "...", "error_description": "..."} y WWW-Authenticate
# cuando corresponde. FastAPI, por defecto, responde {"detail": "..."}: aquí se
# devuelve el JSON de OAuth2 en su lugar, con el mismo código HTTP.
# ============================================================
from fastapi.responses import JSONResponse


class ErrorOAuth(Exception):
    """Error de OAuth2 con su cuerpo y sus cabeceras."""

    def __init__(self, error: str, descripcion: str, estado: int = 400, scope: str | None = None) -> None:
        self.error = error
        self.descripcion = descripcion
        self.estado = estado
        self.scope = scope
        super().__init__(f"{error}: {descripcion}")

    @property
    def cabeceras(self) -> dict[str, str]:
        if self.error == "invalid_client":
            return {"WWW-Authenticate": 'Bearer error="invalid_client"'}
        if self.error == "insufficient_scope" and self.scope:
            return {"WWW-Authenticate": f'Bearer error="insufficient_scope", scope="{self.scope}"'}
        return {}


def error_oauth(error: str, descripcion: str, estado: int = 400, scope: str | None = None) -> ErrorOAuth:
    return ErrorOAuth(error, descripcion, estado=estado, scope=scope)


async def manejador_oauth(_request, exc: ErrorOAuth) -> JSONResponse:
    """Responde el error tal como lo espera un cliente OAuth2."""
    return JSONResponse(
        status_code=exc.estado,
        content={"error": exc.error, "error_description": exc.descripcion},
        headers=exc.cabeceras or None,
    )
