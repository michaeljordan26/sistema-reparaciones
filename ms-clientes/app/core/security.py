"""Este servicio NO crea tokens ni guarda contraseñas: solo VERIFICA los tokens
emitidos por ms-usuarios, usando la misma clave secreta compartida."""
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

# En Swagger: botón Authorize -> pegar el access_token obtenido en ms-usuarios
bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class UsuarioToken:
    id_usuario: int
    roles: list[str]


def get_current_user(cred: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> UsuarioToken:
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Falta el token",
                            headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(cred.credentials, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return UsuarioToken(id_usuario=int(payload["sub"]), roles=list(payload.get("roles", [])))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido o expirado",
                            headers={"WWW-Authenticate": "Bearer"})


def require_roles(*roles_permitidos: str):
    def verificador(usuario: UsuarioToken = Depends(get_current_user)) -> UsuarioToken:
        if not set(usuario.roles).intersection(roles_permitidos):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No tiene permisos para esta operación")
        return usuario
    return verificador


# Grupos de permisos usados en las rutas
puede_registrar = require_roles("ADMINISTRADOR", "RECEPCIONISTA")
solo_admin = require_roles("ADMINISTRADOR")
