"""Tablas del Microservicio 1: usuario, rol, usuario_rol y tecnico."""
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario: Mapped[int] = mapped_column(primary_key=True)
    nombres: Mapped[str] = mapped_column(String(80))
    apellidos: Mapped[str] = mapped_column(String(80))
    correo: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    nombre_usuario: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    contrasena_hash: Mapped[str] = mapped_column(String(255))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    roles: Mapped[list["Rol"]] = relationship(secondary="usuario_rol", back_populates="usuarios", lazy="selectin")
    tecnico: Mapped["Tecnico | None"] = relationship(back_populates="usuario", uselist=False)


class Rol(Base):
    __tablename__ = "rol"

    id_rol: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(30), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(200))

    usuarios: Mapped[list[Usuario]] = relationship(secondary="usuario_rol", back_populates="roles")


class UsuarioRol(Base):
    """Tabla intermedia que resuelve la relación N:M entre usuario y rol."""
    __tablename__ = "usuario_rol"

    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario", ondelete="CASCADE"), primary_key=True)
    id_rol: Mapped[int] = mapped_column(ForeignKey("rol.id_rol", ondelete="RESTRICT"), primary_key=True)
    fecha_asignacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Tecnico(Base):
    """Un técnico ES un usuario (relación 1:1). No duplica credenciales."""
    __tablename__ = "tecnico"
    __table_args__ = (
        CheckConstraint("estado_laboral IN ('ACTIVO','VACACIONES','INACTIVO')", name="ck_tecnico_estado"),
    )

    id_tecnico: Mapped[int] = mapped_column(primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario", ondelete="CASCADE"), unique=True)
    especialidad: Mapped[str] = mapped_column(String(100))
    estado_laboral: Mapped[str] = mapped_column(String(20), default="ACTIVO")

    usuario: Mapped[Usuario] = relationship(back_populates="tecnico", lazy="selectin")
