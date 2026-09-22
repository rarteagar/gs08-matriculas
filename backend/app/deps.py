# ============================================================
# GS08 · Matrículas y Notas | app/deps.py
# Autor: @dev | T1.2 | Sprint 1
# Dependencias de autenticación y autorización.
#   usuario_actual -> exige token válido (401 si falta, si es inválido o si la
#                     cuenta fue desactivada después de emitirlo)
#   solo_admin     -> 403 si el rol no es admin (C-23)
# ============================================================
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Usuario
from app.security import CABECERA_401, leer_token


def token_de_authorization(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el token de sesión (cabecera Authorization: Bearer <token>).",
            headers=CABECERA_401,
        )
    return authorization.split(" ", 1)[1].strip()


def usuario_actual(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Usuario:
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
    return usuario


def solo_admin(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
    if usuario.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta operación es solo para el rol admin.",
        )
    return usuario
