"""CU02 Registrar usuario, CU03 Gestionar usuarios, CU04 Asignar roles."""
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.database.session import get_db
from app.models import Rol, Usuario
from app.schemas.usuario import AsignarRoles, RolOut, UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.services import usuario_service as svc

router = APIRouter(tags=["Usuarios y roles"])
solo_admin = require_roles("ADMINISTRADOR")


@router.get("/roles", response_model=list[RolOut], summary="Listar roles")
def listar_roles(db: Session = Depends(get_db), _: Usuario = Depends(solo_admin)):
    return db.scalars(select(Rol).order_by(Rol.id_rol)).all()


@router.post("/usuarios", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED,
             summary="Registrar usuario")
def crear(datos: UsuarioCreate, db: Session = Depends(get_db), _: Usuario = Depends(solo_admin)):
    return svc.crear_usuario(db, datos)


@router.get("/usuarios", response_model=list[UsuarioOut], summary="Listar usuarios")
def listar(solo_activos: bool = False, db: Session = Depends(get_db), _: Usuario = Depends(solo_admin)):
    return svc.listar_usuarios(db, solo_activos)


@router.get("/usuarios/{id_usuario}", response_model=UsuarioOut, summary="Consultar usuario")
def obtener(id_usuario: int, db: Session = Depends(get_db), _: Usuario = Depends(solo_admin)):
    return svc.obtener_usuario(db, id_usuario)


@router.put("/usuarios/{id_usuario}", response_model=UsuarioOut, summary="Actualizar usuario")
def actualizar(id_usuario: int, datos: UsuarioUpdate, db: Session = Depends(get_db),
               _: Usuario = Depends(solo_admin)):
    return svc.actualizar_usuario(db, id_usuario, datos)


@router.patch("/usuarios/{id_usuario}/desactivar", response_model=UsuarioOut, summary="Desactivar usuario")
def desactivar(id_usuario: int, db: Session = Depends(get_db), actual: Usuario = Depends(solo_admin)):
    return svc.desactivar_usuario(db, id_usuario, actual.id_usuario)


@router.put("/usuarios/{id_usuario}/roles", response_model=UsuarioOut, summary="Asignar roles")
def roles(id_usuario: int, datos: AsignarRoles, db: Session = Depends(get_db),
          _: Usuario = Depends(solo_admin)):
    return svc.asignar_roles(db, id_usuario, datos.roles)
