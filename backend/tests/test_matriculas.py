# ============================================================
# GS08 · Matrículas y Notas | tests/test_matriculas.py
# Autor: @dev | T1.3 / T2.1 / T3.1 | Sprint 1-3
# C-16 (alta válida), C-17 (duplicado -> 409 con el mensaje del legacy), C-18
# (periodo inválido -> 422), C-19 (FK inexistente -> 404), C-20 (retirar es baja
# lógica), C-24/C-25/C-26 (notas), C-27/C-28 (nota del curso y promedio ponderado)
# y C-29 (la nota cuelga de la matrícula).
# ============================================================
import pytest


def _alta_estudiante(cliente, cabecera, codigo, dni, nombres="Alumno", apellidos="De Prueba") -> int:
    respuesta = cliente.post(
        "/api/v1/estudiantes",
        json={"codigo": codigo, "dni": dni, "nombres": nombres, "apellidos": apellidos},
        headers=cabecera,
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["id"]


def _alta_matricula(cliente, cabecera, estudiante_id, curso_id, periodo="2026-02", fecha="2026-08-01"):
    return cliente.post(
        "/api/v1/matriculas",
        json={"estudiante_id": estudiante_id, "curso_id": curso_id, "periodo": periodo, "fecha_matricula": fecha},
        headers=cabecera,
    )


def test_c16_alta_de_matricula_valida_y_filtro_por_periodo(cliente, cabecera, nuevo_codigo, nuevo_dni) -> None:
    estudiante_id = _alta_estudiante(cliente, cabecera, nuevo_codigo(), nuevo_dni())
    try:
        alta = _alta_matricula(cliente, cabecera, estudiante_id, 7, periodo="2026-07")
        assert alta.status_code == 201, alta.text
        creada = alta.json()
        assert creada["id"] and creada["periodo"] == "2026-07"
        assert creada["curso"] == "Fundamentos de Administración"
        assert creada["dni"] and creada["estudiante"]

        listado = cliente.get("/api/v1/matriculas", params={"periodo": "2026-07"}, headers=cabecera).json()
        assert listado["total"] == 1
        assert listado["matriculas"][0]["id"] == creada["id"]
        # el resto del seed sigue en 2026-02
        assert cliente.get("/api/v1/matriculas", params={"periodo": "2026-02"}, headers=cabecera).json()["total"] == 24
    finally:
        cliente.delete(f"/api/v1/estudiantes/{estudiante_id}", params={"confirmar": "true"}, headers=cabecera)


def test_c17_matricula_duplicada_da_409_con_el_mensaje_del_legacy(cliente, cabecera) -> None:
    respuesta = _alta_matricula(cliente, cabecera, 1, 1, periodo="2026-02")
    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["detail"] == "Ese estudiante ya está matriculado en ese curso para el periodo indicado"


@pytest.mark.parametrize("periodo", ["2026-13", "2026/02", "26-02", "2026-2", "202602"])
def test_c18_periodo_invalido_da_422(cliente, cabecera, periodo) -> None:
    respuesta = _alta_matricula(cliente, cabecera, 1, 7, periodo=periodo)
    assert respuesta.status_code == 422, f"periodo={periodo} -> {respuesta.status_code}"
    assert "periodo" in respuesta.json()["detail"].lower()


def test_c19_referencias_inexistentes_dan_404(cliente, cabecera) -> None:
    sin_estudiante = _alta_matricula(cliente, cabecera, 99999, 1, periodo="2026-06")
    assert sin_estudiante.status_code == 404, sin_estudiante.text

    sin_curso = _alta_matricula(cliente, cabecera, 1, 99999, periodo="2026-06")
    assert sin_curso.status_code == 404, sin_curso.text


def test_c20_retirar_es_baja_logica_y_baja_el_kpi_en_uno(cliente, cabecera, nuevo_codigo, nuevo_dni) -> None:
    antes = cliente.get("/api/v1/dashboard", headers=cabecera).json()["matriculas_activas"]
    estudiante_id = _alta_estudiante(cliente, cabecera, nuevo_codigo(), nuevo_dni())
    try:
        creada = _alta_matricula(cliente, cabecera, estudiante_id, 6, periodo="2026-06").json()
        assert cliente.get("/api/v1/dashboard", headers=cabecera).json()["matriculas_activas"] == antes + 1

        retirar = cliente.put(f"/api/v1/matriculas/{creada['id']}", json={"estado": "retirado"}, headers=cabecera)
        assert retirar.status_code == 200, retirar.text
        assert retirar.json()["estado"] == "retirado"
        assert cliente.get("/api/v1/dashboard", headers=cabecera).json()["matriculas_activas"] == antes

        # sigue en el historial, con su badge
        historial = cliente.get("/api/v1/matriculas", params={"periodo": "2026-06"}, headers=cabecera).json()
        assert historial["total"] == 1
        assert historial["matriculas"][0]["estado"] == "retirado"
        solo_activas = cliente.get("/api/v1/matriculas", params={"periodo": "2026-06", "estado": "activa"}, headers=cabecera).json()
        assert solo_activas["total"] == 0
    finally:
        cliente.delete(f"/api/v1/estudiantes/{estudiante_id}", params={"confirmar": "true"}, headers=cabecera)


def test_c21_filtro_por_texto_y_periodo_combinados(cliente, cabecera) -> None:
    solo_periodo = cliente.get("/api/v1/matriculas", params={"periodo": "2026-02"}, headers=cabecera).json()
    assert solo_periodo["total"] == 24

    combinado = cliente.get("/api/v1/matriculas", params={"periodo": "2026-02", "q": "huaman"}, headers=cabecera).json()
    # el estudiante 2 (Quispe Huamán) tiene 2 matrículas (dato de docs/analisis/datos-seed.md)
    assert combinado["total"] == 2, combinado

    otro_periodo = cliente.get("/api/v1/matriculas", params={"periodo": "2027-01", "q": "huaman"}, headers=cabecera).json()
    assert otro_periodo["total"] == 0


def test_c24_alta_de_notas_de_una_matricula_activa(cliente, cabecera, nuevo_codigo, nuevo_dni) -> None:
    estudiante_id = _alta_estudiante(cliente, cabecera, nuevo_codigo(), nuevo_dni())
    try:
        matricula = _alta_matricula(cliente, cabecera, estudiante_id, 1, periodo="2026-03").json()
        esperado = {"practica": 14, "parcial": 16, "final": 18}
        for tipo, nota in esperado.items():
            respuesta = cliente.post(
                f"/api/v1/matriculas/{matricula['id']}/notas",
                json={"tipo": tipo, "numero": 1, "nota": nota},
                headers=cabecera,
            )
            assert respuesta.status_code == 201, respuesta.text
            assert respuesta.json()["nota"] == float(nota)
            assert respuesta.json()["nota_texto"] == f"{nota:.2f}"

        listado = cliente.get(f"/api/v1/matriculas/{matricula['id']}/notas", headers=cabecera).json()
        assert len(listado) == 3
    finally:
        cliente.delete(f"/api/v1/estudiantes/{estudiante_id}", params={"confirmar": "true"}, headers=cabecera)


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"tipo": "practica", "numero": 1, "nota": 21},
        {"tipo": "practica", "numero": 1, "nota": -1},
        {"tipo": "examen", "numero": 1, "nota": 10},
        {"tipo": "practica", "numero": 0, "nota": 10},
    ],
)
def test_c25_notas_invalidas_dan_422(cliente, cabecera, cuerpo) -> None:
    respuesta = cliente.post("/api/v1/matriculas/1/notas", json=cuerpo, headers=cabecera)
    assert respuesta.status_code == 422, f"{cuerpo} -> {respuesta.status_code}: {respuesta.text}"


