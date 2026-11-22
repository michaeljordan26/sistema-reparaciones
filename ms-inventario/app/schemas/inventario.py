"""Esquemas Pydantic del inventario."""
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Dinero = Decimal


class RepuestoBase(BaseModel):
    nombre: str = Field(min_length=3, max_length=120)
    descripcion: str | None = Field(default=None, max_length=300)
    categoria: str = Field(min_length=3, max_length=50, examples=["MEMORIA RAM"])
    marca: str | None = Field(default=None, max_length=50)
    unidad_medida: str = Field(default="UNIDAD", max_length=20)
    precio_costo: Dinero = Field(ge=0, max_digits=12, decimal_places=2)
    precio_venta: Dinero = Field(ge=0, max_digits=12, decimal_places=2)
    stock_minimo: int = Field(default=1, ge=0)

    @field_validator("categoria")
    @classmethod
    def mayusculas(cls, v: str) -> str:
        return v.strip().upper()


class RepuestoCreate(RepuestoBase):
    codigo: str = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_-]+$", examples=["RAM-DDR4-8GB"])
    stock_inicial: int = Field(default=0, ge=0, description="Se registra como una ENTRADA")

    @field_validator("codigo")
    @classmethod
    def codigo_mayus(cls, v: str) -> str:
        return v.strip().upper()


class RepuestoUpdate(BaseModel):
    """El stock NO se cambia aquí: solo con movimientos (entradas, salidas, ajustes)."""
    nombre: str | None = Field(default=None, min_length=3, max_length=120)
    descripcion: str | None = Field(default=None, max_length=300)
    categoria: str | None = Field(default=None, min_length=3, max_length=50)
    marca: str | None = Field(default=None, max_length=50)
    precio_costo: Dinero | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    precio_venta: Dinero | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    stock_minimo: int | None = Field(default=None, ge=0)
    activo: bool | None = None


class RepuestoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_repuesto: int
    codigo: str
    nombre: str
    descripcion: str | None
    categoria: str
    marca: str | None
    unidad_medida: str
    precio_costo: float
    precio_venta: float
    stock_actual: int
    stock_minimo: int
    stock_bajo: bool
    activo: bool


# ---------- Movimientos ----------
class EntradaIn(BaseModel):
    cantidad: int = Field(gt=0, le=100000)
    costo_unitario: Dinero | None = Field(default=None, ge=0, max_digits=12, decimal_places=2,
                                          description="Si se envía, actualiza el precio de costo")
    motivo: str | None = Field(default="Compra a proveedor", max_length=300)


class SalidaIn(BaseModel):
    cantidad: int = Field(gt=0, le=1000)
    id_orden: int = Field(description="Orden de trabajo en la que se usa el repuesto")
    motivo: str | None = Field(default=None, max_length=300)


class DevolucionIn(SalidaIn):
    pass


class AjusteIn(BaseModel):
    tipo: Literal["POSITIVO", "NEGATIVO"]
    cantidad: int = Field(gt=0, le=100000)
    motivo: str = Field(min_length=5, max_length=300, examples=["Conteo físico: 2 unidades dañadas"])


class MovimientoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_movimiento: int
    id_repuesto: int
    tipo: str
    cantidad: int
    stock_anterior: int
    stock_resultante: int
    precio_unitario: float | None
    id_orden: int | None
    motivo: str | None
    id_usuario: int
    fecha: datetime | None


class MovimientoConRepuesto(MovimientoOut):
    repuesto: RepuestoOut


class ConsumoLinea(BaseModel):
    id_repuesto: int
    codigo: str
    nombre: str
    cantidad: int
    precio_unitario: float
    subtotal: float


class ConsumoOrden(BaseModel):
    """Repuestos usados en una orden (salidas menos devoluciones). Lo usará ms-facturacion."""
    id_orden: int
    lineas: list[ConsumoLinea]
    total_materiales: float
