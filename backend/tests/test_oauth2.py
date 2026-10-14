# ============================================================
# GS08 · Matrículas y Notas | tests/test_oauth2.py
# Autor: @dev | Rúbrica: "autenticación y autorización con OAuth2, JWT y roles RBAC"
# Se prueba el flujo completo: token con scopes, errores con la forma del RFC 6749,
# y que cada endpoint exija su scope (403 `insufficient_scope` si falta).
# ============================================================
import jwt
import pytest
from sqlalchemy import text

from app.config import config
from app.security import generar_hash
from tests.conftest import ADMIN_CLAVE, ADMIN_USUARIO

RUTA = "/api/v1/auth/token"


def pedir_token(
    cliente, usuario=ADMIN_USUARIO, password=ADMIN_CLAVE, scope=None, client_id=None, client_secret=None, grant_type="password"
):
    datos = {
        "grant_type": grant_type,
        "username": usuario,
        "password": password,
        "client_id": config.oauth_client_id if client_id is None else client_id,
        "client_secret": config.oauth_client_secret if client_secret is None else client_secret,
    }
    if scope:
        datos["scope"] = " ".join(scope) if isinstance(scope, (list, tuple)) else scope
    return cliente.post(RUTA, data=datos)  # OAuth2 va en formulario, no en JSON


def contenido(token: str) -> dict:
    return jwt.decode(token, config.secret_key, algorithms=[config.algoritmo_token])


