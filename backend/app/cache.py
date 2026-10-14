# ============================================================
# GS08 · Matrículas y Notas | app/cache.py
# Autor: @dev | Rúbrica: "optimización con caching distribuido (Redis)"
# Caché de las respuestas caras (el panel) con TTL e invalidación explícita cuando
# cambian los datos. Si no hay REDIS_URL o Redis no responde, el API responde igual
# (solo que sin caché): la caché nunca puede ser un punto único de falla.
# ============================================================
import json
import logging
import time
from typing import Any

import redis

from app.config import config

log = logging.getLogger("gs08.cache")

# Igual que la bitácora: un fallo al primer uso no apaga la caché para siempre.
ENFRIAMIENTO_SEGUNDOS = 30

_cliente: Any = None
_deshabilitado = False
_enfriamiento = 0.0
CLAVE_PANEL = "gs08:panel"


def cliente():
    """Devuelve el cliente de Redis o None si la caché está apagada."""
    global _cliente, _deshabilitado, _enfriamiento
    if _cliente is not None:
        return _cliente
    if not config.redis_url:
        _deshabilitado = True
        _enfriamiento = float("inf")
        log.info("caché apagada (sin REDIS_URL)")
        return None
    if _deshabilitado and time.monotonic() < _enfriamiento:
        return None
    try:
        conexion = redis.Redis.from_url(
            config.redis_url,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        conexion.ping()
        _cliente = conexion
        _deshabilitado = False
        log.info("caché conectada", extra={"servidor": config.redis_url})
    except Exception as exc:  # redis.exceptions.RedisError y problemas de red
        _deshabilitado = True
        _enfriamiento = time.monotonic() + ENFRIAMIENTO_SEGUNDOS
        log.warning("caché apagada: Redis no responde (%s); se reintenta en %s s", exc, ENFRIAMIENTO_SEGUNDOS)
    return _cliente


def forzar(conexion: Any) -> None:
    """Para las pruebas: inyecta un cliente (o None para apagarla)."""
    global _cliente, _deshabilitado, _enfriamiento
    _cliente = conexion
    _deshabilitado = conexion is None
    _enfriamiento = 0.0


def reiniciar() -> None:
    global _cliente, _deshabilitado, _enfriamiento
    _cliente = None
    _deshabilitado = False
    _enfriamiento = 0.0


def activa() -> bool:
    return cliente() is not None


def obtener(clave: str):
    conexion = cliente()
    if conexion is None:
        return None
    try:
        crudo = conexion.get(clave)
    except Exception as exc:
        log.warning("falló la lectura de la caché (%s)", exc)
        return None
    if crudo is None:
        return None
    try:
        return json.loads(crudo)
    except ValueError:
        return None


def guardar(clave: str, valor, ttl: int | None = None) -> bool:
    conexion = cliente()
    if conexion is None:
        return False
    try:
        conexion.set(clave, json.dumps(valor, ensure_ascii=False, default=str), ex=ttl or config.cache_ttl_segundos)
        return True
    except Exception as exc:
        log.warning("falló la escritura en la caché (%s)", exc)
        return False


def borrar(*claves: str) -> int:
    conexion = cliente()
    if conexion is None or not claves:
        return 0
    try:
        return conexion.delete(*claves)
    except Exception as exc:
        log.warning("falló el borrado en la caché (%s)", exc)
        return 0


def invalidar_panel() -> None:
    """Se llama en toda operación que cambia estudiantes, cursos, matrículas o notas."""
    if activa():
        borrar(CLAVE_PANEL)
