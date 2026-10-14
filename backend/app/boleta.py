# ============================================================
# GS08 · Matrículas y Notas | app/boleta.py
# Autor: @dev | CU-15 / C-27, C-28
# El cálculo de la boleta vive aquí y lo usan las DOS puertas de entrada:
#   REST     -> GET /api/v1/estudiantes/{id}/boleta       (app/routers/matriculas.py)
#   GraphQL  -> consulta boleta(estudianteId, periodo)    (app/graphql.py)
# Una sola fórmula del promedio ponderado por créditos: si hubiera dos copias,
# tarde o temprano darían números distintos (el mismo motivo que la decisión D-14).
# ============================================================
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import Estudiante


def dos_decimales(valor: Decimal | None) -> Decimal | None:
    return None if valor is None else valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular(db: Session, estudiante_id: int, periodo: str) -> dict | None:
    """Boleta del periodo: notas por curso, promedio ponderado por créditos y promedio simple.

    Devuelve None si el estudiante no existe: el llamador decide si es 404 (REST) o null (GraphQL).
    Sale de la VISTA v_matriculas_detalle, no de conteos paralelos.
    """
    estudiante = db.get(Estudiante, estudiante_id)
    if estudiante is None:
        return None

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
