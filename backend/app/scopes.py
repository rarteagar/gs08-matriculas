# ============================================================
# GS08 · Matrículas y Notas | app/scopes.py
# Autor: @dev | Rúbrica: "autenticación y autorización con OAuth2, JWT y roles RBAC"
# El rol NO autoriza por sí solo: el rol ASIGNA scopes, y el API autoriza por scope.
# Así el token dice qué puede hacer («matriculas:escribir») y cada endpoint pide el suyo.
#
# Reparto por rol (idéntico al comportamiento anterior, cuando existía `solo_admin`):
#   * admin     -> todos los scopes
#   * asistente -> leer todo y escribir estudiantes, cursos, matrículas y notas.
#                  NO puede eliminar estudiantes/cursos/matrículas, ni tocar usuarios,
#                  ni leer la bitácora: eso quedó como estaba (antes: 403 de solo_admin).
# ============================================================

# scope -> descripción (sale tal cual en Swagger, en el botón Authorize)
SCOPES: dict[str, str] = {
    "perfil:leer": "Ver la propia sesión (/auth/yo)",
    "panel:leer": "Ver los indicadores del panel",
    "estudiantes:leer": "Listar y ver estudiantes",
    "estudiantes:escribir": "Crear y editar estudiantes",
    "estudiantes:eliminar": "Eliminar estudiantes (arrastra sus matrículas)",
    "cursos:leer": "Listar y ver cursos",
    "cursos:escribir": "Crear y editar cursos",
    "cursos:eliminar": "Eliminar cursos (arrastra sus matrículas)",
    "matriculas:leer": "Listar y ver matrículas",
    "matriculas:escribir": "Crear y editar matrículas",
    "matriculas:eliminar": "Eliminar matrículas (arrastra sus notas)",
    "notas:leer": "Ver las notas de una matrícula",
    "notas:escribir": "Registrar, editar y borrar notas",
    "boleta:leer": "Emitir y consultar boletas",
    "usuarios:admin": "Administrar usuarios del sistema",
    "auditoria:leer": "Consultar la bitácora documental",
}

ASISTENTE = {
    "perfil:leer",
    "panel:leer",
    "estudiantes:leer",
    "estudiantes:escribir",
    "cursos:leer",
    "cursos:escribir",
    "matriculas:leer",
    "matriculas:escribir",
    "notas:leer",
    "notas:escribir",
    "boleta:leer",
}

POR_ROL: dict[str, set[str]] = {
    "admin": set(SCOPES),
    "asistente": ASISTENTE,
}


def de_rol(rol: str) -> list[str]:
    """Todos los scopes que le corresponden a un rol, en orden estable."""
    return sorted(POR_ROL.get(rol, set()))


def revisar(rol: str, pedidos: list[str] | None) -> list[str]:
    """Devuelve los scopes que se van a firmar.

    Sin `scope` en la petición se firman todos los del rol (cómodo para el SPA propio).
    Si piden uno que el rol no tiene, se lanza el error estándar `invalid_scope`.
    """
    permitidos = POR_ROL.get(rol, set())
    if not pedidos:
        return sorted(permitidos)
    desconocidos = [pedido for pedido in pedidos if pedido not in SCOPES]
    no_permitidos = [pedido for pedido in pedidos if pedido not in permitidos]
    if desconocidos or no_permitidos:
        from app.errores_oauth import error_oauth  # import local: evita ciclo con deps

        malos = sorted(set(desconocidos + no_permitidos))
        raise error_oauth(
            "invalid_scope",
            f"El rol '{rol}' no tiene estos permisos: {', '.join(malos)}.",
            estado=400,
            scope=" ".join(sorted(permitidos)),
        )
    return sorted(set(pedidos))
