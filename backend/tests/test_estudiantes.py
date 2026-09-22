# ============================================================
# GS08 · Matrículas y Notas | tests/test_estudiantes.py
# Autor: @dev | T1.3 | Sprint 1
# C-08 (misma cantidad con huaman/Huamán/HUAMAN: ILIKE + unaccent), C-09 (código y
# DNI), C-10 (paginado y 422 fuera de rango), C-11 (altas inválidas -> 422, nunca
# 500), C-12 (baja lógica) y C-30/C-32 (DELETE con matrículas -> 409 y no borra).
# ============================================================
from tests.conftest import ADMIN_CLAVE, ADMIN_USUARIO


def _alta(cliente, cabecera, codigo: str, dni: str, **extra) -> dict:
    cuerpo = {"codigo": codigo, "dni": dni, "nombres": "Prueba", "apellidos": "Automatica"}
    cuerpo.update(extra)
    return cliente.post("/api/v1/estudiantes", json=cuerpo, headers=cabecera)


def _activos(cliente, cabecera) -> int:
    return cliente.get("/api/v1/dashboard", headers=cabecera).json()["estudiantes_activos"]


def test_c08_huaman_huaman_y_huaman_devuelven_lo_mismo(cliente, cabecera) -> None:
    """BUG-07: con LIKE/ILIKE sin unaccent esto sería 0 / 1 / 0."""
    resultados = {}
    for texto in ("huaman", "Huamán", "HUAMAN"):
        respuesta = cliente.get("/api/v1/estudiantes", params={"q": texto}, headers=cabecera)
        assert respuesta.status_code == 200, respuesta.text
        resultados[texto] = respuesta.json()["total"]
    assert resultados["huaman"] == resultados["Huamán"] == resultados["HUAMAN"], resultados
    assert resultados["huaman"] >= 1, resultados
    assert "Quispe Huamán" in cliente.get("/api/v1/estudiantes", params={"q": "huaman"}, headers=cabecera).text


def test_c09_busqueda_por_codigo_y_por_dni_del_seed(cliente, cabecera) -> None:
    por_codigo = cliente.get("/api/v1/estudiantes", params={"q": "E20260001"}, headers=cabecera).json()
    assert por_codigo["total"] == 1
    assert por_codigo["estudiantes"][0]["apellidos"] == "Ramírez Torres"

    por_dni = cliente.get("/api/v1/estudiantes", params={"q": "45123456"}, headers=cabecera).json()
    assert por_dni["total"] == 1
    assert por_dni["estudiantes"][0]["codigo"] == "E20260001"


def test_c10_listado_paginado_del_seed(cliente, cabecera) -> None:
    respuesta = cliente.get("/api/v1/estudiantes", params={"page": 1, "page_size": 25}, headers=cabecera)
    assert respuesta.status_code == 200, respuesta.text
    datos = respuesta.json()
    assert datos["total"] == 12
    # el seed tiene 12 estudiantes, no 25: una página de 25 devuelve las 12 y declara el total
    assert len(datos["estudiantes"]) == 12


def test_c10_page_size_fuera_de_rango_da_422(cliente, cabecera) -> None:
    for valor in (0, 200, -1):
        respuesta = cliente.get("/api/v1/estudiantes", params={"page": 1, "page_size": valor}, headers=cabecera)
        assert respuesta.status_code == 422, f"page_size={valor} -> {respuesta.status_code}"


def test_c11_dni_de_7_digitos_da_422_y_nunca_500(cliente, cabecera, nuevo_codigo) -> None:
    respuesta = _alta(cliente, cabecera, nuevo_codigo(), "1234567")
    assert respuesta.status_code == 422, respuesta.text
    assert "dni" in respuesta.json()["detail"].lower()


def test_c11_dni_con_letras_o_guiones_da_422(cliente, cabecera, nuevo_codigo) -> None:
    for dni in ("4512345A", "4512345-", "1234 567"):
        respuesta = _alta(cliente, cabecera, nuevo_codigo(), dni)
        assert respuesta.status_code == 422, f"dni={dni} -> {respuesta.status_code}"


