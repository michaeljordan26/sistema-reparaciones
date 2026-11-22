"""Tablas del Microservicio 5: repuesto y movimiento_inventario.
Regla principal: el stock NUNCA puede quedar negativo (CHECK en la base + validación + bloqueo de fila)."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

TIPOS_MOVIMIENTO = ["ENTRADA", "SALIDA", "DEVOLUCION", "AJUSTE_POSITIVO", "AJUSTE_NEGATIVO"]
# Cómo afecta cada tipo al stock
SIGNO = {"ENTRADA": 1, "DEVOLUCION": 1, "AJUSTE_POSITIVO": 1, "SALIDA": -1, "AJUSTE_NEGATIVO": -1}


class Repuesto(Base):
    __tablename__ = "repuesto"
    __table_args__ = (
        CheckConstraint("stock_actual >= 0", name="ck_repuesto_stock_no_negativo"),
        CheckConstraint("stock_minimo >= 0", name="ck_repuesto_stock_minimo"),
        CheckConstraint("precio_costo >= 0 AND precio_venta >= 0", name="ck_repuesto_precios"),
    )

    id_repuesto: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str | None] = mapped_column(String(300))
    categoria: Mapped[str] = mapped_column(String(50), index=True)
    marca: Mapped[str | None] = mapped_column(String(50))
    unidad_medida: Mapped[str] = mapped_column(String(20), default="UNIDAD")
    precio_costo: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    precio_venta: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    stock_actual: Mapped[int] = mapped_column(default=0)
    stock_minimo: Mapped[int] = mapped_column(default=0)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    movimientos: Mapped[list["MovimientoInventario"]] = relationship(
        back_populates="repuesto", order_by="MovimientoInventario.id_movimiento")

    @property
    def stock_bajo(self) -> bool:
        return self.stock_actual <= self.stock_minimo


class MovimientoInventario(Base):
    """Kardex: cada entrada o salida queda registrada con el stock antes y después. Nunca se borra."""
    __tablename__ = "movimiento_inventario"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_movimiento_cantidad"),
        CheckConstraint("stock_resultante >= 0", name="ck_movimiento_stock_resultante"),
        CheckConstraint("tipo IN ('ENTRADA','SALIDA','DEVOLUCION','AJUSTE_POSITIVO','AJUSTE_NEGATIVO')",
                        name="ck_movimiento_tipo"),
    )

    id_movimiento: Mapped[int] = mapped_column(primary_key=True)
    id_repuesto: Mapped[int] = mapped_column(ForeignKey("repuesto.id_repuesto", ondelete="RESTRICT"), index=True)
    tipo: Mapped[str] = mapped_column(String(20))
    cantidad: Mapped[int]
    stock_anterior: Mapped[int]
    stock_resultante: Mapped[int]
    precio_unitario: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))  # costo (entrada) o venta (salida)
    id_orden: Mapped[int | None] = mapped_column(index=True)              # ref. ms-ordenes
    motivo: Mapped[str | None] = mapped_column(String(300))
    id_usuario: Mapped[int]                                              # ref. ms-usuarios
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    repuesto: Mapped[Repuesto] = relationship(back_populates="movimientos")
