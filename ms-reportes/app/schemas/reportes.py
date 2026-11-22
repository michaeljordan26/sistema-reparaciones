"""Esquemas Pydantic del Microservicio 7."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EventoIn(BaseModel):
    """Lo envía el middleware de auditoría de cada microservicio."""
    servicio: str = Field(max_length=30)
    metodo: str = Field(pattern="^(POST|PUT|PATCH|DELETE)$")
    ruta: str = Field(max_length=200)
    ruta_plantilla: str = Field(max_length=200)
    recurso_id: str | None = Field(default=None, max_length=40)
    codigo_estado: int
    id_usuario: int | None = None
    roles: list[str] = []
    duracion_ms: int | None = None
    ip: str | None = Field(default=None, max_length=45)


class AuditoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_registro: int
    fecha: datetime | None
    servicio: str
    metodo: str
    ruta: str
    accion: str
    recurso_id: str | None
    codigo_estado: int
    exito: bool
    id_usuario: int | None
    roles: str | None
    ip: str | None
    duracion_ms: int | None


class AuditoriaPagina(BaseModel):
    total: int
    limite: int
    desplazamiento: int
    registros: list[AuditoriaOut]


class NotificacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_notificacion: int
    id_orden: int
    id_cliente: int | None
    tipo: str
    canal: str
    destinatario: str | None
    asunto: str
    mensaje: str
    estado: str
    detalle_error: str | None
    fecha: datetime | None


class Seccion(BaseModel):
    """Cada parte del panel: si un servicio está caído, esa sección trae el error y las demás siguen."""
    disponible: bool
    error: str | None = None
    datos: dict | None = None


class PanelOut(BaseModel):
    generado: datetime
    ordenes: Seccion
    finanzas: Seccion
    inventario: Seccion
    garantias: Seccion
    auditoria: Seccion
