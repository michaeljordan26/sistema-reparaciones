"""Esquemas Pydantic de diagnósticos, reparaciones y garantías."""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Resultado = Literal["EXITOSA", "PARCIAL", "NO_REPARABLE"]


# ---------- Diagnóstico ----------
class DiagnosticoCreate(BaseModel):
    id_orden: int
    hallazgos: str = Field(min_length=10, max_length=3000, examples=["El equipo no recibe carga; el jack DC está flojo"])
    causa_probable: str = Field(min_length=5, max_length=500, examples=["Jack de carga dañado por golpe"])
    solucion_propuesta: str = Field(min_length=5, max_length=3000, examples=["Reemplazar el jack DC"])
    requiere_repuestos: bool = False
    tiempo_estimado_horas: Decimal | None = Field(default=None, gt=0, le=999, decimal_places=1)
    observaciones: str | None = Field(default=None, max_length=500)


class DiagnosticoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_diagnostico: int
    id_orden: int
    id_tecnico: int
    fecha: datetime | None
    hallazgos: str
    causa_probable: str
    solucion_propuesta: str
    requiere_repuestos: bool
    tiempo_estimado_horas: float | None
    observaciones: str | None


# ---------- Reparación ----------
class ReparacionCreate(BaseModel):
    id_orden: int
    actividades_realizadas: str | None = Field(default=None, max_length=3000)


class RepuestoUsoIn(BaseModel):
    id_repuesto: int
    cantidad: int = Field(gt=0, le=100)


class FinalizarReparacion(BaseModel):
    actividades_realizadas: str = Field(min_length=10, max_length=3000,
                                        examples=["Se reemplazó el jack DC y se probó la carga durante 30 min"])
    resultado: Resultado
    observaciones: str | None = Field(default=None, max_length=500)
    garantia_dias: int | None = Field(default=None, ge=0, le=730,
                                      description="0 = sin garantía. Vacío = valor por defecto (90 días)")
    cobertura_garantia: str | None = Field(default=None, max_length=500)


class RepuestoUtilizadoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_repuesto_utilizado: int
    id_repuesto: int
    id_movimiento: int
    codigo: str
    nombre: str
    cantidad: int
    precio_unitario: float
    fecha: datetime | None


class GarantiaResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_garantia: int
    fecha_inicio: date
    fecha_fin: date
    dias: int
    estado: str


class ReparacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_reparacion: int
    id_orden: int
    id_diagnostico: int
    id_tecnico: int
    fecha_inicio: datetime | None
    fecha_fin: datetime | None
    actividades_realizadas: str | None
    resultado: str | None
    observaciones: str | None
    estado: str
    repuestos: list[RepuestoUtilizadoOut] = []
    total_repuestos: float
    garantia: GarantiaResumen | None = None


# ---------- Garantías ----------
class ReclamacionCreate(BaseModel):
    descripcion: str = Field(min_length=10, max_length=3000, examples=["El equipo volvió a dejar de cargar"])


class ReclamacionResolver(BaseModel):
    estado: Literal["APROBADA", "RECHAZADA"]
    respuesta: str = Field(min_length=5, max_length=500)


class ReclamacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_reclamacion: int
    id_garantia: int
    fecha: datetime | None
    descripcion: str
    estado: str
    respuesta: str | None
    fecha_respuesta: datetime | None


class AnularGarantia(BaseModel):
    motivo: str = Field(min_length=5, max_length=300, examples=["Equipo manipulado por terceros"])


class GarantiaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_garantia: int
    id_reparacion: int
    id_orden: int
    id_equipo: int
    id_cliente: int
    fecha_inicio: date
    fecha_fin: date
    dias: int
    cobertura: str
    condiciones: str | None
    estado: str
    motivo_anulacion: str | None
    reclamaciones: list[ReclamacionOut] = []


class ResumenOrden(BaseModel):
    """Todo lo técnico de una orden en una sola consulta (útil para el frontend)."""
    id_orden: int
    diagnostico: DiagnosticoOut | None
    reparacion: ReparacionOut | None
    garantia: GarantiaOut | None
