"""Verifica los tokens emitidos por ms-usuarios (misma clave secreta).
Guarda también el token original para reenviarlo a los otros microservicios."""
from dataclasses import dataclass

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
puede_presupuestar = require_roles("ADMINISTRADOR", "TECNICO", "RECEPCIONISTA", "CAJA")
atiende_cliente = require_roles("ADMINISTRADOR", "RECEPCIONISTA", "CAJA")
caja = require_roles("ADMINISTRADOR", "CAJA")
cobra = require_roles("ADMINISTRADOR", "CAJA", "RECEPCIONISTA")
solo_admin = require_roles("ADMINISTRADOR")
