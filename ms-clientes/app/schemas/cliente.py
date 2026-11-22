
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

TipoDocumento = Literal["CC", "CE", "NIT", "TI", "PAS"]
TipoEquipo = Literal["PORTATIL", "ESCRITORIO", "TODO_EN_UNO", "IMPRESORA", "TABLET", "SERVIDOR", "OTRO"]
Estado = Literal["ACTIVO", "INACTIVO"]


# ---------- Cliente ----------
class ClienteBase(BaseModel):
    nombres: str = Field(min_length=2, max_length=80)
    apellidos: str = Field(min_length=2, max_length=80)
    telefono: str = Field(min_length=7, max_length=20, pattern=r"^[0-9+ ()-]+$")
    correo: EmailStr | None = None
    direccion: str | None = Field(default=None, max_length=150)


class ClienteCreate(ClienteBase):
    tipo_documento: TipoDocumento
    numero_documento: str = Field(min_length=4, max_length=20, pattern=r"^[0-9A-Za-z-]+$")


class ClienteUpdate(BaseModel):
    nombres: str | None = Field(default=None, min_length=2, max_length=80)
    apellidos: str | None = Field(default=None, min_length=2, max_length=80)
    telefono: str | None = Field(default=None, min_length=7, max_length=20, pattern=r"^[0-9+ ()-]+$")
    correo: EmailStr | None = None
    direccion: str | None = Field(default=None, max_length=150)


class ClienteOut(ClienteCreate):
    model_config = ConfigDict(from_attributes=True)
    id_cliente: int
    correo: str | None = None
    fecha_registro: datetime | None = None
    estado: str


# ---------- Equipo ----------
class EquipoCreate(BaseModel):
    id_cliente: int
    tipo_equipo: TipoEquipo
    marca: str = Field(min_length=2, max_length=50)
    modelo: str = Field(min_length=1, max_length=80)
    numero_serie: str = Field(min_length=3, max_length=80)
    descripcion: str | None = Field(default=None, max_length=300)

    @field_validator("numero_serie")
    @classmethod
    def normalizar_serie(cls, v: str) -> str:
        return v.strip().upper()


class EquipoUpdate(BaseModel):
    tipo_equipo: TipoEquipo | None = None
    marca: str | None = Field(default=None, min_length=2, max_length=50)
    modelo: str | None = Field(default=None, min_length=1, max_length=80)
    descripcion: str | None = Field(default=None, max_length=300)
    estado: Estado | None = None


class EquipoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_equipo: int
    id_cliente: int
    tipo_equipo: str
    marca: str
    modelo: str
    numero_serie: str
    descripcion: str | None = None
    fecha_registro: datetime | None = None
    estado: str


class EquipoDetalle(EquipoOut):

    cliente: ClienteOut


class ClienteConEquipos(ClienteOut):
    equipos: list[EquipoOut] = []
