# ============================================================
# GS08 · Matrículas y Notas | app/routers/matriculas.py
# Autor: @dev | T1.3 (listado/uso de la vista) y T2.1/T3.1 | Sprint 1-3
# CU-09..CU-12 / C-16..C-21 y CU-14/CU-15 / C-24..C-29:
#   * el listado lee la VISTA v_matriculas_detalle (no un JOIN paralelo): C-06
#   * periodo AAAA-MM -> 422; estudiante/curso inexistente -> 404
#   * duplicado -> 409 con el mensaje exacto del legacy
#   * retirar es baja lógica (estado='retirado'): sale del KPI, sigue en el historial (C-20)
#   * notas: 0..20, tipo/numero, sin duplicados, y NO se califica una matrícula retirada (RN-14)
#   * boleta: nota del curso = media aritmética; promedio del periodo = ponderado por créditos,
#     redondeado a 2 decimales con ROUND_HALF_UP (numeric(4,2) de PostgreSQL)
# ============================================================
import logging
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import solo_admin, usuario_actual
from app.models import Curso, Estudiante, Matricula, Nota
from app.schemas import (
    Boleta,
    MatriculaActualizar,
    MatriculaEntrada,
    MatriculaSalida,
    NotaEntrada,
    NotaSalida,
    PaginaMatriculas,
    paginas,
)

log = logging.getLogger("gs08.matriculas")
router = APIRouter(prefix="/api/v1/matriculas", tags=["matrículas"])
router_notas = APIRouter(prefix="/api/v1/notas", tags=["notas"])
router_boleta = APIRouter(prefix="/api/v1/estudiantes", tags=["boleta"])

MENSAJE_DUPLICADO = "Ese estudiante ya está matriculado en ese curso para el periodo indicado"
MENSAJE_RETIRADA = "No se registran notas de una matrícula retirada (RN-14)."
MENSAJE_NOTA_DUPLICADA = "Ya existe una nota de ese tipo y número para esa matrícula."

CAMPOS_VISTA = (
    "v.matricula_id AS id, v.periodo, v.fecha_matricula, v.estado_matricula AS estado, "
    "v.estudiante_id, v.codigo_estudiante, v.dni, v.estudiante, v.apellidos_estudiante AS apellidos, "
    "v.nombres_estudiante AS nombres, v.email_estudiante AS email, v.curso_id, v.codigo_curso, "
    "v.curso, v.creditos, v.horas"
)
FILTRO_TEXTO = (
    # unaccent() también sobre `estudiante`: sin esto `q=huaman` devuelve 0 en
    # /matriculas (el apellido del seed es «Huamán») — lo detectó el test de C-21.
    "(unaccent(v.estudiante) ILIKE unaccent(:patron) "
    " OR v.codigo_estudiante ILIKE :patron "
    " OR v.dni ILIKE :patron "
    " OR v.codigo_curso ILIKE :patron "
    " OR unaccent(v.curso) ILIKE unaccent(:patron))"
)


def dos_decimales(valor: Decimal | None) -> Decimal | None:
    return None if valor is None else valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _fila_matricula(db: Session, matricula_id: int) -> dict | None:
    return (
        db.execute(text(f"SELECT {CAMPOS_VISTA} FROM v_matriculas_detalle v WHERE v.matricula_id = :id"), {"id": matricula_id})
        .mappings()
        .first()
    )


