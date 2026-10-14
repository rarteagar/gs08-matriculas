# ============================================================
# GS08 · Matrículas y Notas | tests/test_auditoria.py
# Autor: @dev | Rubrica: bases de datos hibridas
# La bitácora se lee con GET /api/v1/auditoria (solo admin) y su contenido nace de
# las escrituras ya probadas en test_observabilidad.py.
# ============================================================
import pytest
from sqlalchemy import text

from app import mongo
from tests.dobles import BaseFalsa


@pytest.fixture()
def base_falsa():
    base = BaseFalsa()
    mongo.forzar("conexion-de-prueba", base)
    yield base
    mongo.reiniciar()


@pytest.fixture()
def cabecera_asistente(cliente, sesion, cabecera):
    """Un usuario con rol asistente; se borra al final para no mover los KPIs del seed."""
    from app.security import generar_hash

    identificador = sesion.execute(
        text(
            "INSERT INTO usuarios (nombre_usuario, email, password_hash, nombre_completo, rol, estado) "
            "VALUES ('qa_bitacora_asistente', 'qa_bitacora@horizonte.edu.pe', :hash, 'QA Bitacora', 'asistente', true) "
            "RETURNING id"
        ),
        {"hash": generar_hash("Clave1234")},
    ).scalar_one()
    sesion.commit()
    try:
        login = cliente.post("/api/v1/auth/login", json={"usuario": "qa_bitacora_asistente", "password": "Clave1234"})
        assert login.status_code == 200, login.text
        yield {"Authorization": f"Bearer {login.json()['access_token']}"}
    finally:
        sesion.execute(text("DELETE FROM usuarios WHERE id = :id"), {"id": identificador})
        sesion.commit()


def test_la_bitacora_lista_lo_que_se_escribio(cliente, cabecera, base_falsa, nuevo_codigo, nuevo_dni) -> None:
    alta = cliente.post(
        "/api/v1/estudiantes",
        json={"codigo": nuevo_codigo(), "dni": nuevo_dni(), "nombres": "AUDITORIA", "apellidos": "LISTA"},
        headers=cabecera,
    )
    assert alta.status_code == 201, alta.text
    try:
        respuesta = cliente.get("/api/v1/auditoria", headers=cabecera)
        assert respuesta.status_code == 200, respuesta.text
        datos = respuesta.json()
        assert datos["activa"] is True
        assert datos["detalle"] is None
        assert datos["total"] == 1
        assert datos["total_bitacora"] == 1
        assert datos["items"][0]["entidad"] == "estudiante"
        assert datos["items"][0]["accion"] == "crear"
        assert datos["items"][0]["usuario"] == "admin"
        assert datos["items"][0]["datos"]["cuerpo"]["nombres"] == "AUDITORIA"
    finally:
        cliente.delete(f"/api/v1/estudiantes/{alta.json()['id']}", params={"confirmar": "true"}, headers=cabecera)


def test_la_bitacora_filtra_por_entidad(cabecera, cliente, base_falsa, nuevo_codigo, nuevo_dni) -> None:
    estudiante = cliente.post(
        "/api/v1/estudiantes",
        json={"codigo": nuevo_codigo(), "dni": nuevo_dni(), "nombres": "FILTRO", "apellidos": "UNO"},
        headers=cabecera,
    )
    curso = cliente.post(
        "/api/v1/cursos",
        json={"codigo": f"C{nuevo_codigo()}", "nombre": "CURSO DE FILTRO", "creditos": 3, "horas": 48},
        headers=cabecera,
    )
    assert estudiante.status_code == 201 and curso.status_code == 201
    try:
        solo_curso = cliente.get("/api/v1/auditoria", params={"entidad": "curso"}, headers=cabecera).json()
        assert solo_curso["total"] == 1
        assert solo_curso["total_bitacora"] == 2
        assert solo_curso["items"][0]["entidad"] == "curso"
        # en un alta el id no viene en la ruta: queda el código en el cuerpo del documento
        assert solo_curso["items"][0]["entidad_id"] is None
        assert solo_curso["items"][0]["datos"]["cuerpo"]["codigo"] == curso.json()["codigo"]

        solo_crear = cliente.get("/api/v1/auditoria", params={"entidad": "estudiante", "accion": "crear"}, headers=cabecera).json()
        assert solo_crear["total"] == 1
        # un filtro sin coincidencias devuelve la lista vacía, no todo
        nada = cliente.get("/api/v1/auditoria", params={"accion": "eliminar"}, headers=cabecera).json()
        assert nada["total"] == 0 and nada["items"] == []
    finally:
        cliente.delete(f"/api/v1/estudiantes/{estudiante.json()['id']}", params={"confirmar": "true"}, headers=cabecera)
        cliente.delete(f"/api/v1/cursos/{curso.json()['id']}", params={"confirmar": "true"}, headers=cabecera)


def test_la_bitacora_solo_la_ve_el_admin(cliente, cabecera_asistente) -> None:
    assert cliente.get("/api/v1/auditoria", headers=cabecera_asistente).status_code == 403
    assert cliente.get("/api/v1/auditoria").status_code == 401  # sin token


def test_sin_bitacora_responde_activa_false_y_lo_dice(cliente, cabecera) -> None:
    mongo.forzar(None)  # la segunda base está apagada
    try:
        respuesta = cliente.get("/api/v1/auditoria", headers=cabecera)
        assert respuesta.status_code == 200, respuesta.text
        datos = respuesta.json()
        assert datos["activa"] is False
        assert datos["items"] == []
        assert datos["total"] == 0
        assert "apagada" in datos["detalle"]
    finally:
        mongo.reiniciar()


def test_el_limite_de_la_consulta_se_valida(cliente, cabecera, base_falsa) -> None:
    assert cliente.get("/api/v1/auditoria", params={"limite": 0}, headers=cabecera).status_code == 422
    assert cliente.get("/api/v1/auditoria", params={"limite": 500}, headers=cabecera).status_code == 422
