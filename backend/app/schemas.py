# ============================================================
# GS08 · Matrículas y Notas | app/schemas.py
# Autor: @dev | T1.1–T1.4 | Sprint 1
# Contratos de entrada/salida. Cada validación repite una regla de
# docs/analisis/modelo-datos.md §3 y da el mensaje en español con el campo, que
# es lo que el SPA muestra en pantalla (T2.4) y lo que exige C-11.
#
# numeric(4,2): en JSON sale como número (14.0) y además como texto con los dos
# decimales fijos (14.00) porque C-27 habla de «16.00» y la pantalla lo muestra
# así. Decisión pedida en el handoff de T1.5.
# ============================================================
import math
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

PATRON_DNI = r"^\d{8}$"
PATRON_EMAIL = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
PATRON_PERIODO = r"^\d{4}-(0[1-9]|1[0-2])$"
PATRON_USUARIO = r"^[A-Za-z0-9_.]{3,50}$"

MENSAJE_DNI = "El DNI debe tener exactamente 8 dígitos numéricos (ej. 45123456)."
MENSAJE_PERIODO = "El periodo debe tener el formato AAAA-MM con mes 01..12 (ej. 2026-02)."
MENSAJE_EMAIL = "El email no tiene un formato válido (ej. nombre@dominio.pe)."
MENSAJE_USUARIO = "El nombre de usuario debe tener entre 3 y 50 caracteres: letras, números, punto o guion bajo."


def _texto_o_none(valor: object) -> object:
    if isinstance(valor, str) and not valor.strip():
        return None
    return valor


def paginas(total: int, page_size: int) -> int:
    return max(1, math.ceil(total / page_size)) if total else 0


