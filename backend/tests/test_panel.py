# ============================================================
# GS08 · Matrículas y Notas | tests/test_panel.py
# Autor: @dev | T1.4 | Sprint 1
# C-05 (KPIs 12/7/23/1 + top 5 + últimos 6), C-06 (el top sale de la vista y su
# suma es ≤ matrículas activas) y C-07 (sin matrículas el top es [] y no es error).
# ============================================================
from sqlalchemy import text

from tests.conftest import ADMIN_CLAVE, ADMIN_USUARIO


def test_c05_kpis_del_seed_y_top_cinco(cliente, cabecera) -> None:
    respuesta = cliente.get("/api/v1/dashboard", headers=cabecera)
    assert respuesta.status_code == 200, respuesta.text
    datos = respuesta.json()

    assert datos["estudiantes_activos"] == 12
    assert datos["cursos_activos"] == 7
    assert datos["matriculas_activas"] == 23
    assert datos["usuarios_activos"] == 1

    assert len(datos["top_cursos"]) == 5
    assert datos["top_cursos"][0]["codigo"] == "C101"
    assert datos["top_cursos"][0]["matriculas"] == 5
    assert len(datos["ultimos_estudiantes"]) == 6
    assert all("codigo" in e and "nombre_completo" in e for e in datos["ultimos_estudiantes"])


def test_c06_el_top_sale_de_la_vista_y_su_suma_no_pasa_de_las_activas(cliente, cabecera, sesion) -> None:
    datos = cliente.get("/api/v1/dashboard", headers=cabecera).json()
    suma_top = sum(c["matriculas"] for c in datos["top_cursos"])
    assert suma_top <= datos["matriculas_activas"] == 23

    # el mismo agrupado, calculado directo contra la vista (no contra un conteo paralelo)
    filas = sesion.execute(
        text(
            "SELECT codigo_curso, count(*) AS matriculas FROM v_matriculas_detalle "
            "WHERE estado_matricula = 'activa' GROUP BY codigo_curso, curso "
            "ORDER BY matriculas DESC, curso LIMIT 5"
        )
    ).all()
    assert [(f[0], f[1]) for f in filas] == [(c["codigo"], c["matriculas"]) for c in datos["top_cursos"]]
    assert suma_top == 19  # C101 5 · C102 4 · C201 4 · C203 3 · C204 3


def test_c07_sin_matriculas_el_top_es_vacio_y_responde_200(cliente, cabecera, sesion) -> None:
    """Se vacía la tabla a propósito y se restaura tal cual estaba (ids incluidos)."""
    guardadas = sesion.execute(
        text("SELECT id, estudiante_id, curso_id, periodo, fecha_matricula, estado FROM matriculas ORDER BY id")
    ).all()
    assert len(guardadas) == 24
    try:
        sesion.execute(text("DELETE FROM matriculas"))
        sesion.commit()
        respuesta = cliente.get("/api/v1/dashboard", headers=cabecera)
        assert respuesta.status_code == 200, respuesta.text
        datos = respuesta.json()
        assert datos["top_cursos"] == []
        assert datos["matriculas_activas"] == 0
        assert datos["estudiantes_activos"] == 12  # los estudiantes no se tocan
    finally:
        for fila in guardadas:
            sesion.execute(
                text(
                    "INSERT INTO matriculas (id, estudiante_id, curso_id, periodo, fecha_matricula, estado) "
                    "VALUES (:id, :e, :c, :p, :f, :s)"
                ),
                {"id": fila[0], "e": fila[1], "c": fila[2], "p": fila[3], "f": fila[4], "s": fila[5]},
            )
        sesion.execute(text("SELECT setval(pg_get_serial_sequence('matriculas','id'), (SELECT max(id) FROM matriculas))"))
        sesion.commit()
    assert cliente.get("/api/v1/dashboard", headers=cabecera).json()["matriculas_activas"] == 23


def test_el_panel_exige_sesion(cliente) -> None:
    assert cliente.get("/api/v1/dashboard").status_code == 401
    token = cliente.post("/api/v1/auth/login", json={"usuario": ADMIN_USUARIO, "password": ADMIN_CLAVE}).json()["access_token"]
    assert cliente.get("/api/v1/dashboard", headers={"Authorization": f"Bearer {token}"}).status_code == 200
