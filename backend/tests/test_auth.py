# ============================================================
# GS08 · Matrículas y Notas | tests/test_auth.py
# Autor: @dev | T1.2 | Sprint 1
# C-01 (login con usuario o email), C-02 (inactivo no entra), C-03 (hash $2y$ del
# seed), C-04 (nadie desactiva su propia cuenta) y C-23 (403 por rol).
# ============================================================
from sqlalchemy import text

from app.security import generar_hash, verificar_password
from tests.conftest import ADMIN_CLAVE, ADMIN_USUARIO, HASH_SEED


def test_c03_el_hash_del_seed_corresponde_a_admin123() -> None:
    """El hash del legacy se usa tal cual: no se regenera ni se migra."""
    assert verificar_password(ADMIN_CLAVE, HASH_SEED) is True


def test_c03_el_hash_del_seed_rechaza_otra_clave() -> None:
    assert verificar_password("admin123", HASH_SEED) is False
    assert verificar_password("Admin123", HASH_SEED) is False
    assert verificar_password("", HASH_SEED) is False


def test_c03_un_hash_corrupto_no_provoca_500() -> None:
    assert verificar_password("Admin123!", "no-es-un-hash") is False
    assert verificar_password("Admin123!", "$2y$10$corto") is False


def test_c01_login_con_nombre_de_usuario(cliente) -> None:
    respuesta = cliente.post("/api/v1/auth/login", json={"usuario": ADMIN_USUARIO, "password": ADMIN_CLAVE})
    assert respuesta.status_code == 200, respuesta.text
    datos = respuesta.json()
    assert datos["access_token"]
    assert datos["token_type"] == "bearer"
    assert datos["usuario"]["rol"] == "admin"
    assert "password_hash" not in respuesta.text


def test_c01_login_con_el_email_del_seed(cliente) -> None:
    respuesta = cliente.post("/api/v1/auth/login", json={"usuario": "admin@horizonte.edu.pe", "password": ADMIN_CLAVE})
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["usuario"]["nombre_usuario"] == "admin"


def test_c01_clave_equivocada_no_emite_token(cliente) -> None:
    respuesta = cliente.post("/api/v1/auth/login", json={"usuario": ADMIN_USUARIO, "password": "clave-equivocada"})
    assert respuesta.status_code == 401
    assert "access_token" not in respuesta.text


def test_c01_usuario_inexistente_no_emite_token(cliente) -> None:
    respuesta = cliente.post("/api/v1/auth/login", json={"usuario": "no_existe", "password": ADMIN_CLAVE})
    assert respuesta.status_code == 401


def test_c01_sin_token_no_se_lee_el_listado(cliente) -> None:
    assert cliente.get("/api/v1/estudiantes").status_code == 401
    assert cliente.get("/api/v1/dashboard").status_code == 401
    assert cliente.get("/api/v1/matriculas").status_code == 401


def test_c01_token_falsificado_no_sirve(cliente) -> None:
    respuesta = cliente.get("/api/v1/estudiantes", headers={"Authorization": "Bearer token.invalido.falsificado"})
    assert respuesta.status_code == 401


def test_c02_usuario_inactivo_no_entra_ni_con_la_clave_correcta(cliente, sesion) -> None:
    sesion.execute(
        text(
            "INSERT INTO usuarios (nombre_usuario, email, password_hash, nombre_completo, rol, estado) "
            "VALUES ('qa_inactivo', 'qa_inactivo@horizonte.edu.pe', :hash, 'QA Inactivo', 'asistente', false)"
        ),
        {"hash": generar_hash("Clave1234")},
    )
    sesion.commit()
    try:
        respuesta = cliente.post("/api/v1/auth/login", json={"usuario": "qa_inactivo", "password": "Clave1234"})
        assert respuesta.status_code == 401, respuesta.text
        assert "access_token" not in respuesta.text
        assert "desactivada" in respuesta.json()["detail"].lower()
    finally:
        sesion.execute(text("DELETE FROM usuarios WHERE nombre_usuario = 'qa_inactivo'"))
        sesion.commit()


