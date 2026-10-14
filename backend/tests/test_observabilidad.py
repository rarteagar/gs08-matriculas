# ============================================================
# GS08 · Matrículas y Notas | tests/test_observabilidad.py
# Autor: @dev | Rubrica: logging centralizado
#   * cada petición viaja con su X-Request-ID y su usuario
#   * los logs salen en JSON (una línea = un JSON parseable)
#   * el manejador de Loki empuja el log y, si Loki no está, no rompe nada
#   * una escritura deja rastro en la bitácora e invalida la caché del panel
# ============================================================
import io
import json
import logging

import pytest

from app import cache, mongo, observabilidad
from tests.dobles import BaseFalsa, RedisFalso, ServidorLoki


@pytest.fixture()
def base_falsa():
    base = BaseFalsa()
    mongo.forzar("conexion-de-prueba", base)
    yield base
    mongo.reiniciar()


@pytest.fixture()
def redis_falso():
    doble = RedisFalso()
    cache.forzar(doble)
    yield doble
    cache.reiniciar()


def _registro(mensaje: str, nivel: int = logging.INFO) -> logging.LogRecord:
    registro = logging.LogRecord("gs08.prueba", nivel, __file__, 1, mensaje, None, None)
    observabilidad.FiltroContexto().filter(registro)
    return registro


def test_el_log_es_una_linea_json() -> None:
    manejador = logging.StreamHandler(io.StringIO())
    manejador.setFormatter(observabilidad.formateador_json())
    manejador.addFilter(observabilidad.FiltroContexto())
    observabilidad.pedido_id.set("abc123")
    observabilidad.usuario_log.set("admin")
    try:
        manejador.emit(_registro("estudiante creado id=7"))
    finally:
        observabilidad.pedido_id.set("-")
        observabilidad.usuario_log.set("-")

    linea = json.loads(manejador.stream.getvalue().strip())
    assert linea["mensaje"] == "estudiante creado id=7"
    assert linea["nivel"] == "INFO"
    assert linea["pedido_id"] == "abc123"
    assert linea["usuario"] == "admin"
    assert linea["logger"] == "gs08.prueba"
    assert "momento" in linea and "servicio" in linea and "entorno" in linea


def test_los_logs_llegan_a_loki() -> None:
    servidor = ServidorLoki()
    try:
        manejador = observabilidad.ManejadorLoki(servidor.url, "gs08-api")
        manejador.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        manejador.addFilter(observabilidad.FiltroContexto())
        manejador.emit(_registro("matrícula creada id=3"))
        assert len(servidor.peticiones) == 1
        cuerpo = servidor.peticiones[0]
        assert cuerpo["streams"][0]["stream"] == {"servicio": "gs08-api", "nivel": "INFO"}
        etiqueta, texto = cuerpo["streams"][0]["values"][0]
        assert int(etiqueta) > 0
        assert json.loads(texto)["mensaje"] == "matrícula creada id=3"
    finally:
        servidor.detener()


def test_si_loki_esta_caido_no_rompe_la_peticion() -> None:
    manejador = observabilidad.ManejadorLoki("http://127.0.0.1:1", "gs08-api")
    manejador.addFilter(observabilidad.FiltroContexto())
    manejador.emit(_registro("da igual"))  # no debe lanzar
    assert manejador.avisado is True


def test_la_respuesta_trae_el_x_request_id(cliente, cabecera) -> None:
    respuesta = cliente.get("/api/v1/estudiantes", headers={**cabecera, "X-Request-ID": "prueba-123"})
    assert respuesta.status_code == 200
    assert respuesta.headers["X-Request-ID"] == "prueba-123"

    otra = cliente.get("/api/v1/estudiantes", headers=cabecera)
    assert len(otra.headers["X-Request-ID"]) == 12  # generado


