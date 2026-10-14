# ============================================================
# GS08 · Matrículas y Notas | tests/test_cache.py
# Autor: @dev | Rubrica: caching distribuido (Redis)
# Se prueba con un doble de Redis: el CI no necesita un Redis levantado.
# ============================================================
import pytest

from app import cache
from app.config import config
from tests.dobles import RedisFalso


@pytest.fixture()
def redis_falso():
    doble = RedisFalso()
    cache.forzar(doble)
    yield doble
    cache.reiniciar()


def test_guardar_obtener_y_borrar(redis_falso) -> None:
    assert cache.activa() is True
    assert cache.guardar("prueba:clave", {"total": 3}) is True
    assert cache.obtener("prueba:clave") == {"total": 3}
    assert cache.borrar("prueba:clave") == 1
    assert cache.obtener("prueba:clave") is None


def test_usa_el_ttl_configurado(redis_falso) -> None:
    cache.guardar("prueba:ttl", [1, 2, 3])
    assert redis_falso.ttls["prueba:ttl"] == config.cache_ttl_segundos
    cache.guardar("prueba:ttl-corto", [1], ttl=5)
    assert redis_falso.ttls["prueba:ttl-corto"] == 5


def test_invalidar_panel(redis_falso) -> None:
    cache.guardar(cache.CLAVE_PANEL, {"estudiantes_activos": 12})
    cache.invalidar_panel()
    assert cache.obtener(cache.CLAVE_PANEL) is None
    assert cache.CLAVE_PANEL in redis_falso.borrados


def test_apagada_responde_sin_cache_y_sin_errores() -> None:
    cache.forzar(None)
    try:
        assert cache.activa() is False
        assert cache.obtener("lo-que-sea") is None
        assert cache.guardar("lo-que-sea", {"a": 1}) is False
        assert cache.borrar("lo-que-sea") == 0
        assert cache.invalidar_panel() is None  # no revienta
    finally:
        cache.reiniciar()


def test_sin_url_no_se_conecta(monkeypatch) -> None:
    monkeypatch.setattr(config, "redis_url", "")
    cache.reiniciar()
    try:
        assert cache.cliente() is None
        assert cache.activa() is False
    finally:
        cache.reiniciar()


def test_si_redis_no_responde_queda_apagada(monkeypatch) -> None:
    monkeypatch.setattr(config, "redis_url", "redis://127.0.0.1:1/0")  # puerto cerrado
    cache.reiniciar()
    try:
        assert cache.cliente() is None
        assert cache.obtener("x") is None
    finally:
        cache.reiniciar()


def test_valor_corrupto_no_revienta(redis_falso) -> None:
    redis_falso.valores["prueba:corrupta"] = "esto-no-es-json"
    assert cache.obtener("prueba:corrupta") is None


def test_error_de_redis_se_traga(redis_falso) -> None:
    class RedisQueFalla:
        def get(self, *a):
            raise ConnectionError("redis caído")

        def set(self, *a, **k):
            raise ConnectionError("redis caído")

        def delete(self, *a):
            raise ConnectionError("redis caído")

    cache.forzar(RedisQueFalla())
    try:
        assert cache.obtener("x") is None
        assert cache.guardar("x", {"a": 1}) is False
        assert cache.borrar("x") == 0
        assert cache.invalidar_panel() is None
    finally:
        cache.reiniciar()
