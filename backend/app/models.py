# ============================================================
# GS08 · Matrículas y Notas | app/models.py
# Autor: @dev | T1.1 | Sprint 1
# Mapeo ORM de las 5 tablas de db/init/ (4 del legacy + notas de T1.5).
# Las 2 vistas (v_matriculas_detalle, v_notas_detalle) se consultan con SQL
# directo en los routers: son de solo lectura y llevan los JOIN ya resueltos.
# ============================================================
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_usuario: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(100), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False, default="asistente")
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def como_diccionario(self) -> dict:
        return {
            "id": self.id,
            "nombre_usuario": self.nombre_usuario,
            "email": self.email,
            "nombre_completo": self.nombre_completo,
            "rol": self.rol,
            "estado": self.estado,
            "creado_en": self.creado_en,
        }


class Estudiante(Base):
    __tablename__ = "estudiantes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False)
    dni: Mapped[str] = mapped_column(String(8), nullable=False)
    nombres: Mapped[str] = mapped_column(String(80), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str | None] = mapped_column(String(100))
    telefono: Mapped[str | None] = mapped_column(String(20))
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date)
    direccion: Mapped[str | None] = mapped_column(String(150))
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def como_diccionario(self) -> dict:
        return {
            "id": self.id,
            "codigo": self.codigo,
            "dni": self.dni,
            "nombres": self.nombres,
            "apellidos": self.apellidos,
            "nombre_completo": f"{self.apellidos}, {self.nombres}",
            "email": self.email,
            "telefono": self.telefono,
            "fecha_nacimiento": self.fecha_nacimiento,
            "direccion": self.direccion,
            "estado": self.estado,
            "creado_en": self.creado_en,
        }


class Curso(Base):
    __tablename__ = "cursos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    creditos: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=3)
    horas: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=48)
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def como_diccionario(self) -> dict:
        return {
            "id": self.id,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "creditos": self.creditos,
            "horas": self.horas,
            "estado": self.estado,
            "creado_en": self.creado_en,
        }


class Matricula(Base):
    __tablename__ = "matriculas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    estudiante_id: Mapped[int] = mapped_column(Integer, nullable=False)
    curso_id: Mapped[int] = mapped_column(Integer, nullable=False)
    periodo: Mapped[str] = mapped_column(String(7), nullable=False)
    fecha_matricula: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[str] = mapped_column(String(15), nullable=False, default="activa")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def como_diccionario(self) -> dict:
        return {
            "id": self.id,
            "estudiante_id": self.estudiante_id,
            "curso_id": self.curso_id,
            "periodo": self.periodo,
            "fecha_matricula": self.fecha_matricula,
            "estado": self.estado,
            "creado_en": self.creado_en,
        }


class Nota(Base):
    __tablename__ = "notas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    matricula_id: Mapped[int] = mapped_column(Integer, nullable=False)
    tipo: Mapped[str] = mapped_column(String(15), nullable=False)
    numero: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    nota: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    fecha_registro: Mapped[date] = mapped_column(Date, nullable=False)
    observacion: Mapped[str | None] = mapped_column(String(200))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def como_diccionario(self) -> dict:
        # decision (@analista, handoff de T1.5): numeric(4,2) se serializa como
        # numero JSON redondeado a 2 decimales + un campo *_texto con los dos
        # decimales fijos, que es lo que muestra la pantalla de la boleta (C-27).
        return {
            "id": self.id,
            "matricula_id": self.matricula_id,
            "tipo": self.tipo,
            "numero": self.numero,
            "nota": float(self.nota),
            "nota_texto": f"{self.nota:.2f}",
            "fecha_registro": self.fecha_registro,
            "observacion": self.observacion,
        }
