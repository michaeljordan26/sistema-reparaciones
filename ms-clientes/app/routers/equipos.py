"""CU09 Registrar equipo, CU10 Consultar y actualizar equipo."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import UsuarioToken, get_current_user, puede_registrar
from app.database.session import get_db
from app.schemas.cliente import EquipoCreate, EquipoDetalle, EquipoOut, EquipoUpdate
from app.services import cliente_service as svc

router = APIRouter(prefix="/equipos", tags=["Equipos"])


@router.post("", response_model=EquipoOut, status_code=status.HTTP_201_CREATED, summary="Registrar equipo")
def crear(datos: EquipoCreate, db: Session = Depends(get_db), _: UsuarioToken = Depends(puede_registrar)):
    return svc.crear_equipo(db, datos)


@router.get("", response_model=list[EquipoOut], summary="Listar equipos (filtrar por serie o cliente)")
def listar(numero_serie: str | None = None, id_cliente: int | None = None, db: Session = Depends(get_db),
           _: UsuarioToken = Depends(get_current_user)):
    return svc.listar_equipos(db, numero_serie, id_cliente)


@router.get("/{id_equipo}", response_model=EquipoDetalle,
            summary="Consultar equipo con su cliente (lo usa ms-ordenes)")
def obtener(id_equipo: int, db: Session = Depends(get_db), _: UsuarioToken = Depends(get_current_user)):
    return svc.obtener_equipo(db, id_equipo)


@router.put("/{id_equipo}", response_model=EquipoOut, summary="Actualizar equipo")
def actualizar(id_equipo: int, datos: EquipoUpdate, db: Session = Depends(get_db),
               _: UsuarioToken = Depends(puede_registrar)):
    return svc.actualizar_equipo(db, id_equipo, datos)
