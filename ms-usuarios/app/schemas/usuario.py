"""Esquemas Pydantic: validan lo que entra y definen lo que sale de la API."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

NombreRol = Literal["ADMINISTRADOR", "RECEPCIONISTA", "TECNICO", "CAJA", "INVENTARIO"]
EstadoLaboral = Literal["ACTIVO", "VACACIONES", "INACTIVO"]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RolOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_rol: int
    nombre: str
    descripcion: str | None = None


class UsuarioCreate(BaseModel):
    nombres: str = Field(min_length=2, max_length=80)
    apellidos: str = Field(min_length=2, max_length=80)
    correo: EmailStr
    nombre_usuario: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.]+$")
    contrasena: str = Field(min_length=8, max_length=72)
    roles: list[NombreRol] = Field(min_length=1)


class UsuarioUpdate(BaseModel):
    nombres: str | None = Field(default=None, min_length=2, max_length=80)
    apellidos: str | None = Field(default=None, min_length=2, max_length=80)
    correo: EmailStr | None = None
    contrasena: str | None = Field(default=None, min_length=8, max_length=72)
    activo: bool | None = None


class AsignarRoles(BaseModel):
    roles: list[NombreRol] = Field(min_length=1)


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_usuario: int
    nombres: str
    apellidos: str
    correo: str
    nombre_usuario: str
    activo: bool
    fecha_creacion: datetime | None = None
    roles: list[RolOut] = []


class TecnicoCreate(BaseModel):
    id_usuario: int
    especialidad: str = Field(min_length=3, max_length=100)
    estado_laboral: EstadoLaboral = "ACTIVO"


class TecnicoUpdate(BaseModel):
    especialidad: str | None = Field(default=None, min_length=3, max_length=100)
    estado_laboral: EstadoLaboral | None = None


class TecnicoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_tecnico: int
    id_usuario: int
    especialidad: str
    estado_laboral: str
    usuario: UsuarioOut


class TokenValidado(BaseModel):
    """Respuesta que usan los OTROS microservicios para validar un token."""
    id_usuario: int
    nombre_usuario: str
    roles: list[str]
    id_tecnico: int | None = None
