"""CU12–CU17: órdenes de trabajo. CU11: historial de servicios de un equipo."""
from typing import Literal

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core import estados as E
from app.core.security import UsuarioToken, get_current_user, personal_taller, puede_recibir
from app.database.session import get_db
from app.schemas.orden import (AsignarTecnico, CambioEstado, Estado, HistorialOut, OrdenCreate,
                               OrdenDetalle, OrdenOut)
from app.services import orden_service as svc

router = APIRouter(tags=["Órdenes de trabajo"])


def _detalle(orden) -> OrdenDetalle:
    d = OrdenDetalle.model_validate(orden)
    d.transiciones_permitidas = E.TRANSICIONES[orden.estado_actual]
    return d


@router.get("/ordenes/estados", summary="Estados y transiciones permitidas")
def mapa_estados():
    return {"estados": E.ESTADOS, "transiciones": E.TRANSICIONES}


@router.post("/ordenes", response_model=OrdenDetalle, status_code=status.HTTP_201_CREATED,
             summary="Crear orden de trabajo (recepción del equipo)")
def crear(datos: OrdenCreate, db: Session = Depends(get_db), usuario: UsuarioToken = Depends(puede_recibir)):
    return _detalle(svc.crear_orden(db, datos, usuario))


@router.get("/ordenes", response_model=list[OrdenOut], summary="Listar órdenes (pendientes, finalizadas y filtros)")
def listar(grupo: Literal["pendientes", "finalizadas"] | None = None, estado: Estado | None = None,
           id_equipo: int | None = None, id_cliente: int | None = None, id_tecnico: int | None = None,
           db: Session = Depends(get_db), _: UsuarioToken = Depends(get_current_user)):
    return svc.listar_ordenes(db, grupo, estado, id_equipo, id_cliente, id_tecnico)


@router.get("/ordenes/mis-ordenes", response_model=list[OrdenOut], summary="Órdenes asignadas al técnico actual")
def mis_ordenes(db: Session = Depends(get_db), usuario: UsuarioToken = Depends(personal_taller)):
    return svc.listar_ordenes(db, grupo="pendientes", id_usuario_tecnico=usuario.id_usuario)


@router.get("/ordenes/{id_orden}", response_model=OrdenDetalle, summary="Consultar orden con historial")
def obtener(id_orden: int, db: Session = Depends(get_db), _: UsuarioToken = Depends(get_current_user)):
    return _detalle(svc.obtener_orden(db, id_orden))


@router.post("/ordenes/{id_orden}/asignar", response_model=OrdenDetalle, summary="Asignar o reasignar técnico")
def asignar(id_orden: int, datos: AsignarTecnico, db: Session = Depends(get_db),
            usuario: UsuarioToken = Depends(puede_recibir)):
    return _detalle(svc.asignar_tecnico(db, id_orden, datos, usuario))


@router.patch("/ordenes/{id_orden}/estado", response_model=OrdenDetalle, summary="Cambiar el estado de la orden")
def cambiar_estado(id_orden: int, datos: CambioEstado, db: Session = Depends(get_db),
                   usuario: UsuarioToken = Depends(personal_taller)):
    return _detalle(svc.cambiar_estado(db, id_orden, datos, usuario))


@router.get("/ordenes/{id_orden}/historial", response_model=list[HistorialOut], summary="Historial de estados")
def historial(id_orden: int, db: Session = Depends(get_db), _: UsuarioToken = Depends(get_current_user)):
    return svc.obtener_orden(db, id_orden).historial


@router.get("/equipos/{id_equipo}/historial", response_model=list[OrdenDetalle],
            summary="CU11: historial de servicios de un equipo")
def historial_equipo(id_equipo: int, db: Session = Depends(get_db), _: UsuarioToken = Depends(get_current_user)):
    return [_detalle(o) for o in svc.listar_ordenes(db, id_equipo=id_equipo)]