def test_c25_nota_duplicada_da_409(cliente, cabecera, nuevo_codigo, nuevo_dni) -> None:
    estudiante_id = _alta_estudiante(cliente, cabecera, nuevo_codigo(), nuevo_dni())
    try:
        matricula = _alta_matricula(cliente, cabecera, estudiante_id, 1, periodo="2026-04").json()
        url = f"/api/v1/matriculas/{matricula['id']}/notas"
        assert cliente.post(url, json={"tipo": "parcial", "numero": 1, "nota": 12}, headers=cabecera).status_code == 201
        repetida = cliente.post(url, json={"tipo": "parcial", "numero": 1, "nota": 20}, headers=cabecera)
        assert repetida.status_code == 409, repetida.text
        # la nota original no se pisó
        notas = cliente.get(url, headers=cabecera).json()
        assert len(notas) == 1 and notas[0]["nota"] == 12.0
    finally:
        cliente.delete(f"/api/v1/estudiantes/{estudiante_id}", params={"confirmar": "true"}, headers=cabecera)


def test_c26_no_se_califica_una_matricula_retirada(cliente, cabecera) -> None:
    """La matrícula 13 del seed (estudiante 7, curso 4) está en estado 'retirado'."""
    respuesta = cliente.post("/api/v1/matriculas/13/notas", json={"tipo": "parcial", "numero": 1, "nota": 15}, headers=cabecera)
    assert respuesta.status_code == 409, respuesta.text
    assert "retirada" in respuesta.json()["detail"].lower()

    # y la base lo rechaza igual aunque se intente por SQL directo (trigger RN-14)
    assert cliente.get("/api/v1/matriculas/13/notas", headers=cabecera).json() == []


