"""Tablas del Microservicio 4: diagnostico, reparacion, repuesto_utilizado,
garantia y reclamacion_garantia.
id_orden, id_tecnico, id_repuesto, id_movimiento, id_equipo e id_cliente son referencias
lógicas a otros microservicios (no son claves foráneas físicas)."""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.tiempo import hoy
from app.database.session import Base


class Diagnostico(Base):
    __tablename__ = "diagnostico"
    __table_args__ = (CheckConstraint("tiempo_estimado_horas IS NULL OR tiempo_estimado_horas > 0",
                                      name="ck_diagnostico_tiempo"),)

    id_diagnostico: Mapped[int] = mapped_column(primary_key=True)
    id_orden: Mapped[int] = mapped_column(unique=True, index=True)        # un diagnóstico por orden
    id_tecnico: Mapped[int]
    id_usuario_tecnico: Mapped[int]
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    hallazgos: Mapped[str] = mapped_column(Text)
    causa_probable: Mapped[str] = mapped_column(String(500))
    solucion_propuesta: Mapped[str] = mapped_column(Text)
    requiere_repuestos: Mapped[bool] = mapped_column(default=False)
    tiempo_estimado_horas: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    observaciones: Mapped[str | None] = mapped_column(String(500))

    reparacion: Mapped["Reparacion | None"] = relationship(back_populates="diagnostico", uselist=False)


class Reparacion(Base):
    __tablename__ = "reparacion"
    __table_args__ = (
        CheckConstraint("estado IN ('EN_PROCESO','FINALIZADA')", name="ck_reparacion_estado"),
        CheckConstraint("resultado IS NULL OR resultado IN ('EXITOSA','PARCIAL','NO_REPARABLE')",
                        name="ck_reparacion_resultado"),
        CheckConstraint("(estado = 'FINALIZADA') = (fecha_fin IS NOT NULL)", name="ck_reparacion_fin"),
    )

    id_reparacion: Mapped[int] = mapped_column(primary_key=True)
    id_orden: Mapped[int] = mapped_column(unique=True, index=True)
    id_diagnostico: Mapped[int] = mapped_column(ForeignKey("diagnostico.id_diagnostico", ondelete="RESTRICT"),
                                                unique=True)
    id_tecnico: Mapped[int]
    id_usuario_tecnico: Mapped[int]
    fecha_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    fecha_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actividades_realizadas: Mapped[str | None] = mapped_column(Text)
    resultado: Mapped[str | None] = mapped_column(String(15))
    observaciones: Mapped[str | None] = mapped_column(String(500))
    estado: Mapped[str] = mapped_column(String(12), default="EN_PROCESO")

    diagnostico: Mapped[Diagnostico] = relationship(back_populates="reparacion")
    repuestos: Mapped[list["RepuestoUtilizado"]] = relationship(
        back_populates="reparacion", order_by="RepuestoUtilizado.id_repuesto_utilizado", cascade="all, delete-orphan")
    garantia: Mapped["Garantia | None"] = relationship(back_populates="reparacion", uselist=False)

    @property
    def total_repuestos(self) -> float:
        return float(sum((r.cantidad * r.precio_unitario for r in self.repuestos), Decimal(0)))


class RepuestoUtilizado(Base):
    """Copia local de lo que se usó. El descuento real de stock lo hace ms-inventario (id_movimiento)."""
    __tablename__ = "repuesto_utilizado"
    __table_args__ = (CheckConstraint("cantidad > 0", name="ck_ru_cantidad"),)

    id_repuesto_utilizado: Mapped[int] = mapped_column(primary_key=True)
    id_reparacion: Mapped[int] = mapped_column(ForeignKey("reparacion.id_reparacion", ondelete="CASCADE"), index=True)
    id_repuesto: Mapped[int]
    id_movimiento: Mapped[int]                                 # movimiento SALIDA en ms-inventario
    codigo: Mapped[str] = mapped_column(String(30))
    nombre: Mapped[str] = mapped_column(String(120))
    cantidad: Mapped[int]
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    reparacion: Mapped[Reparacion] = relationship(back_populates="repuestos")


class Garantia(Base):
    __tablename__ = "garantia"
    __table_args__ = (
        CheckConstraint("fecha_fin >= fecha_inicio", name="ck_garantia_fechas"),
        CheckConstraint("dias > 0", name="ck_garantia_dias"),
    )

    id_garantia: Mapped[int] = mapped_column(primary_key=True)
    id_reparacion: Mapped[int] = mapped_column(ForeignKey("reparacion.id_reparacion", ondelete="RESTRICT"),
                                               unique=True)
    id_orden: Mapped[int] = mapped_column(index=True)
    id_equipo: Mapped[int] = mapped_column(index=True)
    id_cliente: Mapped[int] = mapped_column(index=True)
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date] = mapped_column(Date)
    dias: Mapped[int]
    cobertura: Mapped[str] = mapped_column(String(500))
    condiciones: Mapped[str | None] = mapped_column(String(500))
    anulada: Mapped[bool] = mapped_column(default=False)
    motivo_anulacion: Mapped[str | None] = mapped_column(String(300))

    reparacion: Mapped[Reparacion] = relationship(back_populates="garantia")
    reclamaciones: Mapped[list["ReclamacionGarantia"]] = relationship(
        back_populates="garantia", order_by="ReclamacionGarantia.id_reclamacion")

    @property
    def estado(self) -> str:
        if self.anulada:
            return "ANULADA"
        return "VIGENTE" if hoy() <= self.fecha_fin else "VENCIDA"


class ReclamacionGarantia(Base):
    __tablename__ = "reclamacion_garantia"
    __table_args__ = (
        CheckConstraint("estado IN ('ABIERTA','APROBADA','RECHAZADA')", name="ck_reclamacion_estado"),
        # Solo una reclamación abierta a la vez por garantía
        Index("uq_reclamacion_abierta", "id_garantia", unique=True,
              postgresql_where=text("estado = 'ABIERTA'"), sqlite_where=text("estado = 'ABIERTA'")),
    )

    id_reclamacion: Mapped[int] = mapped_column(primary_key=True)
    id_garantia: Mapped[int] = mapped_column(ForeignKey("garantia.id_garantia", ondelete="RESTRICT"), index=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    descripcion: Mapped[str] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(10), default="ABIERTA")
    respuesta: Mapped[str | None] = mapped_column(String(500))
    fecha_respuesta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    id_usuario_registro: Mapped[int]
    id_usuario_respuesta: Mapped[int | None]

    garantia: Mapped[Garantia] = relationship(back_populates="reclamaciones")
