# ============================================================
# GS08 · Matrículas y Notas | tests/test_boleta_archivada.py
# Autor: @dev | Rubrica: bases de datos hibridas
# Al emitir la boleta (REST) queda una copia como documento en la segunda base y se
# consulta por GET /api/v1/estudiantes/{id}/boleta/archivada.
# ============================================================
import pytest

from app import mongo
from tests.dobles import BaseFalsa


@pytest.fixture()
def base_falsa():
    base = BaseFalsa()
    mongo.forzar("conexion-de-prueba", base)
    yield base
    mongo.reiniciar()


def _estudiante_con_nota(cliente, cabecera, codigo, dni, periodo="2026-12") -> tuple[int, int]:
    curso_id = cliente.get("/api/v1/cursos", headers=cabecera).json()["cursos"][0]["id"]
    estudiante_id = cliente.post(
        "/api/v1/estudiantes",
        json={"codigo": codigo, "dni": dni, "nombres": "ARCHIVO", "apellidos": "BOLETA"},
        headers=cabecera,
    ).json()["id"]
    matricula_id = cliente.post(
        "/api/v1/matriculas",
        json={
            "estudiante_id": estudiante_id,
            "curso_id": curso_id,
            "periodo": periodo,
            "fecha_matricula": "2026-08-01",
        },
        headers=cabecera,
    ).json()["id"]
    cliente.post(
        f"/api/v1/matriculas/{matricula_id}/notas",
        json={"tipo": "parcial", "numero": 1, "nota": 16},
        headers=cabecera,
    )
    return estudiante_id, matricula_id


def test_la_boleta_emitida_queda_archivada(cliente, cabecera, base_falsa, nuevo_codigo, nuevo_dni) -> None:
    estudiante_id, _ = _estudiante_con_nota(cliente, cabecera, nuevo_codigo(), nuevo_dni())
    try:
        boleta = cliente.get(f"/api/v1/estudiantes/{estudiante_id}/boleta", params={"periodo": "2026-12"}, headers=cabecera)
        assert boleta.status_code == 200, boleta.text

        archivada = cliente.get(
            f"/api/v1/estudiantes/{estudiante_id}/boleta/archivada", params={"periodo": "2026-12"}, headers=cabecera
        )
        assert archivada.status_code == 200, archivada.text
        datos = archivada.json()
        assert datos["activa"] is True
        assert datos["archivada"] is True
        assert datos["generado_por"] == "admin"
        assert datos["generado_en"]
        assert datos["boleta"]["promedio_texto"] == boleta.json()["promedio_texto"]
        # el documento guardado es el mismo que devolvió el REST
        assert datos["boleta"]["cursos"][0]["nota"] == boleta.json()["cursos"][0]["nota"]
    finally:
        cliente.delete(f"/api/v1/estudiantes/{estudiante_id}", params={"confirmar": "true"}, headers=cabecera)


def test_sin_archivo_lo_dice(cliente, cabecera, base_falsa) -> None:
    respuesta = cliente.get("/api/v1/estudiantes/1/boleta/archivada", params={"periodo": "2026-12"}, headers=cabecera)
    assert respuesta.status_code == 200, respuesta.text
    datos = respuesta.json()
    assert datos["archivada"] is False
    assert datos["boleta"] is None


def test_con_la_segunda_base_apagada_responde_igual(cliente, cabecera) -> None:
    mongo.forzar(None)
    try:
        respuesta = cliente.get("/api/v1/estudiantes/1/boleta/archivada", params={"periodo": "2026-12"}, headers=cabecera)
        assert respuesta.status_code == 200, respuesta.text
        datos = respuesta.json()
        assert datos["activa"] is False
        assert datos["archivada"] is False
    finally:
        mongo.reiniciar()


def test_el_periodo_se_valida(cliente, cabecera, base_falsa) -> None:
    respuesta = cliente.get("/api/v1/estudiantes/1/boleta/archivada", params={"periodo": "2026"}, headers=cabecera)
    assert respuesta.status_code == 422
