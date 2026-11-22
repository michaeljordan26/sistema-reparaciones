"""Tablas del Microservicio 6: presupuesto, detalle_presupuesto, respuesta_presupuesto,
factura, detalle_factura y pago. id_orden e id_repuesto son referencias lógicas a otros servicios."""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, String, Text, func,
                        text)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.tiempo import hoy
from app.database.session import Base

CERO = Decimal("0.00")


class Presupuesto(Base):
    __tablename__ = "presupuesto"
    __table_args__ = (
        CheckConstraint("estado IN ('PENDIENTE','APROBADO','RECHAZADO','ANULADO')", name="ck_presupuesto_estado"),
        CheckConstraint("total = subtotal + iva", name="ck_presupuesto_total"),
        CheckConstraint("fecha_vencimiento >= fecha", name="ck_presupuesto_vencimiento"),
        # Solo un presupuesto vigente (pendiente o aprobado) por orden
        Index("uq_presupuesto_vigente", "id_orden", unique=True,
              postgresql_where=text("estado IN ('PENDIENTE','APROBADO')"),
              sqlite_where=text("estado IN ('PENDIENTE','APROBADO')")),
    )

    id_presupuesto: Mapped[int] = mapped_column(primary_key=True)
    id_orden: Mapped[int] = mapped_column(index=True)
    fecha: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    fecha_vencimiento: Mapped[date] = mapped_column(Date)
    subtotal_materiales: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    subtotal_mano_obra: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    iva_porcentaje: Mapped[int]
    iva: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    observaciones: Mapped[str | None] = mapped_column(String(500))
    estado: Mapped[str] = mapped_column(String(10), default="PENDIENTE")
    id_usuario: Mapped[int]
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    detalles: Mapped[list["DetallePresupuesto"]] = relationship(
        back_populates="presupuesto", order_by="DetallePresupuesto.id_detalle", cascade="all, delete-orphan")
    respuesta: Mapped["RespuestaPresupuesto | None"] = relationship(back_populates="presupuesto", uselist=False)

    @property
    def codigo(self) -> str:
        return f"PR-{self.id_presupuesto:06d}"

    @property
    def vencido(self) -> bool:
        return self.estado == "PENDIENTE" and hoy() > self.fecha_vencimiento


class DetallePresupuesto(Base):
    __tablename__ = "detalle_presupuesto"
    __table_args__ = (
        CheckConstraint("tipo IN ('MANO_OBRA','REPUESTO')", name="ck_detalle_tipo"),
        CheckConstraint("cantidad > 0", name="ck_detalle_cantidad"),
        CheckConstraint("precio_unitario >= 0", name="ck_detalle_precio"),
        CheckConstraint("subtotal = round(cantidad * precio_unitario, 2)", name="ck_detalle_subtotal"),
        CheckConstraint("(tipo = 'REPUESTO') = (id_repuesto IS NOT NULL)", name="ck_detalle_repuesto"),
    )

    id_detalle: Mapped[int] = mapped_column(primary_key=True)
    id_presupuesto: Mapped[int] = mapped_column(ForeignKey("presupuesto.id_presupuesto", ondelete="CASCADE"),
                                                index=True)
    tipo: Mapped[str] = mapped_column(String(10))
    id_repuesto: Mapped[int | None]                              # ref. ms-inventario
    descripcion: Mapped[str] = mapped_column(String(200))
    cantidad: Mapped[Decimal] = mapped_column(Numeric(8, 2))     # horas o unidades
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    presupuesto: Mapped[Presupuesto] = relationship(back_populates="detalles")


class RespuestaPresupuesto(Base):
    """Registro de la decisión del cliente (quién, cuándo, por qué medio)."""
    __tablename__ = "respuesta_presupuesto"
    __table_args__ = (
        CheckConstraint("decision IN ('APROBADO','RECHAZADO')", name="ck_respuesta_decision"),
        CheckConstraint("medio IN ('PRESENCIAL','TELEFONO','CORREO','WHATSAPP')", name="ck_respuesta_medio"),
    )

    id_respuesta: Mapped[int] = mapped_column(primary_key=True)
    id_presupuesto: Mapped[int] = mapped_column(ForeignKey("presupuesto.id_presupuesto", ondelete="RESTRICT"),
                                                unique=True)
    decision: Mapped[str] = mapped_column(String(10))
    medio: Mapped[str] = mapped_column(String(12))
    nombre_responde: Mapped[str] = mapped_column(String(120))
    observacion: Mapped[str | None] = mapped_column(String(500))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    id_usuario: Mapped[int]

    presupuesto: Mapped[Presupuesto] = relationship(back_populates="respuesta")


