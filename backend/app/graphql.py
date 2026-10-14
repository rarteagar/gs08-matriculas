# ============================================================
# GS08 · Matrículas y Notas | app/graphql.py
# Autor: @dev | Rúbrica: "API REST y GraphQL"
# La segunda puerta de entrada al MISMO modelo de datos: mismas vistas, mismas
# consultas y la misma fórmula de boleta (app/boleta.py) que el API REST.
#   POST /graphql   -> consultas (GraphiQL en el navegador)
# Exige token igual que el REST: sin cabecera Authorization responde 401.
# ============================================================
from typing import Annotated

import strawberry
from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from strawberry.fastapi import GraphQLRouter

from app.boleta import calcular
from app.db import SesionLocal
from app.deps import usuario_actual

CAMPOS_ESTUDIANTE = "e.id, e.codigo, e.dni, e.nombres, e.apellidos, e.email, e.telefono, e.estado"


@strawberry.type(description="Una nota registrada en una matrícula")
class NotaG:
    id: int
    tipo: str
    numero: int
    nota: float
    nota_texto: str
    observacion: str | None = None


@strawberry.type(description="Curso del catálogo")
class CursoG:
    id: int
    codigo: str
    nombre: str
    creditos: int
    horas: int | None = None
    estado: bool


@strawberry.type(description="Fila del ranking de cursos con más matrículas activas")
class CursoTopG:
    curso_id: int
    codigo: str
    curso: str
    creditos: int
    matriculas: int


@strawberry.type(description="Estudiante")
class EstudianteG:
    id: int
    codigo: str
    dni: str
    nombre_completo: str
    email: str | None = None
    telefono: str | None = None
    estado: bool


@strawberry.type(description="Matrícula con sus notas")
class MatriculaG:
    id: int
    periodo: str
    estado: str
    curso_id: int
    codigo_curso: str
    curso: str
    creditos: int
    notas: list[NotaG]


@strawberry.type(description="Curso dentro de la boleta")
class CursoBoletaG:
    curso_id: int
    codigo_curso: str
    curso: str
    creditos: int
    cantidad_notas: int
    nota: float | None = None


@strawberry.type(description="Boleta del periodo: promedio ponderado por créditos")
class BoletaG:
    estudiante: EstudianteG
    periodo: str
    cursos: list[CursoBoletaG]
    creditos_con_notas: int
    promedio: float | None = None
    promedio_texto: str | None = None
    promedio_simple: float | None = None


@strawberry.type(description="KPIs del panel")
class PanelG:
    estudiantes_activos: int
    cursos_activos: int
    matriculas_activas: int
    usuarios_activos: int
    top_cursos: list[CursoTopG]
    ultimos_estudiantes: list[EstudianteG]


def _estudiante(fila) -> EstudianteG:
    return EstudianteG(
        id=fila["id"],
        codigo=fila["codigo"],
        dni=fila["dni"],
        nombre_completo=f"{fila['apellidos']}, {fila['nombres']}",
        email=fila["email"],
        telefono=fila["telefono"],
        estado=bool(fila["estado"]),
    )


