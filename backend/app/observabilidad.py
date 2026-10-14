# ============================================================
# GS08 · Matrículas y Notas | app/observabilidad.py
# Autor: @dev | Rúbrica: "logging centralizado"
# Logs estructurados en JSON, con el identificador de la petición y el usuario que
# la hizo, y —si hay LOKI_URL— el mismo log se envía a Loki para verlo en Grafana.
# Si Loki no está configurado o no responde, el API sigue funcionando igual: el
# log nunca puede tumbar una petición.
# ============================================================
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from contextvars import ContextVar

import jwt
from pythonjsonlogger import json as jsonlogger
from starlette.middleware.base import BaseHTTPMiddleware

from app import cache, mongo
from app.config import config

# Identificador de la petición en curso (sale en la cabecera X-Request-ID y en cada log).
pedido_id: ContextVar[str] = ContextVar("pedido_id", default="-")
usuario_log: ContextVar[str] = ContextVar("usuario_log", default="-")

log = logging.getLogger("gs08.observabilidad")

CAMPOS = ("asctime", "levelname", "name", "message", "pedido_id", "usuario", "servicio", "entorno")


class FiltroContexto(logging.Filter):
    """Agrega a cada registro el pedido y el usuario que están en curso."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.pedido_id = pedido_id.get()
        record.usuario = usuario_log.get()
        record.servicio = config.servicio
        record.entorno = config.environment
        return True


class ManejadorLoki(logging.Handler):
    """Envía cada registro a Loki por su API HTTP (logging centralizado).

    No usa dependencias externas y falla en silencio: si Loki está caído, el API
    no se entera más que de una advertencia en el primer intento fallido.
    """

    def __init__(self, url: str, servicio: str) -> None:
        super().__init__()
        self.url = url.rstrip("/") + "/loki/api/v1/push"
        self.servicio = servicio
        self.avisado = False

    def emit(self, record: logging.LogRecord) -> None:
        try:
            linea = {
                "momento": self.format(record),
                "nivel": record.levelname,
                "logger": record.name,
                "mensaje": record.getMessage(),
                "pedido_id": getattr(record, "pedido_id", "-"),
                "usuario": getattr(record, "usuario", "-"),
                "entorno": getattr(record, "entorno", config.environment),
            }
            cuerpo = json.dumps(
                {
                    "streams": [
                        {
                            "stream": {"servicio": self.servicio, "nivel": record.levelname},
                            "values": [[str(int(time.time() * 1e9)), json.dumps(linea, ensure_ascii=False)]],
                        }
                    ]
                }
            ).encode("utf-8")
            pedido = urllib.request.Request(self.url, data=cuerpo, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(pedido, timeout=2):  # noqa: S310 (URL propia de la infraestructura)
                pass
            if self.avisado:
                log.info("Loki volvió a responder")
                self.avisado = False
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            if not self.avisado:
                log.warning("no se pudo enviar el log a Loki (%s); se sigue registrando en consola", exc)
                self.avisado = True


def formateador_json() -> jsonlogger.JsonFormatter:
    """Formato único de los logs: JSON con pedido, usuario, servicio y entorno."""
    return jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(pedido_id)s %(usuario)s %(servicio)s %(entorno)s",
        rename_fields={"asctime": "momento", "levelname": "nivel", "name": "logger", "message": "mensaje"},
        json_ensure_ascii=False,
    )


def configurar_logs() -> None:
    """Un solo formato para todo el API: JSON con pedido, usuario, servicio y entorno."""
    manejador = logging.StreamHandler()
    manejador.setFormatter(formateador_json())
    manejador.addFilter(FiltroContexto())

    raiz = logging.getLogger()
    raiz.handlers.clear()
    raiz.addHandler(manejador)
    raiz.setLevel(getattr(logging, config.log_level.upper(), logging.INFO))

    if config.loki_url:
        loki = ManejadorLoki(config.loki_url, config.servicio)
        loki.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        loki.addFilter(FiltroContexto())
        raiz.addHandler(loki)
        log.info("logging centralizado activo", extra={"loki": config.loki_url})

    # Los logs de acceso de uvicorn se suman al mismo formato.
    for nombre in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(nombre).handlers.clear()


METODOS_ESCRITURA = {"POST", "PUT", "PATCH", "DELETE"}
ACCIONES = {"POST": "crear", "PUT": "editar", "PATCH": "editar", "DELETE": "eliminar"}
ENTIDADES = {
    "estudiantes": "estudiante",
    "cursos": "curso",
    "matriculas": "matricula",
    "notas": "nota",
    "usuarios": "usuario",
    "auth": "sesión",
}
# Nunca se guarda en la bitácora nada que se parezca a una credencial.
CAMPOS_OCULTOS = ("password", "clave", "contrasena", "contraseña", "secret", "token")


def _entidad_de(ruta: str) -> str:
    partes = [p for p in ruta.split("/") if p and p not in ("api", "v1")]
    return ENTIDADES.get(partes[0] if partes else "", partes[0] if partes else "otra")


def _identificador_de(ruta: str) -> int | str | None:
    """El último número de la ruta es el id de la entidad (matrícula, nota, estudiante…)."""
    for parte in reversed([p for p in ruta.split("/") if p]):
        if parte.isdigit():
            return int(parte)
    return None


def _sin_credenciales(datos):
    if isinstance(datos, dict):
        return {
            clave: ("***" if any(oculto in clave.lower() for oculto in CAMPOS_OCULTOS) else _sin_credenciales(valor))
            for clave, valor in datos.items()
        }
    if isinstance(datos, list):
        return [_sin_credenciales(elemento) for elemento in datos]
    if isinstance(datos, str):
        return datos[:200]
    return datos


async def _cuerpo_para_la_bitacora(request) -> dict | None:
    """Cuerpo de la petición para la bitácora, ya sin credenciales.

    Entiende JSON y `application/x-www-form-urlencoded`: el endpoint de token de OAuth2
    manda formulario, y sin esto la bitácora guardaría un documento sin datos.
    """
    try:
        crudo = await request.body()
    except Exception:
        return None
    if not crudo:
        return None
    tipo = request.headers.get("content-type", "")
    try:
        if "application/x-www-form-urlencoded" in tipo:
            return _sin_credenciales(dict(urllib.parse.parse_qsl(crudo.decode("utf-8", "replace"))))
        return _sin_credenciales(json.loads(crudo))
    except Exception:
        return None


def _quien_firma(authorization: str | None) -> tuple[str, str]:
    """Usuario y rol del token, para la bitácora. Sin token válido: guiones."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return "-", "-"
    try:
        datos = jwt.decode(authorization.split(" ", 1)[1].strip(), config.secret_key, algorithms=[config.algoritmo_token])
    except Exception:
        return "-", "-"
    return str(datos.get("usuario", "-")), str(datos.get("rol", "-"))


