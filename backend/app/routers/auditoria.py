# ============================================================
# GS08 · Matrículas y Notas | app/routers/auditoria.py
# Autor: @dev | Rúbrica: "bases de datos híbridas"
# Lectura de la bitácora que vive en la segunda base (MongoDB). Solo el rol admin.
# Si la bitácora está apagada, responde 200 con activo=false y sin items: es más
# honesto decir "no está activa" que devolver un error o una lista vacía mentirosa.
# ============================================================
from fastapi import APIRouter, Depends, Query

from app import mongo
from app.deps import solo_admin
from app.models import Usuario

router = APIRouter(prefix="/api/v1/auditoria", tags=["auditoría"])


@router.get("")
def listar_bitacora(
    entidad: str | None = Query(default=None, description="estudiante, curso, matricula, nota o usuario"),
    accion: str | None = Query(default=None, description="crear, editar o eliminar"),
    limite: int = Query(default=25, ge=1, le=200),
    _: Usuario = Depends(solo_admin),
) -> dict:
    """Últimas operaciones registradas en la bitácora documental.

    `total` es lo que coincide con el filtro; `total_bitacora` es todo lo guardado.
    En las altas (POST) el identificador del recurso aún no existe en la ruta: queda
    en el cuerpo del documento (código, DNI, etc.) porque la base lo asigna después.
    """
    activo = mongo.activa()
    if not activo:
        return {
            "activa": False,
            "total": 0,
            "total_bitacora": 0,
            "items": [],
            "detalle": "La bitácora documental está apagada (sin MONGO_URL en el API).",
        }
    return {
        "activa": True,
        "total": mongo.contar(entidad=entidad, accion=accion),
        "total_bitacora": mongo.total(),
        "items": mongo.listar(entidad=entidad, accion=accion, limite=limite),
        "detalle": None,
    }
