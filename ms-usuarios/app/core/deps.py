"""Dependencias reutilizables: usuario actual y control de roles."""
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.session import get_db
from app.models import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

CREDENCIALES_INVALIDAS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token inválido o expirado",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Usuario:
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise CREDENCIALES_INVALIDAS
    usuario = db.get(Usuario, user_id)
    if usuario is None or not usuario.activo:
        raise CREDENCIALES_INVALIDAS
    return usuario


def require_roles(*roles_permitidos: str):
    """Uso: Depends(require_roles("ADMINISTRADOR")). Devuelve 403 si no tiene el rol."""
    def verificador(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        roles_usuario = {r.nombre for r in usuario.roles}
        if not roles_usuario.intersection(roles_permitidos):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="No tiene permisos para esta operación")
        return usuario
    return verificador