class ContextoPeticion(BaseHTTPMiddleware):
    """Id de petición, una línea de log por petición, y —en las escrituras— la bitácora
    documental (MongoDB) con quién hizo qué, más la invalidación de la caché del panel."""

    async def dispatch(self, request, call_next):  # type: ignore[no-untyped-def]
        identificador = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        pedido_id.set(identificador)
        inventario = request.method in METODOS_ESCRITURA and request.url.path.startswith("/api/v1")
        cuerpo = await _cuerpo_para_la_bitacora(request) if inventario else None
        usuario, rol = _quien_firma(request.headers.get("Authorization"))
        usuario_log.set(usuario)
        arranque = time.perf_counter()
        try:
            respuesta = await call_next(request)
        except Exception:
            demora = (time.perf_counter() - arranque) * 1000
            log.exception("petición fallida en %s %s (%.1f ms)", request.method, request.url.path, demora)
            raise
        demora = (time.perf_counter() - arranque) * 1000
        respuesta.headers["X-Request-ID"] = identificador
        nivel = logging.WARNING if respuesta.status_code >= 400 else logging.INFO
        log.log(
            nivel,
            "%s %s -> %s (%.1f ms)",
            request.method,
            request.url.path,
            respuesta.status_code,
            demora,
            extra={"estado": respuesta.status_code, "demora_ms": round(demora, 1), "ruta": request.url.path},
        )
        if inventario:
            bien = respuesta.status_code < 400
            mongo.registrar(
                ACCIONES.get(request.method, request.method.lower()),
                _entidad_de(request.url.path),
                _identificador_de(request.url.path),
                usuario=usuario,
                datos={
                    "rol": rol,
                    "ruta": request.url.path,
                    "estado": respuesta.status_code,
                    "demora_ms": round(demora, 1),
                    "cuerpo": cuerpo,
                },
                resultado="ok" if bien else f"error {respuesta.status_code}",
                pedido=identificador,
            )
            if bien:
                # Cualquier alta/edición/baja mueve los KPIs del panel: se descarta lo cacheado.
                cache.invalidar_panel()
        return respuesta
