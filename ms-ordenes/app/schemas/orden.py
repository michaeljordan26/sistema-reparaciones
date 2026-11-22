"""Esquemas Pydantic de órdenes de trabajo."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.estados import ESTADOS

Prioridad = Literal["BAJA", "MEDIA", "ALTA", "URGENTE"]
Estado = Literal[tuple(ESTADOS)]  # type: ignore[valid-type]


class OrdenCreate(BaseModel):
    id_equipo: int
    descripcion_problema: str = Field(min_length=5, max_length=2000)
    accesorios_recibidos: str | None = Field(default=None, max_length=250, examples=["Cargador, estuche"])
    prioridad: Prioridad = "MEDIA"


class AsignarTecnico(BaseModel):
    id_tecnico: int
    observacion: str | None = Field(default=None, max_length=500)


class CambioEstado(BaseModel):
    estado: Estado
    observacion: str | None = Field(default=None, max_length=500)


class HistorialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_historial: int
    estado_anterior: str | None
    estado_nuevo: str
    fecha_cambio: datetime | None
    observacion: str | None
    id_usuario: int


class AsignacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_asignacion: int
    id_tecnico: int
    nombre_tecnico: str
    fecha_asignacion: datetime | None
    fecha_finalizacion: datetime | None
    estado_asignacion: str


class OrdenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_orden: int
    codigo: str
    id_equipo: int
    id_cliente: int
    fecha_recepcion: datetime | None
    descripcion_problema: str
    accesorios_recibidos: str | None
    prioridad: str
    estado_actual: str
    fecha_cierre: datetime | None
    asignacion_activa: AsignacionOut | None = None


class OrdenDetalle(OrdenOut):
    historial: list[HistorialOut] = []
    asignaciones: list[AsignacionOut] = []
    transiciones_permitidas: list[str] = []
