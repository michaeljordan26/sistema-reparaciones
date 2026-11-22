
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import UsuarioToken, get_current_user, puede_registrar, solo_admin
from app.database.session import get_db
from app.schemas.cliente import ClienteConEquipos, ClienteCreate, ClienteOut, ClienteUpdate, EquipoOut
from app.services import cliente_service as svc

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.post("", response_model=ClienteOut, status_code=status.HTTP_201_CREATED, summary="Registrar cliente")
def crear(datos: ClienteCreate, db: Session = Depends(get_db), _: UsuarioToken = Depends(puede_registrar)):
    return svc.crear_cliente(db, datos)


@router.get("", response_model=list[ClienteOut], summary="Listar o buscar clientes (documento, nombre o teléfono)")
def listar(buscar: str | None = None, solo_activos: bool = True, db: Session = Depends(get_db),
           _: UsuarioToken = Depends(get_current_user)):
    return svc.listar_clientes(db, buscar, solo_activos)


@router.get("/{id_cliente}", response_model=ClienteConEquipos, summary="Consultar cliente con sus equipos")
def obtener(id_cliente: int, db: Session = Depends(get_db), _: UsuarioToken = Depends(get_current_user)):
    return svc.obtener_cliente(db, id_cliente)


@router.get("/{id_cliente}/equipos", response_model=list[EquipoOut], summary="Equipos de un cliente")
def equipos(id_cliente: int, db: Session = Depends(get_db), _: UsuarioToken = Depends(get_current_user)):
    return svc.obtener_cliente(db, id_cliente).equipos


@router.put("/{id_cliente}", response_model=ClienteOut, summary="Actualizar cliente")
def actualizar(id_cliente: int, datos: ClienteUpdate, db: Session = Depends(get_db),
               _: UsuarioToken = Depends(puede_registrar)):
    return svc.actualizar_cliente(db, id_cliente, datos)


@router.patch("/{id_cliente}/desactivar", response_model=ClienteOut, summary="Desactivar cliente")
def desactivar(id_cliente: int, db: Session = Depends(get_db), _: UsuarioToken = Depends(solo_admin)):
    return svc.cambiar_estado_cliente(db, id_cliente, "INACTIVO")


@router.patch("/{id_cliente}/activar", response_model=ClienteOut, summary="Reactivar cliente")
def activar(id_cliente: int, db: Session = Depends(get_db), _: UsuarioToken = Depends(solo_admin)):
    return svc.cambiar_estado_cliente(db, id_cliente, "ACTIVO")
