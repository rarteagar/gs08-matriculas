# ============================================================
# GS08 · Matrículas y Notas | tests/test_cursos.py
# Autor: @dev | T1.3 | Sprint 1
# C-13 (créditos 1..10, horas válidas y default del legacy), C-14 (código repetido
# -> 409), C-15 (baja lógica) y C-30 (DELETE con matrículas -> 409 con el conteo).
# ============================================================
import itertools

_contador = itertools.count(2000)


def _codigo() -> str:
    return f"PZC{next(_contador)}"


def test_c13_creditos_y_horas_fuera_de_rango_dan_422(cliente, cabecera) -> None:
    for creditos in (0, 11, -1):
        respuesta = cliente.post(
            "/api/v1/cursos",
            json={"codigo": _codigo(), "nombre": "Curso inválido", "creditos": creditos, "horas": 10},
            headers=cabecera,
        )
        assert respuesta.status_code == 422, f"creditos={creditos} -> {respuesta.status_code}"
        assert "creditos" in respuesta.json()["detail"].lower()

    for horas in (0, 1001):
        respuesta = cliente.post(
            "/api/v1/cursos",
            json={"codigo": _codigo(), "nombre": "Curso inválido", "creditos": 3, "horas": horas},
            headers=cabecera,
        )
        assert respuesta.status_code == 422, f"horas={horas} -> {respuesta.status_code}"
        assert "horas" in respuesta.json()["detail"].lower()


def test_c13_sin_creditos_ni_horas_se_guardan_los_defaults_del_legacy(cliente, cabecera) -> None:
    codigo = _codigo()
    alta = cliente.post("/api/v1/cursos", json={"codigo": codigo, "nombre": "Curso con defaults"}, headers=cabecera)
    assert alta.status_code == 201, alta.text
    creado = alta.json()
    try:
        assert creado["creditos"] == 3, creado
        assert creado["horas"] == 48, creado
        assert creado["estado"] is True
    finally:
        assert cliente.delete(f"/api/v1/cursos/{creado['id']}", headers=cabecera).status_code == 204


def test_c14_codigo_de_curso_repetido_da_409(cliente, cabecera) -> None:
    respuesta = cliente.post(
        "/api/v1/cursos", json={"codigo": "C101", "nombre": "Otro nombre", "creditos": 3, "horas": 48}, headers=cabecera
    )
    assert respuesta.status_code == 409, respuesta.text
    assert "código" in respuesta.json()["detail"].lower()


def test_c15_baja_logica_del_curso(cliente, cabecera) -> None:
    codigo = _codigo()
    creado = cliente.post("/api/v1/cursos", json={"codigo": codigo, "nombre": "Curso a dar de baja"}, headers=cabecera).json()
    try:
        baja = cliente.put(
            f"/api/v1/cursos/{creado['id']}",
            json={"codigo": codigo, "nombre": "Curso a dar de baja", "creditos": 3, "horas": 48, "estado": False},
            headers=cabecera,
        )
        assert baja.status_code == 200, baja.text
        activos = cliente.get("/api/v1/cursos", params={"estado": "activo"}, headers=cabecera).json()
        assert all(c["codigo"] != codigo for c in activos["cursos"])
        # el registro sigue existiendo (baja lógica, no borrado)
        assert cliente.get(f"/api/v1/cursos/{creado['id']}", headers=cabecera).status_code == 200
        assert cliente.get("/api/v1/dashboard", headers=cabecera).json()["cursos_activos"] == 7
    finally:
        assert cliente.delete(f"/api/v1/cursos/{creado['id']}", headers=cabecera).status_code == 204


def test_c30_delete_de_curso_con_matriculas_da_409_con_el_conteo(cliente, cabecera) -> None:
    """El curso 5 del seed tiene 3 matrículas: 409 con el conteo exacto y no borra."""
    respuesta = cliente.delete("/api/v1/cursos/5", headers=cabecera)
    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["matriculas"] == 3, respuesta.json()
    assert cliente.get("/api/v1/cursos/5", headers=cabecera).status_code == 200
    assert cliente.get("/api/v1/dashboard", headers=cabecera).json()["matriculas_activas"] == 23


def test_c19_curso_inexistente_da_404(cliente, cabecera) -> None:
    assert cliente.get("/api/v1/cursos/99999", headers=cabecera).status_code == 404