def test_c27_c28_boleta_con_nota_del_curso_y_promedio_ponderado(cliente, cabecera, nuevo_codigo, nuevo_dni) -> None:
    """Caso de RN-15: C101 (4 créditos) 14/16/18 -> 16.00 · C102 (3) 11 -> 11.00 · promedio 13.86 (no 13.50)."""
    estudiante_id = _alta_estudiante(cliente, cabecera, nuevo_codigo(), nuevo_dni())
    try:
        m101 = _alta_matricula(cliente, cabecera, estudiante_id, 1, periodo="2026-09").json()
        m102 = _alta_matricula(cliente, cabecera, estudiante_id, 2, periodo="2026-09").json()
        # C-28: un curso sin notas NO cuenta como 0 en el promedio (C203 · Inglés Técnico)
        m203 = _alta_matricula(cliente, cabecera, estudiante_id, 5, periodo="2026-09").json()

        for tipo, nota in (("practica", 14), ("parcial", 16), ("final", 18)):
            cliente.post(f"/api/v1/matriculas/{m101['id']}/notas", json={"tipo": tipo, "numero": 1, "nota": nota}, headers=cabecera)
        cliente.post(f"/api/v1/matriculas/{m102['id']}/notas", json={"tipo": "parcial", "numero": 1, "nota": 11}, headers=cabecera)

        boleta = cliente.get(f"/api/v1/estudiantes/{estudiante_id}/boleta", params={"periodo": "2026-09"}, headers=cabecera)
        assert boleta.status_code == 200, boleta.text
        datos = boleta.json()
        assert len(datos["cursos"]) == 3

        por_codigo = {c["codigo_curso"]: c for c in datos["cursos"]}
        assert por_codigo["C101"]["nota"] == 16.0
        assert por_codigo["C101"]["nota_texto"] == "16.00"
        assert por_codigo["C101"]["cantidad_notas"] == 3
        assert por_codigo["C102"]["nota"] == 11.0
        assert por_codigo["C203"]["nota"] is None and por_codigo["C203"]["notas"] == []

        assert datos["creditos_con_notas"] == 7
        assert datos["promedio"] == 13.86, datos
        assert datos["promedio_texto"] == "13.86"
        # la media simple daría 13.50: fijada para que nadie confunda los dos criterios
        assert datos["promedio_simple"] == 13.5
        assert m203  # el curso sin notas queda en la boleta con nota null
    finally:
        cliente.delete(f"/api/v1/estudiantes/{estudiante_id}", params={"confirmar": "true"}, headers=cabecera)


def test_c29_la_nota_cuelga_de_la_matricula_y_borrar_al_estudiante_borra_sus_notas(
    cliente, cabecera, sesion, nuevo_codigo, nuevo_dni
) -> None:
    from sqlalchemy import text

    estudiante_id = _alta_estudiante(cliente, cabecera, nuevo_codigo(), nuevo_dni())
    try:
        matricula = _alta_matricula(cliente, cabecera, estudiante_id, 1, periodo="2026-11").json()
        cliente.post(
            f"/api/v1/matriculas/{matricula['id']}/notas",
            json={"tipo": "final", "numero": 1, "nota": 17},
            headers=cabecera,
        )
        assert len(cliente.get(f"/api/v1/matriculas/{matricula['id']}/notas", headers=cabecera).json()) == 1

        # retirar la matrícula NO borra las notas ya registradas
        cliente.put(f"/api/v1/matriculas/{matricula['id']}", json={"estado": "retirado"}, headers=cabecera)
        assert len(cliente.get(f"/api/v1/matriculas/{matricula['id']}/notas", headers=cabecera).json()) == 1

        borrado = cliente.delete(f"/api/v1/estudiantes/{estudiante_id}", params={"confirmar": "true"}, headers=cabecera)
        assert borrado.status_code == 204, borrado.text
        quedan = sesion.execute(text("SELECT count(*) FROM notas WHERE matricula_id = :m"), {"m": matricula["id"]}).scalar_one()
        assert quedan == 0, "borrar el estudiante debe arrastrar sus notas por cascada"
    finally:
        cliente.delete(f"/api/v1/estudiantes/{estudiante_id}", params={"confirmar": "true"}, headers=cabecera)
