"""Verifica los tokens emitidos por ms-usuarios (misma clave secreta).
Guarda también el token original para reenviarlo a los otros microservicios."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class UsuarioToken:
    id_usuario: int
    roles: list[str]
    token: str

    def tiene_rol(self, *roles: str) -> bool:
        return bool(set(self.roles).intersection(roles))


def get_current_user(cred: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> UsuarioToken:
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Falta el token", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(cred.credentials, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return UsuarioToken(int(payload["sub"]), list(payload.get("roles", [])), cred.credentials)
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido o expirado",
                            headers={"WWW-Authenticate": "Bearer"})


def require_roles(*roles_permitidos: str):
    def verificador(usuario: UsuarioToken = Depends(get_current_user)) -> UsuarioToken:
        if not usuario.tiene_rol(*roles_permitidos):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No tiene permisos para esta operación")
        return usuario
    return verificador


# Grupos de permisos
solo_admin = require_roles("ADMINISTRADOR")
ve_ordenes = require_roles("ADMINISTRADOR", "RECEPCIONISTA")
ve_finanzas = require_roles("ADMINISTRADOR", "CAJA")
ve_inventario = require_roles("ADMINISTRADOR", "INVENTARIO")
gestiona_notificaciones = require_roles("ADMINISTRADOR", "RECEPCIONISTA")


# ---------- Comunicación entre servicios ----------
def servicio_interno(cred: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> str:
    """Solo los microservicios (token con rol SERVICIO firmado con la clave compartida) envían eventos."""
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Falta el token de servicio")
    try:
        datos = jwt.decode(cred.credentials, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token de servicio inválido")
    if "SERVICIO" not in datos.get("roles", []) or not str(datos.get("sub", "")).startswith("servicio:"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo los microservicios pueden registrar auditoría")
    return str(datos["sub"]).removeprefix("servicio:")


def token_sistema() -> str:
    """Token de corta duración con el que ms-reportes consulta otros servicios por su cuenta
    (por ejemplo, para armar una notificación). sub=0 identifica al 'sistema'."""
    datos = {"sub": "0", "roles": ["ADMINISTRADOR"], "exp": datetime.now(timezone.utc) + timedelta(minutes=2)}
    return jwt.encode(datos, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
