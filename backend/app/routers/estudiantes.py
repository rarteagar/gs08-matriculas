# ============================================================
# GS08 · Matrículas y Notas | app/routers/estudiantes.py
# Autor: @dev | T1.3 | Sprint 1
# CU-03..CU-06 / C-08..C-12:
#   * buscador por código, DNI, nombres o apellidos, sin distinguir mayúsculas
#     NI tildes: ILIKE + unaccent (BUG-07 de @qa; con LIKE daría 0 — modelo-datos.md §6.3)
#   * listado paginado con `total` (page_size 1..100: 0 y 200 -> 422)
#   * alta/edición con 422 y el campo en el mensaje, nunca 500
#   * baja lógica con estado=false (el registro se conserva)
#   * DELETE con matrículas -> 409 con el conteo; con ?confirmar=true -> 204 (C-30..C-32)
# ============================================================
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import solo_admin, usuario_actual
from app.models import Estudiante
from app.schemas import EstudianteEntrada, EstudianteSalida, PaginaEstudiantes, paginas

log = logging.getLogger("gs08.estudiantes")
router = APIRouter(prefix="/api/v1/estudiantes", tags=["estudiantes"])

CAMPOS = (
    "e.id, e.codigo, e.dni, e.nombres, e.apellidos, e.email, e.telefono, e.fecha_nacimiento, e.direccion, e.estado, e.creado_en"
)
# unaccent() es lo que hace que `huaman` encuentre `Huamán` (C-08)
FILTRO_TEXTO = (
    "(e.codigo ILIKE :patron "
    " OR e.dni ILIKE :patron "
    " OR unaccent(e.nombres) ILIKE unaccent(:patron) "
    " OR unaccent(e.apellidos) ILIKE unaccent(:patron))"
)


def _fila_a_salida(fila) -> dict:
    datos = dict(fila)
    datos["nombre_completo"] = f"{datos['apellidos']}, {datos['nombres']}"
    return datos


@router.get("", response_model=PaginaEstudiantes)
def listar(
    q: str | None = Query(default=None, max_length=100, description="código, DNI, nombres o apellidos"),
    estado: str = Query(default="todos", pattern="^(todos|activo|inactivo)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    _: object = Depends(usuario_actual),
) -> dict:
    condiciones: list[str] = []
    parametros: dict = {"limite": page_size, "salto": (page - 1) * page_size}
    if q and q.strip():
        condiciones.append(FILTRO_TEXTO)
        parametros["patron"] = f"%{q.strip()}%"
    if estado == "activo":
        condiciones.append("e.estado IS TRUE")
    elif estado == "inactivo":
        condiciones.append("e.estado IS FALSE")
    where = f" WHERE {' AND '.join(condiciones)}" if condiciones else ""

    total = db.execute(text(f"SELECT count(*) FROM estudiantes e{where}"), parametros).scalar_one()
    filas = (
        db.execute(
            text(f"SELECT {CAMPOS} FROM estudiantes e{where} ORDER BY e.apellidos, e.nombres, e.id LIMIT :limite OFFSET :salto"),
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
        "estudiantes": [_fila_a_salida(f) for f in filas],
    }


@router.get("/{estudiante_id}", response_model=EstudianteSalida)
def obtener(estudiante_id: int, db: Session = Depends(get_db), _: object = Depends(usuario_actual)) -> dict:
    fila = db.execute(text(f"SELECT {CAMPOS} FROM estudiantes e WHERE e.id = :id"), {"id": estudiante_id}).mappings().first()
    if fila is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No existe el estudiante {estudiante_id}.")
    return _fila_a_salida(fila)


def _verificar_duplicados(db: Session, datos: EstudianteEntrada, propio_id: int | None = None) -> None:
    """422 con el campo en el mensaje (C-11). La base lo vuelve a rechazar por UNIQUE."""
    fila = (
        db.execute(
            text("SELECT id, dni, codigo FROM estudiantes WHERE dni = :dni OR codigo = :codigo"),
            {"dni": datos.dni, "codigo": datos.codigo},
        )
        .mappings()
        .all()
    )
    for otra in fila:
        if propio_id is not None and otra["id"] == propio_id:
            continue
        if otra["dni"] == datos.dni:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="dni: Ya existe un estudiante con ese DNI."
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="codigo: Ya existe un estudiante con ese código."
        )


@router.post("", response_model=EstudianteSalida, status_code=status.HTTP_201_CREATED)
def crear(datos: EstudianteEntrada, db: Session = Depends(get_db), _: object = Depends(usuario_actual)) -> dict:
    _verificar_duplicados(db, datos)
    estudiante = Estudiante(**datos.model_dump())
    db.add(estudiante)
    db.commit()
    db.refresh(estudiante)
    log.info("estudiante creado id=%s codigo=%s", estudiante.id, estudiante.codigo)
    return estudiante.como_diccionario()


@router.put("/{estudiante_id}", response_model=EstudianteSalida)
def actualizar(
    estudiante_id: int,
    datos: EstudianteEntrada,
    db: Session = Depends(get_db),
    _: object = Depends(usuario_actual),
) -> dict:
    estudiante = db.get(Estudiante, estudiante_id)
    if estudiante is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No existe el estudiante {estudiante_id}.")
    _verificar_duplicados(db, datos, propio_id=estudiante_id)
    for campo, valor in datos.model_dump().items():
        setattr(estudiante, campo, valor)
    db.commit()
    db.refresh(estudiante)
    return estudiante.como_diccionario()


@router.delete("/{estudiante_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(
    estudiante_id: int,
    confirmar: bool = Query(default=False, description="segunda llamada explícita: borra el estudiante y sus matrículas"),
    db: Session = Depends(get_db),
    _: object = Depends(solo_admin),
) -> Response:
    """C-30/C-31/C-32: primero 409 con el conteo, y solo con ?confirmar=true borra en cascada."""
    estudiante = db.get(Estudiante, estudiante_id)
    if estudiante is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No existe el estudiante {estudiante_id}.")

    matriculas = db.execute(text("SELECT count(*) FROM matriculas WHERE estudiante_id = :id"), {"id": estudiante_id}).scalar_one()
    if matriculas and not confirmar:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": (
                    f"{estudiante.apellidos}, {estudiante.nombres} tiene {matriculas} matrícula(s). "
                    "La base las borraría en cascada: repite la llamada con ?confirmar=true si es lo que quieres."
                ),
                "matriculas": matriculas,
            },
        )
    db.delete(estudiante)
    db.commit()
    log.warning("estudiante %s eliminado (matrículas borradas en cascada: %s)", estudiante_id, matriculas)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
