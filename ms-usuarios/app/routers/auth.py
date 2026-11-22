"""CU01 Iniciar sesión y CU06 Validar acceso según el rol."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import create_access_token
from app.database.session import get_db
from app.models import Usuario
from app.schemas.usuario import Token, TokenValidado, UsuarioOut
from app.services import usuario_service as svc

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=Token, summary="Iniciar sesión (usuario o correo + contraseña)")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = svc.autenticar(db, form.username, form.password)
    if usuario is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario o contraseña incorrectos",
                            headers={"WWW-Authenticate": "Bearer"})
    token = create_access_token(usuario.id_usuario, [r.nombre for r in usuario.roles])
    return Token(access_token=token)


@router.get("/me", response_model=UsuarioOut, summary="Datos del usuario que inició sesión")
def me(usuario: Usuario = Depends(get_current_user)):
    return usuario


@router.get("/validar", response_model=TokenValidado,
            summary="Validar token (lo usan los otros microservicios)")
def validar(usuario: Usuario = Depends(get_current_user)):
    return TokenValidado(
        id_usuario=usuario.id_usuario,
        nombre_usuario=usuario.nombre_usuario,
        roles=[r.nombre for r in usuario.roles],
        id_tecnico=usuario.tecnico.id_tecnico if usuario.tecnico else None,
    )
