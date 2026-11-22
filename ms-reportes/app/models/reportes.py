"""Tablas del Microservicio 7: registro_auditoria y notificacion."""
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class RegistroAuditoria(Base):
    """Bitácora de operaciones de TODOS los microservicios.
    Es de solo inserción: un trigger en PostgreSQL impide UPDATE y DELETE (ver la migración)."""
    __tablename__ = "registro_auditoria"
    __table_args__ = (
        CheckConstraint("metodo IN ('POST','PUT','PATCH','DELETE')", name="ck_auditoria_metodo"),
        Index("ix_auditoria_servicio_fecha", "servicio", "fecha"),
    )

    id_registro: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    servicio: Mapped[str] = mapped_column(String(30))
    metodo: Mapped[str] = mapped_column(String(6))
    ruta: Mapped[str] = mapped_column(String(200))
    ruta_plantilla: Mapped[str] = mapped_column(String(200))
    accion: Mapped[str] = mapped_column(String(120))            # descripción legible
    recurso_id: Mapped[str | None] = mapped_column(String(40))
    codigo_estado: Mapped[int]
    exito: Mapped[bool]
    id_usuario: Mapped[int | None] = mapped_column(index=True)   # ref. ms-usuarios
    roles: Mapped[str | None] = mapped_column(String(120))
    ip: Mapped[str | None] = mapped_column(String(45))
    duracion_ms: Mapped[int | None]


class Notificacion(Base):
    """Mensaje al cliente por cada cambio importante de su orden. El envío es SIMULADO:
    se guarda como si se hubiera enviado; en producción se conectaría un servicio de correo o SMS."""
    __tablename__ = "notificacion"
    __table_args__ = (
        UniqueConstraint("id_orden", "tipo", name="uq_notificacion_orden_tipo"),   # sin duplicados
        CheckConstraint("canal IN ('CORREO','SMS')", name="ck_notificacion_canal"),
        CheckConstraint("estado IN ('ENVIADA','FALLIDA')", name="ck_notificacion_estado"),
    )

    id_notificacion: Mapped[int] = mapped_column(primary_key=True)
    id_orden: Mapped[int] = mapped_column(index=True)
    id_cliente: Mapped[int | None] = mapped_column(index=True)
    tipo: Mapped[str] = mapped_column(String(25))                # el estado que la generó
    canal: Mapped[str] = mapped_column(String(10))
    destinatario: Mapped[str | None] = mapped_column(String(120))
    asunto: Mapped[str] = mapped_column(String(150))
    mensaje: Mapped[str] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(10))
    detalle_error: Mapped[str | None] = mapped_column(String(300))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