def test_una_escritura_deja_rastro_en_la_bitacora(cliente, cabecera, base_falsa, nuevo_codigo, nuevo_dni) -> None:
    codigo = nuevo_codigo()
    alta = cliente.post(
        "/api/v1/estudiantes",
        json={"codigo": codigo, "dni": nuevo_dni(), "nombres": "BITACORA", "apellidos": "PRUEBA"},
        headers={**cabecera, "X-Request-ID": "rastro-1"},
    )
    assert alta.status_code == 201, alta.text
    try:
        documentos = base_falsa["bitacora"].documentos
        assert len(documentos) == 1
        registro = documentos[0]
        assert registro["accion"] == "crear"
        assert registro["entidad"] == "estudiante"
        # en un alta el id lo pone la base después: en la ruta no viene, y el cuerpo
        # del documento guarda el código con el que se identificó al recurso
        assert registro["entidad_id"] is None
        assert registro["datos"]["cuerpo"]["codigo"] == codigo
        assert registro["usuario"] == "admin"
        assert registro["resultado"] == "ok"
        assert registro["pedido_id"] == "rastro-1"
        assert registro["datos"]["estado"] == 201
        assert registro["datos"]["cuerpo"]["nombres"] == "BITACORA"
    finally:
        cliente.delete(f"/api/v1/estudiantes/{alta.json()['id']}", params={"confirmar": "true"}, headers=cabecera)


def test_en_una_edicion_y_una_baja_queda_el_id_de_la_ruta(cliente, cabecera, base_falsa, nuevo_codigo, nuevo_dni) -> None:
    alta = cliente.post(
        "/api/v1/estudiantes",
        json={"codigo": nuevo_codigo(), "dni": nuevo_dni(), "nombres": "RASTRO", "apellidos": "POR ID"},
        headers=cabecera,
    )
    assert alta.status_code == 201, alta.text
    nuevo_id = alta.json()["id"]
    try:
        assert (
            cliente.put(
                f"/api/v1/estudiantes/{nuevo_id}",
                json={"codigo": alta.json()["codigo"], "dni": alta.json()["dni"], "nombres": "EDITADO", "apellidos": "POR ID"},
                headers=cabecera,
            ).status_code
            == 200
        )
        assert cliente.delete(f"/api/v1/estudiantes/{nuevo_id}", params={"confirmar": "true"}, headers=cabecera).status_code == 204

        acciones = [(d["accion"], d["entidad_id"]) for d in base_falsa["bitacora"].documentos]
        assert ("editar", nuevo_id) in acciones
        assert ("eliminar", nuevo_id) in acciones
    finally:
        pass


def test_una_escritura_invalida_la_cache_del_panel(cliente, cabecera, redis_falso, nuevo_codigo, nuevo_dni) -> None:
    cache.guardar(cache.CLAVE_PANEL, {"estudiantes_activos": 12})
    assert cache.obtener(cache.CLAVE_PANEL) is not None
    alta = cliente.post(
        "/api/v1/estudiantes",
        json={"codigo": nuevo_codigo(), "dni": nuevo_dni(), "nombres": "CACHE", "apellidos": "PRUEBA"},
        headers=cabecera,
    )
    assert alta.status_code == 201, alta.text
    try:
        assert cache.obtener(cache.CLAVE_PANEL) is None
        assert cache.CLAVE_PANEL in redis_falso.borrados
    finally:
        cliente.delete(f"/api/v1/estudiantes/{alta.json()['id']}", params={"confirmar": "true"}, headers=cabecera)


def test_el_login_no_guarda_la_contrasena_en_la_bitacora(cliente, base_falsa) -> None:
    from tests.conftest import ADMIN_CLAVE, ADMIN_USUARIO

    respuesta = cliente.post("/api/v1/auth/login", json={"usuario": ADMIN_USUARIO, "password": ADMIN_CLAVE})
    assert respuesta.status_code == 200, respuesta.text
    documentos = base_falsa["bitacora"].documentos
    assert len(documentos) == 1
    assert documentos[0]["entidad"] == "sesión"
    assert documentos[0]["datos"]["cuerpo"]["password"] == "***"
    assert documentos[0]["datos"]["cuerpo"]["usuario"] == ADMIN_USUARIO
    assert ADMIN_CLAVE not in json.dumps(documentos, ensure_ascii=False, default=str)


def test_una_lectura_no_escribe_en_la_bitacora(cliente, cabecera, base_falsa) -> None:
    assert cliente.get("/api/v1/dashboard", headers=cabecera).status_code == 200
    assert cliente.get("/api/v1/estudiantes", headers=cabecera).status_code == 200
    assert base_falsa["bitacora"].documentos == []


def test_un_error_de_validacion_queda_registrado_como_error(cliente, cabecera, base_falsa) -> None:
    respuesta = cliente.post("/api/v1/estudiantes", json={"nombres": "SIN CODIGO"}, headers=cabecera)
    assert respuesta.status_code == 422
    registros = base_falsa["bitacora"].documentos
    assert len(registros) == 1
    assert registros[0]["resultado"] == "error 422"
    assert registros[0]["entidad"] == "estudiante"