class BaseEstricta(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


# ------------------------------------------------------------
# Salud
# ------------------------------------------------------------
class SaludSalida(BaseModel):
    status: str
    motor: str
    instancia: str
    entorno: str


# ------------------------------------------------------------
# Autenticación (CU-01 / C-01..C-04)
# ------------------------------------------------------------
class LoginEntrada(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    usuario: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=128)


class UsuarioSalida(BaseModel):
    id: int
    nombre_usuario: str
    email: str
    nombre_completo: str
    rol: str
    estado: bool
    creado_en: datetime | None = None


class LoginSalida(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expira_en: datetime
    expira_en_minutos: int
    usuario: UsuarioSalida


# ------------------------------------------------------------
# Estudiantes (CU-03..CU-06 / C-08..C-12)
# ------------------------------------------------------------
class EstudianteEntrada(BaseEstricta):
    codigo: str = Field(min_length=1, max_length=20)
    dni: str
    nombres: str = Field(min_length=1, max_length=80)
    apellidos: str = Field(min_length=1, max_length=80)
    email: str | None = Field(default=None, max_length=100)
    telefono: str | None = Field(default=None, max_length=20)
    fecha_nacimiento: date | None = None
    direccion: str | None = Field(default=None, max_length=150)
    estado: bool = True

    @field_validator("codigo", "dni", mode="before")
    @classmethod
    def numero_a_texto(cls, valor: object) -> object:
        return str(valor) if isinstance(valor, int) else valor

    @field_validator("email", "telefono", "direccion", mode="before")
    @classmethod
    def vacio_es_none(cls, valor: object) -> object:
        return _texto_o_none(valor)

    @field_validator("codigo")
    @classmethod
    def codigo_no_vacio(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("El código del estudiante es obligatorio.")
        return valor

    @field_validator("dni")
    @classmethod
    def dni_ocho_digitos(cls, valor: str) -> str:
        if not re.match(PATRON_DNI, valor or ""):
            raise ValueError(MENSAJE_DNI)
        return valor

    @field_validator("email")
    @classmethod
    def email_valido(cls, valor: str | None) -> str | None:
        if valor is not None and not re.match(PATRON_EMAIL, valor):
            raise ValueError(MENSAJE_EMAIL)
        return valor

    @field_validator("fecha_nacimiento")
    @classmethod
    def nacimiento_real(cls, valor: date | None) -> date | None:
        if valor is not None and valor <= date(1900, 1, 1):
            raise ValueError("La fecha de nacimiento debe ser posterior al 01/01/1900.")
        return valor


class EstudianteSalida(BaseModel):
    id: int
    codigo: str
    dni: str
    nombres: str
    apellidos: str
    nombre_completo: str
    email: str | None = None
    telefono: str | None = None
    fecha_nacimiento: date | None = None
    direccion: str | None = None
    estado: bool
    creado_en: datetime | None = None


class PaginaEstudiantes(BaseModel):
    total: int
    page: int
    page_size: int
    paginas: int
    estudiantes: list[EstudianteSalida]


# ------------------------------------------------------------
# Cursos (CU-07..CU-08 / C-13..C-15)
# ------------------------------------------------------------
class CursoEntrada(BaseEstricta):
    codigo: str = Field(min_length=1, max_length=20)
    nombre: str = Field(min_length=1, max_length=100)
    descripcion: str | None = None
    # C-13: si no se envía, se guarda el default del legacy (3 créditos / 48 horas)
    creditos: int = 3
    horas: int = 48
    estado: bool = True

    @field_validator("descripcion", mode="before")
    @classmethod
    def vacio_es_none(cls, valor: object) -> object:
        return _texto_o_none(valor)

    @field_validator("creditos")
    @classmethod
    def creditos_en_rango(cls, valor: int) -> int:
        if not 1 <= valor <= 10:
            raise ValueError("Los créditos deben estar entre 1 y 10 (regla del legacy, RN-02).")
        return valor

    @field_validator("horas")
    @classmethod
    def horas_en_rango(cls, valor: int) -> int:
        if not 1 <= valor <= 1000:
            raise ValueError("Las horas deben estar entre 1 y 1000 (RN-02).")
        return valor


class CursoSalida(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: str | None = None
    creditos: int
    horas: int
    estado: bool
    creado_en: datetime | None = None


class PaginaCursos(BaseModel):
    total: int
    page: int
    page_size: int
    paginas: int
    cursos: list[CursoSalida]


# ------------------------------------------------------------
# Matrículas (CU-09..CU-12 / C-16..C-21)
# ------------------------------------------------------------
class MatriculaEntrada(BaseEstricta):
    estudiante_id: int = Field(ge=1)
    curso_id: int = Field(ge=1)
    periodo: str
    fecha_matricula: date
    estado: Literal["activa", "retirado"] = "activa"

    @field_validator("periodo")
    @classmethod
    def periodo_aaaamm(cls, valor: str) -> str:
        if not re.match(PATRON_PERIODO, valor or ""):
            raise ValueError(MENSAJE_PERIODO)
        return valor


class MatriculaActualizar(BaseEstricta):
    estudiante_id: int | None = Field(default=None, ge=1)
    curso_id: int | None = Field(default=None, ge=1)
    periodo: str | None = None
    fecha_matricula: date | None = None
    estado: Literal["activa", "retirado"] | None = None

    @field_validator("periodo")
    @classmethod
    def periodo_aaaamm(cls, valor: str | None) -> str | None:
        if valor is not None and not re.match(PATRON_PERIODO, valor):
            raise ValueError(MENSAJE_PERIODO)
        return valor


class MatriculaSalida(BaseModel):
    """Fila de v_matriculas_detalle: la matrícula con estudiante y curso ya resueltos."""

    id: int
    periodo: str
    fecha_matricula: date
    estado: str
    estudiante_id: int
    codigo_estudiante: str
    dni: str
    estudiante: str
    apellidos: str
    nombres: str
    email: str | None = None
    curso_id: int
    codigo_curso: str
    curso: str
    creditos: int
    horas: int


class PaginaMatriculas(BaseModel):
    total: int
    page: int
    page_size: int
    paginas: int
    matriculas: list[MatriculaSalida]


# ------------------------------------------------------------
# Notas y boleta (CU-14/CU-15 / C-24..C-29)
# ------------------------------------------------------------
class NotaEntrada(BaseEstricta):
    tipo: Literal["practica", "parcial", "final"]
    numero: int = Field(default=1, ge=1, le=50)
    nota: Decimal = Field(ge=0, le=20)
    fecha_registro: date | None = None
    observacion: str | None = Field(default=None, max_length=200)

    @field_validator("observacion", mode="before")
    @classmethod
    def vacio_es_none(cls, valor: object) -> object:
        return _texto_o_none(valor)


class NotaSalida(BaseModel):
    id: int
    matricula_id: int
    tipo: str
    numero: int
    nota: float
    nota_texto: str
    fecha_registro: date | None = None
    observacion: str | None = None


class CursoBoleta(BaseModel):
    curso_id: int
    codigo_curso: str
    curso: str
    creditos: int
    cantidad_notas: int
    # null = curso sin notas: no cuenta como 0 en el promedio (C-28)
    nota: float | None = None
    nota_texto: str | None = None
    notas: list[NotaSalida] = []


class Boleta(BaseModel):
    estudiante: EstudianteSalida
    periodo: str
    cursos: list[CursoBoleta]
    creditos_con_notas: int
    promedio: float | None = None
    promedio_texto: str | None = None
    # media simple de las notas de curso, para dejar fijada la diferencia con el
    # promedio ponderado por créditos (13.86 vs 13.50 en el ejemplo de RN-15)
    promedio_simple: float | None = None


# ------------------------------------------------------------
# Panel (CU-02 / C-05..C-07)
# ------------------------------------------------------------
class CursoTop(BaseModel):
    curso_id: int
    codigo: str
    curso: str
    creditos: int
    matriculas: int


class Panel(BaseModel):
    estudiantes_activos: int
    cursos_activos: int
    matriculas_activas: int
    usuarios_activos: int
    top_cursos: list[CursoTop]
    ultimos_estudiantes: list[EstudianteSalida]


# ------------------------------------------------------------
# Usuarios (CU-13 / C-22..C-23)
# ------------------------------------------------------------
class UsuarioEntrada(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    nombre_usuario: str
    email: str
    password: str
    nombre_completo: str = Field(min_length=1, max_length=100)
    rol: Literal["admin", "asistente"] = "asistente"
    estado: bool = True

    @field_validator("nombre_usuario")
    @classmethod
    def usuario_valido(cls, valor: str) -> str:
        if not re.match(PATRON_USUARIO, valor or ""):
            raise ValueError(MENSAJE_USUARIO)
        return valor

    @field_validator("email")
    @classmethod
    def email_valido(cls, valor: str) -> str:
        if not re.match(PATRON_EMAIL, valor or ""):
            raise ValueError(MENSAJE_EMAIL)
        return valor

    @field_validator("password")
    @classmethod
    def clave_larga(cls, valor: str) -> str:
        if len(valor or "") < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres (RN-01).")
        return valor


class UsuarioActualizar(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    email: str | None = None
    password: str | None = None
    nombre_completo: str | None = Field(default=None, min_length=1, max_length=100)
    rol: Literal["admin", "asistente"] | None = None
    estado: bool | None = None

    @field_validator("email")
    @classmethod
    def email_valido(cls, valor: str | None) -> str | None:
        if valor is not None and not re.match(PATRON_EMAIL, valor):
            raise ValueError(MENSAJE_EMAIL)
        return valor

    @field_validator("password")
    @classmethod
    def clave_larga(cls, valor: str | None) -> str | None:
        if valor is not None and len(valor) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres (RN-01).")
        return valor