@router.get("", response_model=PaginaMatriculas)
def listar(
    q: str | None = Query(default=None, max_length=100, description="estudiante, código, DNI o curso"),
    periodo: str | None = Query(default=None, max_length=7),
    estado: str = Query(default="todos", pattern="^(todos|activa|retirado)$"),
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
    if periodo:
        condiciones.append("v.periodo = :periodo")
        parametros["periodo"] = periodo
    if estado in ("activa", "retirado"):
        condiciones.append("v.estado_matricula = :estado")
        parametros["estado"] = estado
    where = f" WHERE {' AND '.join(condiciones)}" if condiciones else ""

    total = db.execute(text(f"SELECT count(*) FROM v_matriculas_detalle v{where}"), parametros).scalar_one()
    filas = (
        db.execute(
            text(
                f"SELECT {CAMPOS_VISTA} FROM v_matriculas_detalle v{where} ORDER BY v.fecha_matricula DESC, v.matricula_id DESC LIMIT :limite OFFSET :salto"
            ),
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
        "matriculas": [dict(f) for f in filas],
    }


@router.get("/{matricula_id}", response_model=MatriculaSalida)
def obtener(matricula_id: int, db: Session = Depends(get_db), _: object = Depends(usuario_actual)) -> dict:
    fila = _fila_matricula(db, matricula_id)
    if fila is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No existe la matrícula {matricula_id}.")
    return dict(fila)


def _verificar_referencias(db: Session, estudiante_id: int, curso_id: int) -> None:
    """RN-09/C-19: la matrícula apunta a un estudiante y a un curso que existen."""
    if db.get(Estudiante, estudiante_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No existe el estudiante {estudiante_id}.")
    if db.get(Curso, curso_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No existe el curso {curso_id}.")


def _verificar_duplicado(db: Session, estudiante_id: int, curso_id: int, periodo: str, propia_id: int | None = None) -> None:
    # CAST explícito: un parámetro usado como `:propia IS NULL` deja a PostgreSQL sin
    # poder deducir el tipo y la consulta falla con AmbiguousParameter (visto en pytest).
    otra = db.execute(
        text(
            "SELECT id FROM matriculas WHERE estudiante_id = :e AND curso_id = :c AND periodo = :p "
            "AND (CAST(:propia AS integer) IS NULL OR id <> CAST(:propia AS integer))"
        ),
        {"e": estudiante_id, "c": curso_id, "p": periodo, "propia": propia_id},
    ).scalar_one_or_none()
    if otra is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=MENSAJE_DUPLICADO)


@router.post("", response_model=MatriculaSalida, status_code=status.HTTP_201_CREATED)
def crear(datos: MatriculaEntrada, db: Session = Depends(get_db), _: object = Depends(usuario_actual)) -> dict:
    _verificar_referencias(db, datos.estudiante_id, datos.curso_id)
    _verificar_duplicado(db, datos.estudiante_id, datos.curso_id, datos.periodo)
    matricula = Matricula(**datos.model_dump())
    db.add(matricula)
    db.commit()
    db.refresh(matricula)
    log.info("matrícula creada id=%s estudiante=%s curso=%s", matricula.id, datos.estudiante_id, datos.curso_id)
    return dict(_fila_matricula(db, matricula.id))


@router.put("/{matricula_id}", response_model=MatriculaSalida)
def actualizar(
    matricula_id: int,
    datos: MatriculaActualizar,
    db: Session = Depends(get_db),
    _: object = Depends(usuario_actual),
) -> dict:
    matricula = db.get(Matricula, matricula_id)
    if matricula is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No existe la matrícula {matricula_id}.")
    cambios = datos.model_dump(exclude_unset=True)

    estudiante_id = cambios.get("estudiante_id", matricula.estudiante_id)
    curso_id = cambios.get("curso_id", matricula.curso_id)
    periodo = cambios.get("periodo", matricula.periodo)
    if {"estudiante_id", "curso_id", "periodo"} & set(cambios):
        _verificar_referencias(db, estudiante_id, curso_id)
        _verificar_duplicado(db, estudiante_id, curso_id, periodo, propia_id=matricula_id)

    for campo, valor in cambios.items():
        setattr(matricula, campo, valor)
    db.commit()
    return dict(_fila_matricula(db, matricula_id))


@router.delete("/{matricula_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(matricula_id: int, db: Session = Depends(get_db), _: object = Depends(solo_admin)) -> Response:
    matricula = db.get(Matricula, matricula_id)
    if matricula is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No existe la matrícula {matricula_id}.")
    db.delete(matricula)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------
# Notas de una matrícula (CU-14 / C-24..C-26, C-29)
# ------------------------------------------------------------
@router.get("/{matricula_id}/notas", response_model=list[NotaSalida])
def listar_notas(matricula_id: int, db: Session = Depends(get_db), _: object = Depends(usuario_actual)) -> list[dict]:
    if db.get(Matricula, matricula_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No existe la matrícula {matricula_id}.")
    filas = (
        db.execute(
            text(
                "SELECT id, matricula_id, tipo, numero, nota, fecha_registro, observacion "
                "FROM notas WHERE matricula_id = :id ORDER BY tipo, numero"
            ),
            {"id": matricula_id},
        )
        .mappings()
        .all()
    )
    return [
        {
            "id": f["id"],
            "matricula_id": f["matricula_id"],
            "tipo": f["tipo"],
            "numero": f["numero"],
            "nota": float(f["nota"]),
            "nota_texto": f"{f['nota']:.2f}",
            "fecha_registro": f["fecha_registro"],
            "observacion": f["observacion"],
        }
        for f in filas
    ]


@router.post("/{matricula_id}/notas", response_model=NotaSalida, status_code=status.HTTP_201_CREATED)
def registrar_nota(
    matricula_id: int,
    datos: NotaEntrada,
    db: Session = Depends(get_db),
    _: object = Depends(usuario_actual),
) -> dict:
    matricula = db.get(Matricula, matricula_id)
    if matricula is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No existe la matrícula {matricula_id}.")
    if matricula.estado == "retirado":
        # RN-14 (C-26): el trigger de la base lo rechaza igual; aquí se responde con mensaje
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=MENSAJE_RETIRADA)

    duplicada = db.execute(
        text("SELECT id FROM notas WHERE matricula_id = :m AND tipo = :t AND numero = :n"),
        {"m": matricula_id, "t": datos.tipo, "n": datos.numero},
    ).scalar_one_or_none()
    if duplicada is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=MENSAJE_NOTA_DUPLICADA)

    nota = Nota(
        matricula_id=matricula_id,
        tipo=datos.tipo,
        numero=datos.numero,
        nota=datos.nota,
        fecha_registro=datos.fecha_registro or date.today(),
        observacion=datos.observacion,
    )
    db.add(nota)
    db.commit()
    db.refresh(nota)
    return nota.como_diccionario()


@router_notas.put("/{nota_id}", response_model=NotaSalida)
def actualizar_nota(
    nota_id: int,
    datos: NotaEntrada,
    db: Session = Depends(get_db),
    _: object = Depends(usuario_actual),
) -> dict:
    """Corregir una nota ya registrada: se permite aunque la matrícula se haya retirado después (RN-14 solo aplica al INSERT)."""
    nota = db.get(Nota, nota_id)
    if nota is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No existe la nota {nota_id}.")
    duplicada = db.execute(
        text("SELECT id FROM notas WHERE matricula_id = :m AND tipo = :t AND numero = :n AND id <> :id"),
        {"m": nota.matricula_id, "t": datos.tipo, "n": datos.numero, "id": nota_id},
    ).scalar_one_or_none()
    if duplicada is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=MENSAJE_NOTA_DUPLICADA)
    nota.tipo = datos.tipo
    nota.numero = datos.numero
    nota.nota = datos.nota
    if datos.observacion is not None:
        nota.observacion = datos.observacion
    db.commit()
    db.refresh(nota)
    return nota.como_diccionario()


@router_notas.delete("/{nota_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_nota(nota_id: int, db: Session = Depends(get_db), _: object = Depends(usuario_actual)) -> Response:
    nota = db.get(Nota, nota_id)
    if nota is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No existe la nota {nota_id}.")
    db.delete(nota)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------
# Boleta del periodo (CU-15 / C-27, C-28)
# ------------------------------------------------------------
@router_boleta.get("/{estudiante_id}/boleta", response_model=Boleta)
def boleta(
    estudiante_id: int,
    periodo: str = Query(min_length=7, max_length=7),
    db: Session = Depends(get_db),
    _: object = Depends(usuario_actual),
) -> dict:
    estudiante = db.get(Estudiante, estudiante_id)
    if estudiante is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No existe el estudiante {estudiante_id}.")

    filas = (
        db.execute(
            text(
                "SELECT v.matricula_id, v.curso_id, v.codigo_curso, v.curso, v.creditos, "
                "       n.id AS nota_id, n.tipo, n.numero, n.nota, n.fecha_registro, n.observacion "
                "FROM v_matriculas_detalle v "
                "LEFT JOIN notas n ON n.matricula_id = v.matricula_id "
                "WHERE v.estudiante_id = :id AND v.periodo = :periodo "
                "ORDER BY v.curso, n.tipo, n.numero, n.id"
            ),
            {"id": estudiante_id, "periodo": periodo},
        )
        .mappings()
        .all()
    )

    cursos: list[dict] = []
    por_matricula: dict[int, dict] = {}
    for fila in filas:
        curso = por_matricula.get(fila["matricula_id"])
        if curso is None:
            curso = {
                "matricula_id": fila["matricula_id"],
                "curso_id": fila["curso_id"],
                "codigo_curso": fila["codigo_curso"],
                "curso": fila["curso"],
                "creditos": fila["creditos"],
                "notas": [],
                "suma": Decimal("0"),
            }
            por_matricula[fila["matricula_id"]] = curso
            cursos.append(curso)
        if fila["nota_id"] is not None:
            curso["notas"].append(
                {
                    "id": fila["nota_id"],
                    "matricula_id": fila["matricula_id"],
                    "tipo": fila["tipo"],
                    "numero": fila["numero"],
                    "nota": float(fila["nota"]),
                    "nota_texto": f"{fila['nota']:.2f}",
                    "fecha_registro": fila["fecha_registro"],
                    "observacion": fila["observacion"],
                }
            )
            curso["suma"] += Decimal(fila["nota"])

    salida_cursos: list[dict] = []
    suma_ponderada = Decimal("0")
    creditos_con_notas = 0
    notas_de_curso: list[Decimal] = []
    for curso in cursos:
        cantidad = len(curso["notas"])
        nota_curso = None
        if cantidad:
            nota_curso = dos_decimales(curso["suma"] / cantidad)
            suma_ponderada += nota_curso * curso["creditos"]
            creditos_con_notas += curso["creditos"]
            notas_de_curso.append(nota_curso)
        salida_cursos.append(
            {
                "curso_id": curso["curso_id"],
                "codigo_curso": curso["codigo_curso"],
                "curso": curso["curso"],
                "creditos": curso["creditos"],
                "cantidad_notas": cantidad,
                "nota": float(nota_curso) if nota_curso is not None else None,
                "nota_texto": f"{nota_curso:.2f}" if nota_curso is not None else None,
                "notas": curso["notas"],
            }
        )

    promedio = dos_decimales(suma_ponderada / creditos_con_notas) if creditos_con_notas else None
    promedio_simple = dos_decimales(sum(notas_de_curso) / len(notas_de_curso)) if notas_de_curso else None
    return {
        "estudiante": estudiante.como_diccionario(),
        "periodo": periodo,
        "cursos": salida_cursos,
        "creditos_con_notas": creditos_con_notas,
        "promedio": float(promedio) if promedio is not None else None,
        "promedio_texto": f"{promedio:.2f}" if promedio is not None else None,
        "promedio_simple": float(promedio_simple) if promedio_simple is not None else None,
    }
