# ============================================================
# GS08 · Matrículas y Notas | app/security.py
# Autor: @dev | T1.1 / T1.2 | Sprint 1
# Contraseñas con bcrypt y sesión con JWT HS256.
#
# El hash del seed se verifica TAL CUAL, incluido el prefijo `$2y$` del legacy:
# está comprobado con bcrypt 4.2.1 (docs/analisis/modelo-datos.md §6.1 y
# docs/analisis/evidencia/hash-legacy-python-bcrypt.txt). No se regenera: así el
# admin del legacy entra con la misma contraseña y la trazabilidad se conserva.
# ============================================================
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import HTTPException, status

from app.config import config

CABECERA_401 = {"WWW-Authenticate": "Bearer"}


def verificar_password(password: str, hash_guardado: str) -> bool:
    """True si la contraseña corresponde al hash bcrypt guardado ($2a$/$2b$/$2y$)."""
    if not password or not hash_guardado:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hash_guardado.encode("utf-8"))
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException:
        # bcrypt 4.x es Rust: con un hash mal formado lanza pyo3_runtime.PanicException,
        # que NO hereda de Exception. Se trata como credencial inválida, nunca como 500.
        # Medido en pytest (tests/test_auth.py::test_c03_un_hash_corrupto_no_provoca_500).
        return False


def generar_hash(password: str) -> str:
    """Hash bcrypt coste 10 para usuarios nuevos (mismo coste que el seed, RN-01)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=10)).decode("utf-8")


def crear_token(usuario) -> tuple[str, datetime]:
    ahora = datetime.now(UTC)
    expira = ahora + timedelta(minutes=config.access_token_expire_minutes)
    payload = {
        "sub": str(usuario.id),
        "usuario": usuario.nombre_usuario,
        "rol": usuario.rol,
        "iat": int(ahora.timestamp()),
        "exp": expira,
    }
    token = jwt.encode(payload, config.secret_key, algorithm=config.algoritmo_token)
    return token, expira


def leer_token(token: str) -> dict:
    try:
        return jwt.decode(token, config.secret_key, algorithms=[config.algoritmo_token])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión expiró. Vuelve a iniciar sesión.",
            headers=CABECERA_401,
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token de sesión no es válido.",
            headers=CABECERA_401,
        ) from exc