def cabecera(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_el_token_lleva_los_scopes_del_rol(cliente) -> None:
    respuesta = pedir_token(cliente)
    assert respuesta.status_code == 200, respuesta.text
    datos = respuesta.json()
    assert datos["token_type"] == "bearer"
    assert datos["expires_in"] == config.access_token_expire_minutes * 60
    scopes = datos["scope"].split()
    assert "usuarios:admin" in scopes and "matriculas:escribir" in scopes and "auditoria:leer" in scopes
    assert contenido(datos["access_token"])["scp"] == sorted(scopes)


def test_sin_scope_se_firman_todos_los_del_rol(cliente, sesion, cabecera) -> None:
    """Un asistente recibe los de su rol: ni usuarios ni auditoría."""
    identificador = sesion.execute(
        text(
            "INSERT INTO usuarios (nombre_usuario, email, password_hash, nombre_completo, rol, estado) "
            "VALUES ('qa_oauth_asistente', 'qa_oauth@horizonte.edu.pe', :hash, 'QA OAuth', 'asistente', true) "
            "RETURNING id"
        ),
        {"hash": generar_hash("Clave1234")},
    ).scalar_one()
    sesion.commit()
    try:
        respuesta = pedir_token(cliente, "qa_oauth_asistente", "Clave1234")
        assert respuesta.status_code == 200, respuesta.text
        scopes = set(respuesta.json()["scope"].split())
        assert "estudiantes:escribir" in scopes
        assert "usuarios:admin" not in scopes
        assert "auditoria:leer" not in scopes
        assert "estudiantes:eliminar" not in scopes
    finally:
        sesion.execute(text("DELETE FROM usuarios WHERE id = :id"), {"id": identificador})
        sesion.commit()


def test_el_scope_pedido_se_respeta_y_limita_el_token(cliente, nuevo_codigo, nuevo_dni) -> None:
    respuesta = pedir_token(cliente, scope=["estudiantes:leer"])
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["scope"] == "estudiantes:leer"
    token = respuesta.json()["access_token"]

    assert cliente.get("/api/v1/estudiantes", headers=cabecera(token)).status_code == 200
    # el mismo token no puede escribir: 403 con el error estándar
    alta = cliente.post(
        "/api/v1/estudiantes",
        json={"codigo": nuevo_codigo(), "dni": nuevo_dni(), "nombres": "SIN", "apellidos": "PERMISO"},
        headers=cabecera(token),
    )
    assert alta.status_code == 403, alta.text
    cuerpo = alta.json()
    assert cuerpo["error"] == "insufficient_scope"
    assert "estudiantes:escribir" in cuerpo["error_description"]
    assert "insufficient_scope" in alta.headers["WWW-Authenticate"]


def test_pedir_un_scope_que_no_existe_da_invalid_scope(cliente) -> None:
    respuesta = pedir_token(cliente, scope=["volcan:explotar"])
    assert respuesta.status_code == 400, respuesta.text
    assert respuesta.json()["error"] == "invalid_scope"
    assert "volcan:explotar" in respuesta.json()["error_description"]


def test_el_scope_inexistente_tambien_da_invalid_scope_para_el_asistente(cliente, sesion) -> None:
    identificador = sesion.execute(
        text(
            "INSERT INTO usuarios (nombre_usuario, email, password_hash, nombre_completo, rol, estado) "
            "VALUES ('qa_oauth_scope', 'qa_oauth_scope@horizonte.edu.pe', :hash, 'QA Scope', 'asistente', true) "
            "RETURNING id"
        ),
        {"hash": generar_hash("Clave1234")},
    ).scalar_one()
    sesion.commit()
    try:
        respuesta = pedir_token(cliente, "qa_oauth_scope", "Clave1234", scope=["auditoria:leer"])
        assert respuesta.status_code == 400, respuesta.text
        assert respuesta.json()["error"] == "invalid_scope"
    finally:
        sesion.execute(text("DELETE FROM usuarios WHERE id = :id"), {"id": identificador})
        sesion.commit()


def test_el_cliente_publico_no_necesita_secreto(cliente) -> None:
    """El SPA es cliente público: con usuario y contraseña alcanza (sin client_id)."""
    respuesta = cliente.post(RUTA, data={"grant_type": "password", "username": ADMIN_USUARIO, "password": ADMIN_CLAVE})
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["token_type"] == "bearer"


def test_credenciales_de_cliente_incorrectas(cliente) -> None:
    respuesta = pedir_token(cliente, client_secret="no-es-el-secreto")
    assert respuesta.status_code == 401, respuesta.text
    assert respuesta.json()["error"] == "invalid_client"
    assert "invalid_client" in respuesta.headers["WWW-Authenticate"]

    otra = pedir_token(cliente, client_id="otro-cliente")
    assert otra.status_code == 401
    assert otra.json()["error"] == "invalid_client"


def test_password_incorrecta_da_invalid_grant(cliente) -> None:
    respuesta = pedir_token(cliente, password="clave-que-no-es")
    assert respuesta.status_code == 400, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["error"] == "invalid_grant"
    assert "incorrectos" in cuerpo["error_description"]


def test_usuario_desactivado_no_recibe_token(cliente, sesion) -> None:
    identificador = sesion.execute(
        text(
            "INSERT INTO usuarios (nombre_usuario, email, password_hash, nombre_completo, rol, estado) "
            "VALUES ('qa_oauth_inactivo', 'qa_oauth_inactivo@horizonte.edu.pe', :hash, 'QA Inactivo', 'asistente', false) "
            "RETURNING id"
        ),
        {"hash": generar_hash("Clave1234")},
    ).scalar_one()
    sesion.commit()
    try:
        respuesta = pedir_token(cliente, "qa_oauth_inactivo", "Clave1234")
        assert respuesta.status_code == 400, respuesta.text
        assert respuesta.json()["error"] == "invalid_grant"
        assert "desactivada" in respuesta.json()["error_description"].lower()
    finally:
        sesion.execute(text("DELETE FROM usuarios WHERE id = :id"), {"id": identificador})
        sesion.commit()


def test_grant_type_no_soportado(cliente) -> None:
    respuesta = pedir_token(cliente, grant_type="client_credentials")
    assert respuesta.status_code == 400, respuesta.text
    assert respuesta.json()["error"] == "unsupported_grant_type"


def test_el_endpoint_espera_formulario_no_json(cliente) -> None:
    """OAuth2 define form-urlencoded: con JSON responde 422 (documentado a propósito)."""
    respuesta = cliente.post(
        RUTA,
        json={"grant_type": "password", "username": ADMIN_USUARIO, "password": ADMIN_CLAVE},
    )
    assert respuesta.status_code == 422


def test_el_login_del_spa_sigue_funcionando_y_su_token_trae_scopes(cliente, cabecera) -> None:
    respuesta = cliente.post("/api/v1/auth/login", json={"usuario": ADMIN_USUARIO, "password": ADMIN_CLAVE})
    assert respuesta.status_code == 200, respuesta.text
    assert "usuarios:admin" in contenido(respuesta.json()["access_token"])["scp"]
    assert cliente.get("/api/v1/dashboard", headers=cabecera).status_code == 200
    assert cliente.get("/api/v1/auth/yo", headers=cabecera).status_code == 200


def test_el_token_de_oauth2_sirve_igual_en_el_resto_del_api(cliente) -> None:
    token = pedir_token(cliente).json()["access_token"]
    assert cliente.get("/api/v1/dashboard", headers=cabecera(token)).status_code == 200
    assert cliente.get("/api/v1/estudiantes?q=huaman", headers=cabecera(token)).status_code == 200
    assert cliente.get("/api/v1/auditoria", headers=cabecera(token)).status_code == 200
    # y en GraphQL, que exige token válido igual que el REST
    consulta = cliente.post("/graphql", json={"query": "{ panel { estudiantesActivos } }"}, headers=cabecera(token))
    assert consulta.status_code == 200 and "errors" not in consulta.json()


def test_sin_token_sigue_dando_401(cliente) -> None:
    assert cliente.get("/api/v1/estudiantes").status_code == 401
    assert cliente.get("/api/v1/estudiantes", headers={"Authorization": "Bearer inventado"}).status_code == 401


def test_un_asistente_no_administra_usuarios_ni_borra_estudiantes(cliente, sesion) -> None:
    identificador = sesion.execute(
        text(
            "INSERT INTO usuarios (nombre_usuario, email, password_hash, nombre_completo, rol, estado) "
            "VALUES ('qa_oauth_rbac', 'qa_oauth_rbac@horizonte.edu.pe', :hash, 'QA RBAC', 'asistente', true) "
            "RETURNING id"
        ),
        {"hash": generar_hash("Clave1234")},
    ).scalar_one()
    sesion.commit()
    try:
        token = pedir_token(cliente, "qa_oauth_rbac", "Clave1234").json()["access_token"]
        assert cliente.get("/api/v1/usuarios", headers=cabecera(token)).status_code == 403
        assert cliente.get("/api/v1/auditoria", headers=cabecera(token)).status_code == 403
        assert cliente.delete("/api/v1/estudiantes/1", params={"confirmar": "true"}, headers=cabecera(token)).status_code == 403
        # lo que sí puede: leer y escribir en los módulos del día a día
        assert cliente.get("/api/v1/estudiantes", headers=cabecera(token)).status_code == 200
        assert cliente.get("/api/v1/matriculas", headers=cabecera(token)).status_code == 200
    finally:
        sesion.execute(text("DELETE FROM usuarios WHERE id = :id"), {"id": identificador})
        sesion.commit()


def test_la_bitacora_guarda_el_token_sin_la_contrasena(cliente, base_falsa) -> None:
    respuesta = pedir_token(cliente)
    assert respuesta.status_code == 200, respuesta.text
    documentos = base_falsa["bitacora"].documentos
    assert len(documentos) == 1
    registro = documentos[0]
    assert registro["entidad"] == "sesión"
    assert registro["accion"] == "crear"
    assert registro["datos"]["cuerpo"]["password"] == "***"
    assert registro["datos"]["cuerpo"]["client_secret"] == "***"
    assert registro["datos"]["cuerpo"]["username"] == ADMIN_USUARIO
    texto = str(documentos)
    assert ADMIN_CLAVE not in texto and config.oauth_client_secret not in texto


@pytest.fixture()
def base_falsa():
    from app import mongo
    from tests.dobles import BaseFalsa

    base = BaseFalsa()
    mongo.forzar("conexion-de-prueba", base)
    yield base
    mongo.reiniciar()
