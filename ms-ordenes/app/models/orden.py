"""Tablas del Microservicio 3: orden_trabajo, historial_estado y asignacion.
id_equipo, id_cliente, id_tecnico e id_usuario son REFERENCIAS a datos de otros
microservicios: no son claves foráneas físicas porque viven en otras bases de datos."""
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.estados import ESTADOS
from app.database.session import Base

_lista_estados = ",".join(f"'{e}'" for e in ESTADOS)


class OrdenTrabajo(Base):
    __tablename__ = "orden_trabajo"
    __table_args__ = (
        CheckConstraint(f"estado_actual IN ({_lista_estados})", name="ck_orden_estado"),
        CheckConstraint("prioridad IN ('BAJA','MEDIA','ALTA','URGENTE')", name="ck_orden_prioridad"),
    )

    id_orden: Mapped[int] = mapped_column(primary_key=True)
    id_equipo: Mapped[int] = mapped_column(index=True)            # ref. ms-clientes
    id_cliente: Mapped[int] = mapped_column(index=True)           # ref. ms-clientes (copia para reportes)
    fecha_recepcion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    descripcion_problema: Mapped[str] = mapped_column(Text)
    accesorios_recibidos: Mapped[str | None] = mapped_column(String(250))
    prioridad: Mapped[str] = mapped_column(String(10), default="MEDIA")
    estado_actual: Mapped[str] = mapped_column(String(25), default="RECIBIDO", index=True)
    fecha_cierre: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    id_usuario_recepcion: Mapped[int]                              # ref. ms-usuarios

    historial: Mapped[list["HistorialEstado"]] = relationship(
        back_populates="orden", order_by="HistorialEstado.id_historial", cascade="all, delete-orphan")
    asignaciones: Mapped[list["Asignacion"]] = relationship(
        back_populates="orden", order_by="Asignacion.id_asignacion", cascade="all, delete-orphan")

    @property
    def codigo(self) -> str:
        return f"OT-{self.id_orden:06d}"

    @property
    def asignacion_activa(self) -> "Asignacion | None":
        return next((a for a in self.asignaciones if a.estado_asignacion == "ACTIVA"), None)


class HistorialEstado(Base):
    """RN13 / RNF05: cada cambio de estado queda registrado con fecha y usuario. Nunca se borra."""
    __tablename__ = "historial_estado"

    id_historial: Mapped[int] = mapped_column(primary_key=True)
    id_orden: Mapped[int] = mapped_column(ForeignKey("orden_trabajo.id_orden", ondelete="RESTRICT"), index=True)
    estado_anterior: Mapped[str | None] = mapped_column(String(25))
    estado_nuevo: Mapped[str] = mapped_column(String(25))
    fecha_cambio: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    observacion: Mapped[str | None] = mapped_column(String(500))
    id_usuario: Mapped[int]                                        # ref. ms-usuarios

    orden: Mapped[OrdenTrabajo] = relationship(back_populates="historial")


class Asignacion(Base):
    """Qué técnico atiende la orden y desde cuándo. Solo puede haber UNA asignación activa por orden."""
    __tablename__ = "asignacion"
    __table_args__ = (
        CheckConstraint("estado_asignacion IN ('ACTIVA','FINALIZADA','REASIGNADA')", name="ck_asignacion_estado"),
        Index("uq_asignacion_activa", "id_orden", unique=True,
              postgresql_where=text("estado_asignacion = 'ACTIVA'"),
              sqlite_where=text("estado_asignacion = 'ACTIVA'")),
    )

    id_asignacion: Mapped[int] = mapped_column(primary_key=True)
    id_orden: Mapped[int] = mapped_column(ForeignKey("orden_trabajo.id_orden", ondelete="RESTRICT"), index=True)
    id_tecnico: Mapped[int] = mapped_column(index=True)            # ref. ms-usuarios (tabla tecnico)
    id_usuario_tecnico: Mapped[int]                                # usuario del técnico (para "mis órdenes")
    nombre_tecnico: Mapped[str] = mapped_column(String(170))       # copia para mostrar sin consultar MS1
    fecha_asignacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    fecha_finalizacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estado_asignacion: Mapped[str] = mapped_column(String(12), default="ACTIVA")

    orden: Mapped[OrdenTrabajo] = relationship(back_populates="asignaciones")
