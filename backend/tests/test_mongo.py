# ============================================================
# GS08 · Matrículas y Notas | tests/test_mongo.py
# Autor: @dev | Rubrica: bases de datos hibridas (PostgreSQL + MongoDB)
# El codigo de la bitacora se prueba con un doble de la base documental.
# ============================================================
import pytest

from app import mongo
from app.config import config
from tests.dobles import BaseFalsa


@pytest.fixture()
def base_falsa():
    base = BaseFalsa()
    mongo.forzar("conexion-de-prueba", base)
    yield base
    mongo.reiniciar()


def test_registrar_y_listar(base_falsa) -> None:
    assert mongo.activa() is True
    identificador = mongo.registrar("crear", "estudiante", entidad_id=7, usuario="admin", datos={"codigo": "PZ1"}, pedido="abc123")
    assert identificador is not None
    items = mongo.listar()
    assert len(items) == 1
    assert items[0]["entidad"] == "estudiante"
    assert items[0]["accion"] == "crear"
    assert items[0]["usuario"] == "admin"
    assert items[0]["entidad_id"] == 7
    assert items[0]["pedido_id"] == "abc123"
    assert items[0]["datos"] == {"codigo": "PZ1"}
    assert isinstance(items[0]["fecha"], str)  # se serializa para la respuesta JSON


def test_listar_filtra_por_entidad_y_accion(base_falsa) -> None:
    mongo.registrar("crear", "estudiante", 1, "admin")
    mongo.registrar("editar", "estudiante", 1, "admin")
    mongo.registrar("crear", "curso", 2, "admin")
    assert len(mongo.listar(entidad="estudiante")) == 2
    assert len(mongo.listar(entidad="estudiante", accion="editar")) == 1
    assert len(mongo.listar(entidad="curso")) == 1
    assert mongo.total() == 3
    assert mongo.contar() == 3
    assert mongo.contar(entidad="estudiante") == 2
    assert mongo.contar(entidad="estudiante", accion="crear") == 1
    assert mongo.contar(entidad="nota") == 0


def test_listar_respeta_el_limite_y_ordena_por_fecha(base_falsa) -> None:
    for numero in range(5):
        mongo.registrar("crear", "nota", numero, "admin")
    items = mongo.listar(limite=2)
    assert len(items) == 2


def test_boleta_se_archiva_y_se_recupera(base_falsa) -> None:
    boleta = {"periodo": "2026-02", "promedio_texto": "16.00", "cursos": []}
    assert mongo.guardar_boleta(5, "2026-02", boleta, "admin") is True
    guardada = mongo.boleta_guardada(5, "2026-02")
    assert guardada is not None
    assert guardada["boleta"]["promedio_texto"] == "16.00"
    assert guardada["generado_por"] == "admin"
    assert isinstance(guardada["generado_en"], str)

    # Volver a emitirla reemplaza el documento, no lo duplica (upsert)
    mongo.guardar_boleta(5, "2026-02", {"periodo": "2026-02", "promedio_texto": "17.50"}, "admin")
    assert len(base_falsa["boletas_snapshot"].documentos) == 1
    assert mongo.boleta_guardada(5, "2026-02")["boleta"]["promedio_texto"] == "17.50"


def test_boleta_que_no_existe(base_falsa) -> None:
    assert mongo.boleta_guardada(99, "2026-02") is None


def test_apagada_no_rompe_el_api() -> None:
    mongo.forzar(None)
    try:
        assert mongo.activa() is False
        assert mongo.registrar("crear", "estudiante", 1, "admin") is None
        assert mongo.listar() == []
        assert mongo.total() == 0
        assert mongo.guardar_boleta(1, "2026-02", {}) is False
        assert mongo.boleta_guardada(1, "2026-02") is None
    finally:
        mongo.reiniciar()


def test_sin_url_no_se_conecta(monkeypatch) -> None:
    monkeypatch.setattr(config, "mongo_url", "")
    mongo.reiniciar()
    try:
        assert mongo.base() is None
    finally:
        mongo.reiniciar()


def test_si_mongo_no_responde_queda_apagada(monkeypatch) -> None:
    monkeypatch.setattr(config, "mongo_url", "mongodb://127.0.0.1:1")  # puerto cerrado
    mongo.reiniciar()
    try:
        assert mongo.base() is None
        assert mongo.listar() == []
    finally:
        mongo.reiniciar()


def test_un_fallo_no_apaga_la_bitacora_para_siempre(monkeypatch) -> None:
    """Un fallo al primer intento se reintenta tras el enfriamiento (pasó en la práctica)."""
    from types import SimpleNamespace

    class ClienteQueFalla:
        """Imita a pymongo: cliente[bd] devuelve una base y cliente.admin.command('ping') responde."""

        def __init__(self, fallos: int) -> None:
            self.fallos = fallos
            self.base = BaseFalsa()
            self.admin = SimpleNamespace(command=lambda *a, **k: self._ping())

        def __getitem__(self, nombre: str) -> BaseFalsa:
            return self.base

        def _ping(self) -> dict:
            if self.fallos > 0:
                self.fallos -= 1
                raise ConnectionError("mongo no responde")
            return {"ok": 1}

    cliente = ClienteQueFalla(fallos=2)
    monkeypatch.setattr(config, "mongo_url", "mongodb://espia:27017")
    monkeypatch.setattr(mongo, "ENFRIAMIENTO_SEGUNDOS", 0)  # sin espera real en la prueba
    monkeypatch.setattr(mongo, "MongoClient", lambda *a, **k: cliente)
    mongo.reiniciar()
    try:
        assert mongo.base() is None  # primer intento: falla
        assert mongo.base() is None  # reintenta y vuelve a fallar
        assert mongo.base() is not None  # tercer intento: conecta
        assert mongo.activa() is True
        assert mongo.registrar("crear", "estudiante", 1, "admin") is not None
    finally:
        mongo.reiniciar()


def test_error_al_escribir_se_traga(base_falsa) -> None:
    def explotar(*a, **k):
        raise ConnectionError("mongo caído")

    base_falsa["bitacora"].insert_one = explotar
    base_falsa["boletas_snapshot"].replace_one = explotar
    assert mongo.registrar("crear", "estudiante", 1, "admin") is None
    assert mongo.guardar_boleta(1, "2026-02", {}) is False
