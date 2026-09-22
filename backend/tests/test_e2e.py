# ============================================================
# GS08 · Matrículas y Notas | tests/test_e2e.py
# Autor: @dev | T1.1 (prueba de extremo a extremo del §3) | Sprint 1
# Recorrido «de la matrícula a la nota» del alcance (pasos 1..9) contra la API real.
# El paso 10 (Grafana) y el recorrido por el navegador son de @qa/T2.4.
# ============================================================
from tests.conftest import ADMIN_CLAVE, ADMIN_USUARIO


def test_recorrido_completo_del_alcance_de_la_matricula_a_la_nota(cliente, nuevo_codigo, nuevo_dni) -> None:
    # 1. el asistente entra y ve el panel
    login = cliente.post("/api/v1/auth/login", json={"usuario": ADMIN_USUARIO, "password": ADMIN_CLAVE})
    assert login.status_code == 200, login.text
    cabecera = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # 2. el panel muestra los números del seed
    panel = cliente.get("/api/v1/dashboard", headers=cabecera).json()
    assert (panel["estudiantes_activos"], panel["cursos_activos"]) == (12, 7)
    assert (panel["matriculas_activas"], panel["usuarios_activos"]) == (23, 1)
    assert len(panel["top_cursos"]) == 5 and len(panel["ultimos_estudiantes"]) == 6

    # 3. busca huaman y encuentra a Quispe Huamán (con tilde, sin tilde, en mayúsculas)
    for texto in ("huaman", "Huamán", "HUAMAN"):
        encontrados = cliente.get("/api/v1/estudiantes", params={"q": texto}, headers=cabecera).json()
        assert encontrados["total"] == 1, encontrados

    # 4. registra un estudiante nuevo
    codigo, dni = nuevo_codigo(), nuevo_dni()
    alta = cliente.post(
        "/api/v1/estudiantes",
        json={"codigo": codigo, "dni": dni, "nombres": "Estudiante", "apellidos": "De Prueba SMP", "email": "smoke@correo.pe"},
        headers=cabecera,
    )
    assert alta.status_code == 201, alta.text
    estudiante_id = alta.json()["id"]
    assert cliente.get("/api/v1/dashboard", headers=cabecera).json()["estudiantes_activos"] == 13

    try:
        # 5. elige un curso de 3 créditos (C204 · Estadística Aplicada) y un periodo
        curso = cliente.get("/api/v1/cursos/6", headers=cabecera).json()
        assert curso["creditos"] == 3 and curso["estado"] is True

        # 6. lo matricula; el duplicado responde 409 con el mensaje del legacy
        matricula = cliente.post(
            "/api/v1/matriculas",
            json={"estudiante_id": estudiante_id, "curso_id": 6, "periodo": "2026-02", "fecha_matricula": "2026-08-20"},
            headers=cabecera,
        )
        assert matricula.status_code == 201, matricula.text
        matricula_id = matricula.json()["id"]

        duplicada = cliente.post(
            "/api/v1/matriculas",
            json={"estudiante_id": estudiante_id, "curso_id": 6, "periodo": "2026-02", "fecha_matricula": "2026-08-20"},
            headers=cabecera,
        )
        assert duplicada.status_code == 409, duplicada.text
        assert duplicada.json()["detail"] == "Ese estudiante ya está matriculado en ese curso para el periodo indicado"

        # 7. filtra por periodo y ve su matrícula con estudiante y curso resueltos
        listado = cliente.get("/api/v1/matriculas", params={"periodo": "2026-02"}, headers=cabecera).json()
        suya = next(m for m in listado["matriculas"] if m["id"] == matricula_id)
        assert suya["estudiante"] == "De Prueba SMP, Estudiante"
        assert suya["curso"] == "Estadística Aplicada"
        assert suya["estado"] == "activa"

        # 8. tres notas: práctica 14, parcial 16, final 18
        for tipo, nota in (("practica", 14), ("parcial", 16), ("final", 18)):
            nota_creada = cliente.post(
                f"/api/v1/matriculas/{matricula_id}/notas", json={"tipo": tipo, "numero": 1, "nota": nota}, headers=cabecera
            )
            assert nota_creada.status_code == 201, nota_creada.text

        # 8b. y los dos errores que el alcance exige: duplicado (409) y fuera de rango (422)
        assert (
            cliente.post(
                f"/api/v1/matriculas/{matricula_id}/notas", json={"tipo": "practica", "numero": 1, "nota": 20}, headers=cabecera
            ).status_code
            == 409
        )
        assert (
            cliente.post(
                f"/api/v1/matriculas/{matricula_id}/notas", json={"tipo": "final", "numero": 2, "nota": 21}, headers=cabecera
            ).status_code
            == 422
        )

        # 9. la boleta del periodo: nota del curso 16.00 y promedio del periodo
        boleta = cliente.get(f"/api/v1/estudiantes/{estudiante_id}/boleta", params={"periodo": "2026-02"}, headers=cabecera)
        assert boleta.status_code == 200, boleta.text
        datos = boleta.json()
        assert len(datos["cursos"]) == 1
        assert datos["cursos"][0]["nota"] == 16.0
        assert datos["cursos"][0]["nota_texto"] == "16.00"
        assert datos["promedio"] == 16.0 and datos["promedio_texto"] == "16.00"
        assert [n["tipo"] for n in datos["cursos"][0]["notas"]] == ["final", "parcial", "practica"]
    finally:
        # limpieza: el borrado definitivo es la segunda llamada explícita (C-31)
        borrado = cliente.delete(f"/api/v1/estudiantes/{estudiante_id}", params={"confirmar": "true"}, headers=cabecera)
        assert borrado.status_code == 204, borrado.text

    panel_final = cliente.get("/api/v1/dashboard", headers=cabecera).json()
    assert (panel_final["estudiantes_activos"], panel_final["matriculas_activas"]) == (12, 23)