class Factura(Base):
    __tablename__ = "factura"
    __table_args__ = (
        CheckConstraint("total = subtotal + iva", name="ck_factura_total"),
        CheckConstraint("total >= 0", name="ck_factura_total_positivo"),
        # Una sola factura activa por orden
        Index("uq_factura_activa", "id_orden", unique=True,
              postgresql_where=text("anulada = false"), sqlite_where=text("anulada = 0")),
    )

    id_factura: Mapped[int] = mapped_column(primary_key=True)
    id_orden: Mapped[int] = mapped_column(index=True)
    id_presupuesto: Mapped[int] = mapped_column(ForeignKey("presupuesto.id_presupuesto", ondelete="RESTRICT"))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    subtotal_materiales: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    subtotal_mano_obra: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    iva_porcentaje: Mapped[int]
    iva: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    anulada: Mapped[bool] = mapped_column(default=False)
    motivo_anulacion: Mapped[str | None] = mapped_column(String(300))
    id_usuario: Mapped[int]

    detalles: Mapped[list["DetalleFactura"]] = relationship(
        back_populates="factura", order_by="DetalleFactura.id_detalle", cascade="all, delete-orphan")
    pagos: Mapped[list["Pago"]] = relationship(back_populates="factura", order_by="Pago.id_pago")
    presupuesto: Mapped[Presupuesto] = relationship()

    @property
    def numero(self) -> str:
        return f"FV-{self.id_factura:06d}"

    @property
    def total_pagado(self) -> Decimal:
        return sum((p.monto for p in self.pagos if not p.anulado), CERO)

    @property
    def saldo(self) -> Decimal:
        return CERO if self.anulada else self.total - self.total_pagado

    @property
    def estado(self) -> str:
        if self.anulada:
            return "ANULADA"
        if self.saldo <= 0:
            return "PAGADA"
        return "PARCIAL" if self.total_pagado > 0 else "PENDIENTE"


class DetalleFactura(Base):
    __tablename__ = "detalle_factura"
    __table_args__ = (
        CheckConstraint("tipo IN ('MANO_OBRA','REPUESTO')", name="ck_detfac_tipo"),
        CheckConstraint("cantidad > 0", name="ck_detfac_cantidad"),
        CheckConstraint("subtotal = round(cantidad * precio_unitario, 2)", name="ck_detfac_subtotal"),
    )

    id_detalle: Mapped[int] = mapped_column(primary_key=True)
    id_factura: Mapped[int] = mapped_column(ForeignKey("factura.id_factura", ondelete="CASCADE"), index=True)
    tipo: Mapped[str] = mapped_column(String(10))
    id_repuesto: Mapped[int | None]
    descripcion: Mapped[str] = mapped_column(String(200))
    cantidad: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    factura: Mapped[Factura] = relationship(back_populates="detalles")


class Pago(Base):
    __tablename__ = "pago"
    __table_args__ = (
        CheckConstraint("monto > 0", name="ck_pago_monto"),
        CheckConstraint("metodo IN ('EFECTIVO','TARJETA','TRANSFERENCIA','NEQUI','DAVIPLATA')", name="ck_pago_metodo"),
        CheckConstraint("tipo IN ('ABONO','PAGO_TOTAL')", name="ck_pago_tipo"),
        CheckConstraint("metodo = 'EFECTIVO' OR referencia IS NOT NULL", name="ck_pago_referencia"),
    )

    id_pago: Mapped[int] = mapped_column(primary_key=True)
    id_factura: Mapped[int] = mapped_column(ForeignKey("factura.id_factura", ondelete="RESTRICT"), index=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    metodo: Mapped[str] = mapped_column(String(15))
    referencia: Mapped[str | None] = mapped_column(String(60))
    tipo: Mapped[str] = mapped_column(String(10))
    saldo_anterior: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    saldo_resultante: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    anulado: Mapped[bool] = mapped_column(default=False)
    motivo_anulacion: Mapped[str | None] = mapped_column(String(300))
    id_usuario: Mapped[int]

    factura: Mapped[Factura] = relationship(back_populates="pagos")
