# ============================================================
# GS08 · Matrículas y Notas | app/routers/dashboard.py
# Autor: @dev | T1.4 | Sprint 1
# CU-02 / C-05, C-06, C-07: 4 KPIs + top 5 de cursos con matrículas activas +
# últimos 6 estudiantes. El top sale de la VISTA v_matriculas_detalle (no de un
# conteo paralelo) y su suma es ≤ matrículas activas — que es lo que se comprueba.
# Sin matrículas responde 200 con `top_cursos: []` (no es error).
# ============================================================
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import usuario_actual
from app.schemas import Panel

router = APIRouter(prefix="/api/v1/dashboard", tags=["panel"])

CAMPOS_ESTUDIANTE = (
    "e.id, e.codigo, e.dni, e.nombres, e.apellidos, e.email, e.telefono, e.fecha_nacimiento, e.direccion, e.estado, e.creado_en"
)


@router.get("", response_model=Panel)
def panel(db: Session = Depends(get_db), _: object = Depends(usuario_actual)) -> dict:
    conteos = (
        db.execute(
            text(
                "SELECT (SELECT count(*) FROM estudiantes WHERE estado IS TRUE) AS estudiantes_activos, "
                "       (SELECT count(*) FROM cursos     WHERE estado IS TRUE) AS cursos_activos, "
                "       (SELECT count(*) FROM matriculas WHERE estado = 'activa') AS matriculas_activas, "
                "       (SELECT count(*) FROM usuarios   WHERE estado IS TRUE) AS usuarios_activos"
            )
        )
        .mappings()
        .one()
    )

    top = (
        db.execute(
            text(
                "SELECT curso_id, codigo_curso AS codigo, curso, creditos, count(*) AS matriculas "
                "FROM v_matriculas_detalle WHERE estado_matricula = 'activa' "
                "GROUP BY curso_id, codigo_curso, curso, creditos "
                "ORDER BY matriculas DESC, curso LIMIT 5"
            )
        )
        .mappings()
        .all()
    )

    ultimos = (
        db.execute(text(f"SELECT {CAMPOS_ESTUDIANTE} FROM estudiantes e ORDER BY e.creado_en DESC, e.id DESC LIMIT 6"))
        .mappings()
        .all()
    )

    return {
        "estudiantes_activos": conteos["estudiantes_activos"],
        "cursos_activos": conteos["cursos_activos"],
        "matriculas_activas": conteos["matriculas_activas"],
        "usuarios_activos": conteos["usuarios_activos"],
        "top_cursos": [dict(f) for f in top],
        "ultimos_estudiantes": [{**dict(f), "nombre_completo": f"{f['apellidos']}, {f['nombres']}"} for f in ultimos],
    }