@strawberry.type(description="Consultas del GS08: la misma información que el API REST")
class Consulta:
    @strawberry.field(description="Los 4 KPIs, el top de cursos y los últimos estudiantes")
    def panel(self, info: strawberry.Info) -> PanelG:
        db: Session = info.context["db"]
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
                    "GROUP BY curso_id, codigo_curso, curso, creditos ORDER BY matriculas DESC, curso LIMIT 5"
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
        return PanelG(
            estudiantes_activos=conteos["estudiantes_activos"],
            cursos_activos=conteos["cursos_activos"],
            matriculas_activas=conteos["matriculas_activas"],
            usuarios_activos=conteos["usuarios_activos"],
            top_cursos=[CursoTopG(**dict(f)) for f in top],
            ultimos_estudiantes=[_estudiante(f) for f in ultimos],
        )

    @strawberry.field(description="Estudiantes, con el mismo buscador sin tildes del REST")
    def estudiantes(
        self,
        info: strawberry.Info,
        q: Annotated[str | None, strawberry.argument(description="código, DNI, nombres o apellidos")] = None,
        page: Annotated[int, strawberry.argument(description="página, desde 1")] = 1,
        page_size: Annotated[int, strawberry.argument(description="filas por página, 1..100")] = 25,
    ) -> list[EstudianteG]:
        db: Session = info.context["db"]
        parametros: dict = {"limite": max(1, min(page_size, 100)), "salto": (max(1, page) - 1) * page_size}
        where = ""
        if q and q.strip():
            where = (
                " WHERE (e.codigo ILIKE :patron OR e.dni ILIKE :patron "
                " OR unaccent(e.nombres) ILIKE unaccent(:patron) OR unaccent(e.apellidos) ILIKE unaccent(:patron))"
            )
            parametros["patron"] = f"%{q.strip()}%"
        filas = (
            db.execute(
                text(
                    f"SELECT {CAMPOS_ESTUDIANTE} FROM estudiantes e{where} "
                    "ORDER BY e.apellidos, e.nombres, e.id LIMIT :limite OFFSET :salto"
                ),
                parametros,
            )
            .mappings()
            .all()
        )
        return [_estudiante(f) for f in filas]

    @strawberry.field(description="Un estudiante por id; null si no existe")
    def estudiante(self, info: strawberry.Info, id: int) -> EstudianteG | None:  # noqa: A002 (nombre del argumento en el esquema)
        db: Session = info.context["db"]
        fila = db.execute(text(f"SELECT {CAMPOS_ESTUDIANTE} FROM estudiantes e WHERE e.id = :id"), {"id": id}).mappings().first()
        return _estudiante(fila) if fila else None

    @strawberry.field(description="Catálogo de cursos, con búsqueda por código o nombre")
    def cursos(self, info: strawberry.Info, q: str | None = None, incluir_inactivos: bool = False) -> list[CursoG]:
        db: Session = info.context["db"]
        condiciones, parametros = [], {}
        if q and q.strip():
            condiciones.append("(c.codigo ILIKE :patron OR unaccent(c.nombre) ILIKE unaccent(:patron))")
            parametros["patron"] = f"%{q.strip()}%"
        if not incluir_inactivos:
            condiciones.append("c.estado IS TRUE")
        where = f" WHERE {' AND '.join(condiciones)}" if condiciones else ""
        filas = (
            db.execute(
                text(f"SELECT c.id, c.codigo, c.nombre, c.creditos, c.horas, c.estado FROM cursos c{where} ORDER BY c.codigo"),
                parametros,
            )
            .mappings()
            .all()
        )
        return [CursoG(**dict(f)) for f in filas]

    @strawberry.field(description="Matrículas de un estudiante, con sus notas")
    def matriculas(self, info: strawberry.Info, estudiante_id: int, periodo: str | None = None) -> list[MatriculaG]:
        db: Session = info.context["db"]
        parametros: dict = {"id": estudiante_id}
        filtro = " WHERE v.estudiante_id = :id"
        if periodo:
            filtro += " AND v.periodo = :periodo"
            parametros["periodo"] = periodo
        filas = (
            db.execute(
                text(
                    "SELECT v.matricula_id, v.periodo, v.estado_matricula AS estado, v.curso_id, v.codigo_curso, v.curso, v.creditos "
                    f"FROM v_matriculas_detalle v{filtro} ORDER BY v.periodo DESC, v.curso"
                ),
                parametros,
            )
            .mappings()
            .all()
        )
        matriculas = []
        for fila in filas:
            notas = (
                db.execute(
                    text(
                        "SELECT id, tipo, numero, nota, observacion FROM notas WHERE matricula_id = :id ORDER BY tipo, numero, id"
                    ),
                    {"id": fila["matricula_id"]},
                )
                .mappings()
                .all()
            )
            matriculas.append(
                MatriculaG(
                    id=fila["matricula_id"],
                    periodo=fila["periodo"],
                    estado=fila["estado"],
                    curso_id=fila["curso_id"],
                    codigo_curso=fila["codigo_curso"],
                    curso=fila["curso"],
                    creditos=fila["creditos"],
                    notas=[
                        NotaG(
                            id=n["id"],
                            tipo=n["tipo"],
                            numero=n["numero"],
                            nota=float(n["nota"]),
                            nota_texto=f"{n['nota']:.2f}",
                            observacion=n["observacion"],
                        )
                        for n in notas
                    ],
                )
            )
        return matriculas

    @strawberry.field(description="Boleta del periodo, con la misma fórmula que el REST")
    def boleta(self, info: strawberry.Info, estudiante_id: int, periodo: str) -> BoletaG | None:
        db: Session = info.context["db"]
        datos = calcular(db, estudiante_id, periodo)
        if datos is None:
            return None
        return BoletaG(
            estudiante=_estudiante(datos["estudiante"]),
            periodo=datos["periodo"],
            cursos=[
                CursoBoletaG(**{k: c[k] for k in ("curso_id", "codigo_curso", "curso", "creditos", "cantidad_notas", "nota")})
                for c in datos["cursos"]
            ],
            creditos_con_notas=datos["creditos_con_notas"],
            promedio=datos["promedio"],
            promedio_texto=datos["promedio_texto"],
            promedio_simple=datos["promedio_simple"],
        )


esquema = strawberry.Schema(query=Consulta)


async def contexto():
    """Una sesión de PostgreSQL por petición GraphQL (igual que get_db en el REST)."""
    db = SesionLocal()
    try:
        yield {"db": db}
    finally:
        db.close()


router = GraphQLRouter(
    esquema,
    path="/graphql",
    graphql_ide="graphiql",
    context_getter=contexto,
    dependencies=[Depends(usuario_actual)],
)
