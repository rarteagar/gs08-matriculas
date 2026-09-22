# ============================================================
# GS08 · Matrículas y Notas | app/routers/auth.py
# Autor: @dev | T1.2 | Sprint 1
# CU-01 / C-01..C-04:
#   * el usuario entra con nombre_usuario O email (igual que login.php del legacy)
#   * usuario con estado=false no entra, ni con la contraseña correcta (RN-13)
#   * la contraseña se verifica contra el hash $2y$ del seed tal cual (RN-01/C-03)
# ============================================================
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import config
from app.db import get_db
from app.deps import usuario_actual
from app.models import Usuario
from app.schemas import LoginEntrada, LoginSalida, UsuarioSalida
from app.security import crear_token, verificar_password

log = logging.getLogger("gs08.auth")
router = APIRouter(prefix="/api/v1/auth", tags=["autenticación"])

MENSAJE_CREDENCIALES = "Usuario o contraseña incorrectos."
MENSAJE_INACTIVO = "Tu cuenta está desactivada. Contacta al administrador del sistema."


@router.post("/login", response_model=LoginSalida)
def login(datos: LoginEntrada, db: Session = Depends(get_db)) -> dict:
    fila = (
        db.execute(
            text("SELECT id FROM usuarios WHERE nombre_usuario = :u OR lower(email) = lower(:u) ORDER BY id LIMIT 1"),
            {"u": datos.usuario},
        )
        .mappings()
        .first()
    )
    if fila is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=MENSAJE_CREDENCIALES)

    usuario = db.get(Usuario, fila["id"])
    if usuario is None or not verificar_password(datos.password, usuario.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=MENSAJE_CREDENCIALES)
    if not usuario.estado:
        # C-02: la cuenta desactivada no entra aunque la contraseña sea correcta
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=MENSAJE_INACTIVO)

    token, expira = crear_token(usuario)
    log.info("login correcto: %s (rol %s)", usuario.nombre_usuario, usuario.rol)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expira_en": expira,
        "expira_en_minutos": config.access_token_expire_minutes,
        "usuario": UsuarioSalida(**usuario.como_diccionario()),
    }


@router.get("/yo", response_model=UsuarioSalida)
def yo(usuario: Usuario = Depends(usuario_actual)) -> dict:
    """Quién soy: lo usa el SPA para reconstruir la sesión desde el token."""
    return usuario.como_diccionario()
