# ============================================================
# GS08 · Matrículas y Notas | app/routers/usuarios.py
# Autor: @dev | T2.2 (adelanta C-04/RN-11 que T1.2 exige) | Sprint 1
# CU-13 / C-22, C-23 y RN-11:
#   * todo /api/v1/usuarios es solo del rol admin -> 403 para asistente (C-23)
#   * nombre_usuario / email repetido -> 409; contraseña < 8 -> 422; rol inválido -> 422
#   * nadie desactiva ni elimina su propia cuenta -> 409 (C-04, regla de usuarios/edit.php)
# ============================================================
import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import solo_admin
from app.models import Usuario
from app.schemas import UsuarioActualizar, UsuarioEntrada, UsuarioSalida
from app.security import generar_hash

log = logging.getLogger("gs08.usuarios")
router = APIRouter(prefix="/api/v1/usuarios", tags=["usuarios"])

MENSAJE_PROPIA_CUENTA = "No puedes desactivar ni eliminar tu propia cuenta (RN-11)."


def _duplicados(db: Session, nombre_usuario: str | None, email: str | None, propio_id: int | None = None) -> None:
    condiciones, parametros = [], {}
    if nombre_usuario:
        condiciones.append("nombre_usuario = :nombre_usuario")
        parametros["nombre_usuario"] = nombre_usuario
    if email:
        condiciones.append("lower(email) = lower(:email)")
        parametros["email"] = email
    if not condiciones:
        return
    parametros["propio"] = propio_id
    fila = (
        db.execute(
            text(
                f"SELECT id, nombre_usuario, email FROM usuarios WHERE ({' OR '.join(condiciones)}) "
                "AND (CAST(:propio AS integer) IS NULL OR id <> CAST(:propio AS integer))"
            ),
            parametros,
        )
        .mappings()
        .first()
    )
    if fila is None:
        return
    if nombre_usuario and fila["nombre_usuario"] == nombre_usuario:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un usuario con ese nombre de usuario.")
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un usuario con ese email.")


@router.get("", response_model=list[UsuarioSalida])
def listar(db: Session = Depends(get_db), _: Usuario = Depends(solo_admin)) -> list[dict]:
    usuarios = (
        db.execute(text("SELECT id, nombre_usuario, email, nombre_completo, rol, estado, creado_en FROM usuarios ORDER BY id"))
        .mappings()
        .all()
    )
    return [dict(u) for u in usuarios]


@router.get("/{usuario_id}", response_model=UsuarioSalida)
def obtener(usuario_id: int, db: Session = Depends(get_db), _: Usuario = Depends(solo_admin)) -> dict:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No existe el usuario {usuario_id}.")
    return usuario.como_diccionario()


@router.post("", response_model=UsuarioSalida, status_code=status.HTTP_201_CREATED)
def crear(datos: UsuarioEntrada, db: Session = Depends(get_db), _: Usuario = Depends(solo_admin)) -> dict:
    _duplicados(db, datos.nombre_usuario, datos.email)
    usuario = Usuario(
        nombre_usuario=datos.nombre_usuario,
        email=datos.email,
        password_hash=generar_hash(datos.password),
        nombre_completo=datos.nombre_completo,
        rol=datos.rol,
        estado=datos.estado,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    log.info("usuario creado id=%s rol=%s", usuario.id, usuario.rol)
    return usuario.como_diccionario()


@router.put("/{usuario_id}", response_model=UsuarioSalida)
def actualizar(
    usuario_id: int,
    datos: UsuarioActualizar,
    db: Session = Depends(get_db),
    usuario_sesion: Usuario = Depends(solo_admin),
) -> dict:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No existe el usuario {usuario_id}.")
    cambios = datos.model_dump(exclude_unset=True)

    if usuario_id == usuario_sesion.id and cambios.get("estado") is False:
        # C-04 / RN-11
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=MENSAJE_PROPIA_CUENTA)

    _duplicados(db, None, cambios.get("email"), propio_id=usuario_id)
    if "password" in cambios:
        usuario.password_hash = generar_hash(cambios.pop("password"))
    for campo, valor in cambios.items():
        setattr(usuario, campo, valor)
    db.commit()
    db.refresh(usuario)
    return usuario.como_diccionario()


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_sesion: Usuario = Depends(solo_admin),
) -> Response:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No existe el usuario {usuario_id}.")
    if usuario_id == usuario_sesion.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=MENSAJE_PROPIA_CUENTA)
    db.delete(usuario)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
