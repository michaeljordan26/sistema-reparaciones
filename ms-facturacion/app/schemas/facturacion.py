"""Esquemas Pydantic de presupuestos, facturas y pagos."""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Metodo = Literal["EFECTIVO", "TARJETA", "TRANSFERENCIA", "NEQUI", "DAVIPLATA"]


# ---------- Presupuesto ----------
class ManoObraIn(BaseModel):
    descripcion: str = Field(min_length=3, max_length=200, examples=["Cambio de jack de carga"])
    horas: Decimal = Field(gt=0, le=200, decimal_places=2, examples=[1.5])
    valor_hora: Decimal = Field(ge=0, max_digits=12, decimal_places=2, examples=[40000])


class RepuestoPresupuestoIn(BaseModel):
    id_repuesto: int
    cantidad: int = Field(gt=0, le=100)


class PresupuestoCreate(BaseModel):
    id_orden: int
    mano_obra: list[ManoObraIn] = Field(min_length=1, description="Al menos una línea de mano de obra")
    repuestos: list[RepuestoPresupuestoIn] = []
    observaciones: str | None = Field(default=None, max_length=500)


class DetalleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_detalle: int
    tipo: str
    id_repuesto: int | None
    descripcion: str
    cantidad: float
    precio_unitario: float
    subtotal: float


class RespuestaIn(BaseModel):
    decision: Literal["APROBADO", "RECHAZADO"]
    medio: Literal["PRESENCIAL", "TELEFONO", "CORREO", "WHATSAPP"] = "PRESENCIAL"
    nombre_responde: str = Field(min_length=3, max_length=120, examples=["María Rodríguez"])
    observacion: str | None = Field(default=None, max_length=500)


class RespuestaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    decision: str
    medio: str
    nombre_responde: str
    observacion: str | None
    fecha: datetime | None


class PresupuestoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_presupuesto: int
    codigo: str
    id_orden: int
    fecha: date | None
    fecha_vencimiento: date
    vencido: bool
    subtotal_materiales: float
    subtotal_mano_obra: float
    subtotal: float
    iva_porcentaje: int
    iva: float
    total: float
    observaciones: str | None
    estado: str
    detalles: list[DetalleOut] = []
    respuesta: RespuestaOut | None = None


class AnularIn(BaseModel):
    motivo: str = Field(min_length=5, max_length=300)


# ---------- Factura y pagos ----------
class FacturaCreate(BaseModel):
    id_orden: int


class PagoIn(BaseModel):
    monto: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    metodo: Metodo = "EFECTIVO"
    referencia: str | None = Field(default=None, max_length=60, examples=["Transacción 98765"])

    @model_validator(mode="after")
    def referencia_obligatoria(self):
        if self.metodo != "EFECTIVO" and not (self.referencia and self.referencia.strip()):
            raise ValueError("La referencia es obligatoria para pagos que no son en efectivo")
        return self


class PagoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_pago: int
    id_factura: int
    fecha: datetime | None
    monto: float
    metodo: str
    referencia: str | None
    tipo: str
    saldo_anterior: float
    saldo_resultante: float
    anulado: bool
    motivo_anulacion: str | None


class FacturaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_factura: int
    numero: str
    id_orden: int
    id_presupuesto: int
    fecha: datetime | None
    subtotal_materiales: float
    subtotal_mano_obra: float
    subtotal: float
    iva_porcentaje: int
    iva: float
    total: float
    total_pagado: float
    saldo: float
    estado: str
    motivo_anulacion: str | None
    detalles: list[DetalleOut] = []
    pagos: list[PagoOut] = []


class SaldoOrden(BaseModel):
    """Lo consulta ms-ordenes antes de permitir la entrega del equipo."""
    id_orden: int
    saldo_pendiente: float
    detalle: str


class IngresosOut(BaseModel):
    desde: date
    hasta: date
    total: float
    cantidad_pagos: int
    por_metodo: dict[str, float]


class CarteraLinea(BaseModel):
    id_factura: int
    numero: str
    id_orden: int
    total: float
    total_pagado: float
    saldo: float
    estado: str


class CarteraOut(BaseModel):
    facturas: list[CarteraLinea]
    total_por_cobrar: float
