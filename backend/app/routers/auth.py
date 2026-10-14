# ============================================================
# GS08 · Matrículas y Notas | app/routers/auth.py
# Autor: @dev | T1.2 | Sprint 1
# CU-01 / C-01..C-04:
#   * el usuario entra con nombre_usuario O email (igual que login.php del legacy)
#   * usuario con estado=false no entra, ni con la contraseña correcta (RN-13)
#   * la contraseña se verifica contra el hash $2y$ del seed tal cual (RN-01/C-03)
# ============================================================
import logging
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import config
from app.db import get_db
from app.deps import requiere_scope
from app.errores_oauth import error_oauth
from app.models import Usuario
from app.schemas import LoginEntrada, LoginSalida, TokenSalida, UsuarioSalida
from app.scopes import revisar
from app.security import crear_token, scopes_del_usuario, verificar_password

log = logging.getLogger("gs08.auth")
router = APIRouter(prefix="/api/v1/auth", tags=["autenticación"])

MENSAJE_CREDENCIALES = "Usuario o contraseña incorrectos."
MENSAJE_INACTIVO = "Tu cuenta está desactivada. Contacta al administrador del sistema."


def _usuario_autenticado(db: Session, identificador: str, password: str) -> Usuario:
    """Camino único de autenticación: lo usan /login (compatibilidad) y /token (OAuth2)."""
    fila = (
        db.execute(
            text("SELECT id FROM usuarios WHERE nombre_usuario = :u OR lower(email) = lower(:u) ORDER BY id LIMIT 1"),
            {"u": identificador},
        )
        .mappings()
        .first()
    )
    if fila is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=MENSAJE_CREDENCIALES)

    usuario = db.get(Usuario, fila["id"])
    if usuario is None or not verificar_password(password, usuario.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=MENSAJE_CREDENCIALES)
    if not usuario.estado:
        # C-02: la cuenta desactivada no entra aunque la contraseña sea correcta
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=MENSAJE_INACTIVO)
    return usuario


@router.post("/login", response_model=LoginSalida, summary="Entrar (formato del SPA: JSON)")
def login(datos: LoginEntrada, db: Session = Depends(get_db)) -> dict:
    """Entrada del SPA: JSON con usuario y contraseña.

    Es la misma autenticación que `/token`, con el formato y la respuesta que ya usaba
    el frontend (compatibilidad: el SPA no cambia). El token que emite **ya lleva los
    scopes** del rol, así que sirve en todos los endpoints con `requiere_scope`.
    """
    usuario = _usuario_autenticado(db, datos.usuario, datos.password)
    token, expira = crear_token(usuario, scopes_del_usuario(usuario))
    log.info("login correcto: %s (rol %s, %s scopes)", usuario.nombre_usuario, usuario.rol, len(scopes_del_usuario(usuario)))
    return {
        "access_token": token,
        "token_type": "bearer",
        "expira_en": expira,
        "expira_en_minutos": config.access_token_expire_minutes,
        "usuario": UsuarioSalida(**usuario.como_diccionario()),
    }


class FormularioToken:
    """Formulario del endpoint de token (RFC 6749 §4.3), declarado a mano.

    Dos motivos para no usar el `OAuth2PasswordRequestForm` de FastAPI:
      * valida `grant_type` con un patrón y responde 422, cuando el estándar manda
        responder 400 `unsupported_grant_type`;
      * exige `client_id`/`client_secret`, y el SPA es un **cliente público**: manda
        solo usuario y contraseña. Si vienen, se validan (útil para integraciones).
    """

    def __init__(
        self,
        username: Annotated[str, Form(min_length=1, max_length=100)],
        password: Annotated[str, Form(min_length=1, max_length=128)],
        grant_type: Annotated[str, Form()] = "password",
        scope: Annotated[str | None, Form()] = None,
        client_id: Annotated[str | None, Form()] = None,
        client_secret: Annotated[str | None, Form()] = None,
    ) -> None:
        self.username = username
        self.password = password
        self.grant_type = grant_type
        # el estándar admite que los scopes vengan separados por espacios o por comas
        self.scopes = [parte for parte in (scope or "").replace(",", " ").split() if parte]
        self.client_id = client_id
        self.client_secret = client_secret


@router.post("/token", response_model=TokenSalida, summary="OAuth2: obtener el token con scopes")
def token(datos: Annotated[FormularioToken, Depends()], db: Session = Depends(get_db)) -> dict:
    """Flujo **OAuth2 password grant** (RFC 6749 §4.3), en el propio API.

    Pide `grant_type=password`, `username` y `password` (form-urlencoded). El `scope` es
    opcional: sin él se firman todos los permisos del rol. `client_id`/`client_secret`
    también son opcionales —el SPA es un cliente público—, pero si llegan tienen que ser
    los correctos. Los errores salen con la forma del estándar: `invalid_client`,
    `invalid_grant`, `invalid_scope` y `unsupported_grant_type`.
    """
    if datos.client_id or datos.client_secret:
        autenticado = secrets.compare_digest(datos.client_id or "", config.oauth_client_id) and secrets.compare_digest(
            datos.client_secret or "", config.oauth_client_secret
        )
        if not autenticado:
            raise error_oauth("invalid_client", "client_id o client_secret incorrectos.", estado=status.HTTP_401_UNAUTHORIZED)

    if datos.grant_type != "password":
        raise error_oauth(
            "unsupported_grant_type",
            f"Solo se admite grant_type=password (llegó '{datos.grant_type}').",
            estado=status.HTTP_400_BAD_REQUEST,
        )

    try:
        usuario = _usuario_autenticado(db, datos.username, datos.password)
    except HTTPException as exc:
        raise error_oauth("invalid_grant", str(exc.detail), estado=status.HTTP_400_BAD_REQUEST) from exc

    scopes = revisar(usuario.rol, datos.scopes)
    access_token, _ = crear_token(usuario, scopes)
    log.info("token OAuth2 emitido: %s (rol %s, %s scopes)", usuario.nombre_usuario, usuario.rol, len(scopes))
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": config.access_token_expire_minutes * 60,
        "scope": " ".join(scopes),
    }


@router.get("/yo", response_model=UsuarioSalida)
def yo(usuario: Usuario = Depends(requiere_scope("perfil:leer"))) -> dict:
    """Quién soy: lo usa el SPA para reconstruir la sesión desde el token."""
    return usuario.como_diccionario()
