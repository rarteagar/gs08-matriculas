# ============================================================
# GS08 · Matrículas y Notas | app/deps.py
# Autor: @dev | T1.2 | Sprint 1 · Rúbrica OAuth2 (D-29)
# Dependencias de autenticación y autorización.
#   usuario_actual -> exige token válido (401 si falta, si es inválido o si la cuenta
#                     fue desactivada después de emitirlo)
#   requiere_scope -> exige token válido Y los scopes indicados (403 con el error
#                     estándar `insufficient_scope` si al token le faltan)
#
# El rol NO autoriza por sí solo: el rol ASIGNA scopes (app/scopes.py) y el endpoint
# pide el scope que necesita. Un `asistente` recibe los scopes de su rol; un `admin`,
# todos. Así «usuarios:admin» o «estudiantes:eliminar» son, en la práctica, solo admin.
# ============================================================
from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.errores_oauth import error_oauth
from app.models import Usuario
from app.scopes import SCOPES
from app.security import CABECERA_401, leer_token

# Documenta el flujo OAuth2 en Swagger (botón Authorize) y de dónde sale el token.
esquema_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", scopes=SCOPES, auto_error=False)


def token_de_authorization(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el token de sesión (cabecera Authorization: Bearer ...).",
            headers=CABECERA_401,
        )
    return authorization.split(" ", 1)[1].strip()


def _sesion(authorization: str | None, db: Session) -> tuple[Usuario, dict]:
    """Valida el token y devuelve el usuario de la base junto con su contenido."""
    payload = leer_token(token_de_authorization(authorization))
    try:
        usuario_id = int(payload.get("sub", "0"))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token de sesión no es válido.",
            headers=CABECERA_401,
        ) from exc

    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.estado:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La cuenta no existe o está desactivada.",
            headers=CABECERA_401,
        )
    return usuario, payload


def usuario_actual(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Usuario:
    return _sesion(authorization, db)[0]


def scopes_del_token(payload: dict) -> set[str]:
    return set(payload.get("scp") or [])


def requiere_scope(*pedidos: str):
    """Exige token válido y los scopes indicados. El rol asigna los scopes (RBAC)."""

    def dependencia(
        _token: str | None = Security(esquema_oauth2, scopes=list(pedidos)),
        authorization: str | None = Header(default=None),
        db: Session = Depends(get_db),
    ) -> Usuario:
        usuario, payload = _sesion(authorization, db)
        faltan = [pedido for pedido in pedidos if pedido not in scopes_del_token(payload)]
        if faltan:
            raise error_oauth(
                "insufficient_scope",
                f"Al token le falta el permiso: {', '.join(faltan)}.",
                estado=status.HTTP_403_FORBIDDEN,
                scope=" ".join(pedidos),
            )
        return usuario

    return dependencia
