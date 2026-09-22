# ============================================================
# GS08 · Matrículas y Notas | app/routers/cursos.py
# Autor: @dev | T1.3 | Sprint 1
# CU-07/CU-08 / C-13..C-15:
#   * creditos 1..10 (0 y 11 -> 422), horas 1..1000; sin enviar -> 3 / 48 (default del legacy)
#   * código repetido -> 409
#   * baja lógica con estado=false; el inactivo no aparece en el selector de matrícula
#   * DELETE con matrículas -> 409 con el conteo; con ?confirmar=true -> 204
# ============================================================
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import solo_admin, usuario_actual
from app.models import Curso
from app.schemas import CursoEntrada, CursoSalida, PaginaCursos, paginas

log = logging.getLogger("gs08.cursos")
router = APIRouter(prefix="/api/v1/cursos", tags=["cursos"])

CAMPOS = "c.id, c.codigo, c.nombre, c.descripcion, c.creditos, c.horas, c.estado, c.creado_en"


@router.get("", response_model=PaginaCursos)
def listar(
    q: str | None = Query(default=None, max_length=100),
    estado: str = Query(default="todos", pattern="^(todos|activo|inactivo)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    _: object = Depends(usuario_actual),
) -> dict:
    condiciones: list[str] = []
    parametros: dict = {"limite": page_size, "salto": (page - 1) * page_size}
    if q and q.strip():
        condiciones.append("(c.codigo ILIKE :patron OR unaccent(c.nombre) ILIKE unaccent(:patron))")
        parametros["patron"] = f"%{q.strip()}%"
    if estado == "activo":
        condiciones.append("c.estado IS TRUE")
    elif estado == "inactivo":
        condiciones.append("c.estado IS FALSE")
    where = f" WHERE {' AND '.join(condiciones)}" if condiciones else ""

    total = db.execute(text(f"SELECT count(*) FROM cursos c{where}"), parametros).scalar_one()
    filas = (
        db.execute(
            text(f"SELECT {CAMPOS} FROM cursos c{where} ORDER BY c.nombre, c.id LIMIT :limite OFFSET :salto"),
            parametros,
        )
        .mappings()
        .all()
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "paginas": paginas(total, page_size),
        "cursos": [dict(f) for f in filas],
    }


@router.get("/{curso_id}", response_model=CursoSalida)
def obtener(curso_id: int, db: Session = Depends(get_db), _: object = Depends(usuario_actual)) -> dict:
    fila = db.execute(text(f"SELECT {CAMPOS} FROM cursos c WHERE c.id = :id"), {"id": curso_id}).mappings().first()
    if fila is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No existe el curso {curso_id}.")
    return dict(fila)


@router.post("", response_model=CursoSalida, status_code=status.HTTP_201_CREATED)
def crear(datos: CursoEntrada, db: Session = Depends(get_db), _: object = Depends(usuario_actual)) -> dict:
    repetido = db.execute(text("SELECT id FROM cursos WHERE codigo = :codigo"), {"codigo": datos.codigo}).scalar_one_or_none()
    if repetido is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un curso con ese código.")
    curso = Curso(**datos.model_dump())
    db.add(curso)
    db.commit()
    db.refresh(curso)
    log.info("curso creado id=%s codigo=%s", curso.id, curso.codigo)
    return curso.como_diccionario()


@router.put("/{curso_id}", response_model=CursoSalida)
def actualizar(
    curso_id: int,
    datos: CursoEntrada,
    db: Session = Depends(get_db),
    _: object = Depends(usuario_actual),
) -> dict:
    curso = db.get(Curso, curso_id)
    if curso is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No existe el curso {curso_id}.")
    repetido = db.execute(
        text("SELECT id FROM cursos WHERE codigo = :codigo AND id <> :id"), {"codigo": datos.codigo, "id": curso_id}
    ).scalar_one_or_none()
    if repetido is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un curso con ese código.")
    for campo, valor in datos.model_dump().items():
        setattr(curso, campo, valor)
    db.commit()
    db.refresh(curso)
    return curso.como_diccionario()


@router.delete("/{curso_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(
    curso_id: int,
    confirmar: bool = Query(default=False),
    db: Session = Depends(get_db),
    _: object = Depends(solo_admin),
) -> Response:
    curso = db.get(Curso, curso_id)
    if curso is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No existe el curso {curso_id}.")

    matriculas = db.execute(text("SELECT count(*) FROM matriculas WHERE curso_id = :id"), {"id": curso_id}).scalar_one()
    if matriculas and not confirmar:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": (
                    f"{curso.nombre} tiene {matriculas} matrícula(s). "
                    "La base las borraría en cascada: repite la llamada con ?confirmar=true si es lo que quieres."
                ),
                "matriculas": matriculas,
            },
        )
    db.delete(curso)
    db.commit()
    log.warning("curso %s eliminado (matrículas borradas en cascada: %s)", curso_id, matriculas)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
