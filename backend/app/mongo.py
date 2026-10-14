# ============================================================
# GS08 · Matrículas y Notas | app/mongo.py
# Autor: @dev | Rúbrica: "bases de datos híbridas (PostgreSQL + MongoDB)"
# Segunda base, documental, para lo que no es tabular:
#   bitacora         -> auditoría de cada alta, edición y baja (quién, qué, cuándo, con qué datos)
#   boletas_snapshot -> la boleta calculada se guarda como documento para consultarla después
# Si no hay MONGO_URL o Mongo no responde, el API funciona igual (solo no audita):
# se registra la advertencia una vez y se sigue.
# ============================================================
import logging
from datetime import UTC, datetime
from typing import Any

from pymongo import ASCENDING, DESCENDING, MongoClient

from app.config import config

log = logging.getLogger("gs08.mongo")

COLECCION_BITACORA = "bitacora"
COLECCION_BOLETAS = "boletas_snapshot"

_cliente: Any = None
_base: Any = None
_deshabilitado = False


def base():
    """Devuelve la base documental o None si está apagada."""
    global _cliente, _base, _deshabilitado
    if _base is not None or _deshabilitado:
        return _base
    if not config.mongo_url:
        _deshabilitado = True
        log.info("bitácora apagada (sin MONGO_URL)")
        return None
    try:
        conexion = MongoClient(config.mongo_url, serverSelectionTimeoutMS=1500, tz_aware=True)
        conexion.admin.command("ping")
        _cliente = conexion
        _base = conexion[config.mongo_bd]
        _preparar_indices(_base)
        log.info("segunda base conectada", extra={"base": config.mongo_bd})
    except Exception as exc:
        _deshabilitado = True
        log.warning("bitácora apagada: Mongo no responde (%s)", exc)
    return _base


def _preparar_indices(una_base) -> None:
    una_base[COLECCION_BITACORA].create_index([("fecha", DESCENDING)])
    una_base[COLECCION_BITACORA].create_index([("entidad", ASCENDING), ("fecha", DESCENDING)])
    una_base[COLECCION_BOLETAS].create_index([("estudiante_id", ASCENDING), ("periodo", ASCENDING)], unique=True)


def forzar(conexion: Any, una_base: Any = None) -> None:
    """Para las pruebas: inyecta un cliente/base (o None para apagarla)."""
    global _cliente, _base, _deshabilitado
    _cliente = conexion
    _base = una_base if una_base is not None else (conexion[config.mongo_bd] if conexion is not None else None)
    _deshabilitado = _base is None


def reiniciar() -> None:
    global _cliente, _base, _deshabilitado
    _cliente = None
    _base = None
    _deshabilitado = False


def activa() -> bool:
    return base() is not None


def registrar(
    accion: str,
    entidad: str,
    entidad_id: Any = None,
    usuario: str | None = None,
    datos: dict | None = None,
    resultado: str = "ok",
    pedido: str | None = None,
) -> str | None:
    """Deja constancia de una operación. Devuelve el id del documento o None si está apagada."""
    una_base = base()
    if una_base is None:
        return None
    documento = {
        "fecha": datetime.now(UTC),
        "accion": accion,
        "entidad": entidad,
        "entidad_id": entidad_id,
        "usuario": usuario or "-",
        "resultado": resultado,
        "pedido_id": pedido,
        "datos": datos or {},
    }
    try:
        return str(una_base[COLECCION_BITACORA].insert_one(documento).inserted_id)
    except Exception as exc:
        log.warning("no se pudo escribir en la bitácora (%s)", exc)
        return None


def guardar_boleta(estudiante_id: int, periodo: str, documento: dict, usuario: str | None = None) -> bool:
    """Guarda (o reemplaza) la boleta calculada como documento."""
    una_base = base()
    if una_base is None:
        return False
    registro = {
        "estudiante_id": estudiante_id,
        "periodo": periodo,
        "generado_en": datetime.now(UTC),
        "generado_por": usuario or "-",
        "boleta": documento,
    }
    try:
        una_base[COLECCION_BOLETAS].replace_one({"estudiante_id": estudiante_id, "periodo": periodo}, registro, upsert=True)
        return True
    except Exception as exc:
        log.warning("no se pudo guardar la boleta (%s)", exc)
        return False


def boleta_guardada(estudiante_id: int, periodo: str) -> dict | None:
    una_base = base()
    if una_base is None:
        return None
    try:
        documento = una_base[COLECCION_BOLETAS].find_one({"estudiante_id": estudiante_id, "periodo": periodo}, {"_id": 0})
    except Exception as exc:
        log.warning("no se pudo leer la boleta guardada (%s)", exc)
        return None
    if documento and documento.get("generado_en"):
        documento["generado_en"] = documento["generado_en"].isoformat()
    return documento


def listar(entidad: str | None = None, accion: str | None = None, limite: int = 50) -> list[dict]:
    una_base = base()
    if una_base is None:
        return []
    filtro: dict[str, Any] = {}
    if entidad:
        filtro["entidad"] = entidad
    if accion:
        filtro["accion"] = accion
    try:
        documentos = una_base[COLECCION_BITACORA].find(filtro, {"_id": 0}).sort("fecha", DESCENDING).limit(limite)
        salida = []
        for documento in documentos:
            if documento.get("fecha") is not None:
                documento["fecha"] = documento["fecha"].isoformat()
            salida.append(documento)
        return salida
    except Exception as exc:
        log.warning("no se pudo leer la bitácora (%s)", exc)
        return []


def total() -> int:
    una_base = base()
    if una_base is None:
        return 0
    try:
        return int(una_base[COLECCION_BITACORA].estimated_document_count())
    except Exception:
        return 0


def contar(entidad: str | None = None, accion: str | None = None) -> int:
    """Cuántos documentos coinciden con el filtro (lo que el panel de auditoría muestra)."""
    una_base = base()
    if una_base is None:
        return 0
    filtro: dict[str, Any] = {}
    if entidad:
        filtro["entidad"] = entidad
    if accion:
        filtro["accion"] = accion
    try:
        return int(una_base[COLECCION_BITACORA].count_documents(filtro))
    except Exception as exc:
        log.warning("no se pudo contar la bitácora (%s)", exc)
        return 0