def test_c11_dni_repetido_y_codigo_repetido_dan_422(cliente, cabecera, nuevo_codigo, nuevo_dni) -> None:
    # DNI del seed
    repetido_dni = _alta(cliente, cabecera, nuevo_codigo(), "45123456")
    assert repetido_dni.status_code == 422, repetido_dni.text
    assert "dni" in repetido_dni.json()["detail"].lower()

    # código del seed (con un DNI válido y libre, para que el único error sea el código)
    repetido_codigo = _alta(cliente, cabecera, "E20260001", nuevo_dni())
    assert repetido_codigo.status_code == 422, repetido_codigo.text
    assert "codigo" in repetido_codigo.json()["detail"].lower()


def test_c11_email_invalido_da_422(cliente, cabecera, nuevo_codigo, nuevo_dni) -> None:
    respuesta = _alta(cliente, cabecera, nuevo_codigo(), nuevo_dni(), email="no-es-un-email")
    assert respuesta.status_code == 422, respuesta.text
    assert "email" in respuesta.json()["detail"].lower()


def test_c11_alta_valida_201_y_baja_logica(cliente, cabecera, nuevo_codigo, nuevo_dni) -> None:
    codigo, dni = nuevo_codigo(), nuevo_dni()
    antes = _activos(cliente, cabecera)

    alta = _alta(cliente, cabecera, codigo, dni)
    assert alta.status_code == 201, alta.text
    creado = alta.json()
    assert creado["id"] and creado["estado"] is True
    assert _activos(cliente, cabecera) == antes + 1

    try:
        # C-12: baja lógica -> sale del KPI, pero el registro sigue existiendo
        baja = cliente.put(
            f"/api/v1/estudiantes/{creado['id']}",
            json={"codigo": codigo, "dni": dni, "nombres": "Prueba", "apellidos": "Automatica", "estado": False},
            headers=cabecera,
        )
        assert baja.status_code == 200, baja.text
        assert _activos(cliente, cabecera) == antes
        assert cliente.get(f"/api/v1/estudiantes/{creado['id']}", headers=cabecera).status_code == 200

        inactivos = cliente.get("/api/v1/estudiantes", params={"estado": "inactivo"}, headers=cabecera).json()
        assert any(e["codigo"] == codigo for e in inactivos["estudiantes"])
        en_activos = cliente.get("/api/v1/estudiantes", params={"estado": "activo"}, headers=cabecera).json()
        assert all(e["codigo"] != codigo for e in en_activos["estudiantes"])
    finally:
        assert cliente.delete(f"/api/v1/estudiantes/{creado['id']}", headers=cabecera).status_code == 204
    assert _activos(cliente, cabecera) == antes


def test_c30_delete_con_matriculas_da_409_y_no_borra_nada(cliente, cabecera) -> None:
    """El estudiante 2 del seed tiene 2 matrículas: primero el conteo, no el borrado."""
    respuesta = cliente.delete("/api/v1/estudiantes/2", headers=cabecera)
    assert respuesta.status_code == 409, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["matriculas"] == 2, cuerpo
    assert "confirmar=true" in cuerpo["detail"]
    # no borró nada (C-32): el estudiante y sus matrículas siguen ahí
    assert cliente.get("/api/v1/estudiantes/2", headers=cabecera).status_code == 200
    assert cliente.get("/api/v1/matriculas", params={"q": "E20260002"}, headers=cabecera).json()["total"] == 2


def test_c19_estudiante_inexistente_da_404(cliente, cabecera) -> None:
    assert cliente.get("/api/v1/estudiantes/99999", headers=cabecera).status_code == 404
    assert (
        cliente.put(
            "/api/v1/estudiantes/99999",
            json={"codigo": "PZ9999", "dni": "79999999", "nombres": "No", "apellidos": "Existe"},
            headers=cabecera,
        ).status_code
        == 404
    )


def test_el_listado_no_expone_el_hash_ni_datos_de_sesion(cliente, cabecera) -> None:
    assert "password" not in cliente.get("/api/v1/estudiantes", headers=cabecera).text
    assert cliente.post("/api/v1/auth/login", json={"usuario": ADMIN_USUARIO, "password": ADMIN_CLAVE}).status_code == 200
