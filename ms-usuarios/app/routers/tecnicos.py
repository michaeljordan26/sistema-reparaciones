"""CU05 Registrar y actualizar técnicos."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.database.session import get_db
from app.models import Usuario
from app.schemas.usuario import EstadoLaboral, TecnicoCreate, TecnicoOut, TecnicoUpdate
from app.services import usuario_service as svc

router = APIRouter(prefix="/tecnicos", tags=["Técnicos"])
solo_admin = require_roles("ADMINISTRADOR")


@router.post("", response_model=TecnicoOut, status_code=status.HTTP_201_CREATED,
             summary="Registrar perfil de técnico")
def crear(datos: TecnicoCreate, db: Session = Depends(get_db), _: Usuario = Depends(solo_admin)):
    return svc.crear_tecnico(db, datos)


@router.get("", response_model=list[TecnicoOut], summary="Listar técnicos (cualquier usuario autenticado)")
def listar(estado: EstadoLaboral | None = None, db: Session = Depends(get_db),
           _: Usuario = Depends(get_current_user)):
    return svc.listar_tecnicos(db, estado)


@router.get("/{id_tecnico}", response_model=TecnicoOut, summary="Consultar técnico")
def obtener(id_tecnico: int, db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    return svc.obtener_tecnico(db, id_tecnico)


@router.put("/{id_tecnico}", response_model=TecnicoOut, summary="Actualizar técnico")
def actualizar(id_tecnico: int, datos: TecnicoUpdate, db: Session = Depends(get_db),
               _: Usuario = Depends(solo_admin)):
    return svc.actualizar_tecnico(db, id_tecnico, datos)