def test_c04_no_puedo_desactivar_mi_propia_cuenta_por_put(cliente, cabecera, token) -> None:
    identidad = cliente.get("/api/v1/auth/yo", headers=cabecera).json()
    respuesta = cliente.put(f"/api/v1/usuarios/{identidad['id']}", json={"estado": False}, headers=cabecera)
    assert respuesta.status_code == 409, respuesta.text
    assert "propia cuenta" in respuesta.json()["detail"]
    # la fila sigue intacta: el token sigue sirviendo
    assert cliente.get("/api/v1/auth/yo", headers=cabecera).status_code == 200


def test_c04_no_puedo_eliminar_mi_propia_cuenta(cliente, cabecera) -> None:
    identidad = cliente.get("/api/v1/auth/yo", headers=cabecera).json()
    respuesta = cliente.delete(f"/api/v1/usuarios/{identidad['id']}", headers=cabecera)
    assert respuesta.status_code == 409, respuesta.text
    assert cliente.get("/api/v1/auth/yo", headers=cabecera).status_code == 200


def test_c23_un_asistente_recibe_403_en_usuarios(cliente, sesion, cabecera) -> None:
    sesion.execute(
        text(
            "INSERT INTO usuarios (nombre_usuario, email, password_hash, nombre_completo, rol, estado) "
            "VALUES ('qa_asistente_rol', 'qa_asistente_rol@horizonte.edu.pe', :hash, 'QA Asistente', 'asistente', true)"
        ),
        {"hash": generar_hash("Clave1234")},
    )
    sesion.commit()
    try:
        login = cliente.post("/api/v1/auth/login", json={"usuario": "qa_asistente_rol", "password": "Clave1234"})
        assert login.status_code == 200, login.text
        asistente = {"Authorization": f"Bearer {login.json()['access_token']}"}

        assert cliente.get("/api/v1/usuarios", headers=asistente).status_code == 403
        # el mismo asistente sí puede trabajar en los módulos del día a día
        assert cliente.get("/api/v1/estudiantes", headers=asistente).status_code == 200
        assert cliente.get("/api/v1/dashboard", headers=asistente).status_code == 200
        assert cliente.get("/api/v1/usuarios", headers=cabecera).status_code == 200
    finally:
        sesion.execute(text("DELETE FROM usuarios WHERE nombre_usuario = 'qa_asistente_rol'"))
        sesion.commit()


def test_c22_contrasena_corta_y_rol_invalido_dan_422(cliente, cabecera) -> None:
    corta = cliente.post(
        "/api/v1/usuarios",
        json={
            "nombre_usuario": "qa_corto",
            "email": "qa_corto@horizonte.edu.pe",
            "password": "1234567",
            "nombre_completo": "QA Corto",
            "rol": "asistente",
        },
        headers=cabecera,
    )
    assert corta.status_code == 422, corta.text
    assert "password" in corta.json()["detail"]

    rol = cliente.post(
        "/api/v1/usuarios",
        json={
            "nombre_usuario": "qa_rol",
            "email": "qa_rol@horizonte.edu.pe",
            "password": "Clave1234",
            "nombre_completo": "QA Rol",
            "rol": "docente",
        },
        headers=cabecera,
    )
    assert rol.status_code == 422, rol.text


def test_c22_usuario_repetido_da_409(cliente, cabecera) -> None:
    respuesta = cliente.post(
        "/api/v1/usuarios",
        json={
            "nombre_usuario": ADMIN_USUARIO,
            "email": "otro@horizonte.edu.pe",
            "password": "Clave1234",
            "nombre_completo": "Otro Admin",
            "rol": "admin",
        },
        headers=cabecera,
    )
    assert respuesta.status_code == 409, respuesta.text
