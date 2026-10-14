# ============================================================
# GS08 · Matrículas y Notas | tests/test_graphql.py
# Autor: @dev | Rubrica: API REST y GraphQL
# La capa GraphQL se prueba de punta a punta con TestClient: mismo token, mismos
# datos y la misma boleta que el REST (el cálculo vive en app/boleta.py).
# Strawberry expone los campos en camelCase (estudianteId, promedioTexto...).
# ============================================================
import pytest

URL = "/graphql"


def consultar(cliente, cuerpo: str, cabecera: dict | None = None):
    return cliente.post(URL, json={"query": cuerpo}, headers=cabecera or {})


def _alta_estudiante(cliente, cabecera, codigo, dni) -> int:
    respuesta = cliente.post(
        "/api/v1/estudiantes",
        json={"codigo": codigo, "dni": dni, "nombres": "GRAPHQL", "apellidos": "PRUEBA"},
        headers=cabecera,
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["id"]


def _alta_matricula(cliente, cabecera, estudiante_id, curso_id, periodo) -> int:
    respuesta = cliente.post(
        "/api/v1/matriculas",
        json={
            "estudiante_id": estudiante_id,
            "curso_id": curso_id,
            "periodo": periodo,
            "fecha_matricula": "2026-08-01",
        },
        headers=cabecera,
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["id"]


def test_sin_token_responde_401(cliente) -> None:
    respuesta = consultar(cliente, "{ panel { estudiantesActivos } }")
    assert respuesta.status_code == 401


def test_el_panel_responde_los_mismos_kpis_que_el_rest(cliente, cabecera) -> None:
    rest = cliente.get("/api/v1/dashboard", headers=cabecera).json()
    respuesta = consultar(
        cliente,
        "{ panel { estudiantesActivos cursosActivos matriculasActivas usuariosActivos "
        "topCursos { codigo matriculas } ultimosEstudiantes { nombreCompleto } } }",
        cabecera,
    )
    assert respuesta.status_code == 200, respuesta.text
    datos = respuesta.json()
    assert "errors" not in datos, datos
    panel = datos["data"]["panel"]
    assert panel["estudiantesActivos"] == rest["estudiantes_activos"]
    assert panel["cursosActivos"] == rest["cursos_activos"]
    assert panel["matriculasActivas"] == rest["matriculas_activas"]
    assert panel["usuariosActivos"] == rest["usuarios_activos"]
    assert len(panel["topCursos"]) == len(rest["top_cursos"])


def test_estudiantes_con_el_buscador_sin_tildes(cliente, cabecera) -> None:
    respuesta = consultar(cliente, '{ estudiantes(q: "huaman") { id codigo nombreCompleto } }', cabecera)
    datos = respuesta.json()
    assert "errors" not in datos, datos
    estudiantes = datos["data"]["estudiantes"]
    assert estudiantes, "el seed trae a Huamán: `huaman` sin tilde debe encontrarlo"
    assert all("Huam" in e["nombreCompleto"] for e in estudiantes)


def test_estudiante_inexistente_devuelve_null(cliente, cabecera) -> None:
    respuesta = consultar(cliente, "{ estudiante(id: 999999) { id nombreCompleto } }", cabecera)
    datos = respuesta.json()
    assert "errors" not in datos, datos
    assert datos["data"]["estudiante"] is None


def test_cursos_con_busqueda(cliente, cabecera) -> None:
    respuesta = consultar(cliente, '{ cursos(q: "C10") { id codigo nombre creditos } }', cabecera)
    datos = respuesta.json()
    assert "errors" not in datos, datos
    assert all("C10" in c["codigo"] for c in datos["data"]["cursos"])


def test_la_boleta_de_graphql_da_lo_mismo_que_el_rest(cliente, cabecera, nuevo_codigo, nuevo_dni) -> None:
    """Mismo caso de la rúbrica: C101 14/16/18 -> 16.00 y promedio ponderado."""
    curso_id = cliente.get("/api/v1/cursos", headers=cabecera).json()["cursos"][0]["id"]
    estudiante_id = _alta_estudiante(cliente, cabecera, nuevo_codigo(), nuevo_dni())
    try:
        matricula_id = _alta_matricula(cliente, cabecera, estudiante_id, curso_id, "2026-10")
        for tipo, nota in (("practica", 14), ("parcial", 16), ("final", 18)):
            assert (
                cliente.post(
                    f"/api/v1/matriculas/{matricula_id}/notas",
                    json={"tipo": tipo, "numero": 1, "nota": nota},
                    headers=cabecera,
                ).status_code
                == 201
            )

        rest = cliente.get(f"/api/v1/estudiantes/{estudiante_id}/boleta", params={"periodo": "2026-10"}, headers=cabecera).json()
        respuesta = consultar(
            cliente,
            f"""{{ boleta(estudianteId: {estudiante_id}, periodo: "2026-10") {{
                    periodo promedio promedioTexto promedioSimple creditosConNotas
                    estudiante {{ id nombreCompleto }}
                    cursos {{ codigoCurso nota cantidadNotas }}
                 }} }}""",
            cabecera,
        )
        datos = respuesta.json()
        assert "errors" not in datos, datos
        boleta = datos["data"]["boleta"]
        assert boleta["estudiante"]["id"] == estudiante_id
        assert boleta["promedio"] == 16.0
        assert boleta["promedioTexto"] == "16.00"
        assert boleta["creditosConNotas"] == rest["creditos_con_notas"]
        assert boleta["cursos"][0]["nota"] == rest["cursos"][0]["nota"]
        assert boleta["cursos"][0]["cantidadNotas"] == 3
    finally:
        cliente.delete(f"/api/v1/estudiantes/{estudiante_id}", params={"confirmar": "true"}, headers=cabecera)


def test_matriculas_de_un_estudiante_con_sus_notas(cliente, cabecera, nuevo_codigo, nuevo_dni) -> None:
    curso_id = cliente.get("/api/v1/cursos", headers=cabecera).json()["cursos"][0]["id"]
    estudiante_id = _alta_estudiante(cliente, cabecera, nuevo_codigo(), nuevo_dni())
    try:
        matricula_id = _alta_matricula(cliente, cabecera, estudiante_id, curso_id, "2026-11")
        cliente.post(
            f"/api/v1/matriculas/{matricula_id}/notas",
            json={"tipo": "parcial", "numero": 1, "nota": 15},
            headers=cabecera,
        )
        respuesta = consultar(
            cliente,
            f"""{{ matriculas(estudianteId: {estudiante_id}, periodo: "2026-11") {{
                    id periodo estado codigoCurso curso notas {{ tipo numero nota notaTexto }}
                 }} }}""",
            cabecera,
        )
        datos = respuesta.json()
        assert "errors" not in datos, datos
        matriculas = datos["data"]["matriculas"]
        assert len(matriculas) == 1
        assert matriculas[0]["id"] == matricula_id
        assert matriculas[0]["estado"] == "activa"
        assert matriculas[0]["notas"][0]["nota"] == 15.0
        assert matriculas[0]["notas"][0]["notaTexto"] == "15.00"
    finally:
        cliente.delete(f"/api/v1/estudiantes/{estudiante_id}", params={"confirmar": "true"}, headers=cabecera)


def test_boleta_de_un_estudiante_inexistente_devuelve_null(cliente, cabecera) -> None:
    respuesta = consultar(cliente, '{ boleta(estudianteId: 999999, periodo: "2026-10") { periodo } }', cabecera)
    datos = respuesta.json()
    assert "errors" not in datos, datos
    assert datos["data"]["boleta"] is None


@pytest.mark.parametrize("campo", ["{ noExiste }", "{ estudiantes }"])
def test_campos_mal_escritos_dan_error_de_esquema(cliente, cabecera, campo) -> None:
    respuesta = consultar(cliente, campo, cabecera)
    assert respuesta.status_code == 200
    assert "errors" in respuesta.json()
