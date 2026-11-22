"""Auditoría, notificaciones y reportes."""
from datetime import date
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import (UsuarioToken, gestiona_notificaciones, servicio_interno, solo_admin, ve_finanzas,
                               ve_inventario, ve_ordenes)
from app.database.session import get_db
from app.schemas.reportes import AuditoriaPagina, EventoIn, NotificacionOut, PanelOut
from app.services import auditoria_service, notificacion_service, reportes_service

router = APIRouter()
NOMBRES_SERVICIOS = Literal["ms-usuarios", "ms-clientes", "ms-ordenes", "ms-reparaciones", "ms-inventario",
                            "ms-facturacion"]


# ---------- Auditoría ----------
@router.post("/auditoria/eventos", status_code=status.HTTP_201_CREATED, tags=["Auditoría"],
             summary="Recibir un evento (solo microservicios, con token de servicio)")
def recibir_evento(evento: EventoIn, tareas: BackgroundTasks, db: Session = Depends(get_db),
                   servicio: str = Depends(servicio_interno)):
    if servicio != evento.servicio:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "El servicio del token no coincide con el del evento")
    r = auditoria_service.registrar(db, evento)
    if notificacion_service.debe_notificar(evento):
        tareas.add_task(notificacion_service.generar_en_segundo_plano, int(evento.recurso_id))
    return {"id_registro": r.id_registro}


@router.get("/auditoria", response_model=AuditoriaPagina, tags=["Auditoría"],
            summary="Consultar la bitácora (filtros y paginación)")
def consultar_auditoria(servicio: NOMBRES_SERVICIOS | None = None, id_usuario: int | None = None,
                        metodo: Literal["POST", "PUT", "PATCH", "DELETE"] | None = None, solo_fallidos: bool = False,
                        desde: date | None = None, hasta: date | None = None,
                        limite: int = Query(100, ge=1, le=500), desplazamiento: int = Query(0, ge=0),
                        db: Session = Depends(get_db), _: UsuarioToken = Depends(solo_admin)):
    return auditoria_service.listar(db, servicio, id_usuario, metodo, solo_fallidos, desde, hasta, limite,
                                    desplazamiento)


@router.get("/auditoria/resumen", tags=["Auditoría"], summary="Resumen de las últimas horas")
def resumen_auditoria(horas: int = Query(24, ge=1, le=720), db: Session = Depends(get_db),
                      _: UsuarioToken = Depends(solo_admin)):
    return auditoria_service.resumen(db, horas)


# ---------- Notificaciones ----------
@router.get("/notificaciones", response_model=list[NotificacionOut], tags=["Notificaciones"])
def notificaciones(id_orden: int | None = None, id_cliente: int | None = None,
                   estado: Literal["ENVIADA", "FALLIDA"] | None = None, db: Session = Depends(get_db),
                   _: UsuarioToken = Depends(gestiona_notificaciones)):
    return notificacion_service.listar(db, id_orden, id_cliente, estado)


@router.post("/notificaciones/ordenes/{id_orden}", response_model=NotificacionOut, tags=["Notificaciones"],
             summary="Reenviar la notificación del estado actual de una orden")
def reenviar(id_orden: int, db: Session = Depends(get_db), _: UsuarioToken = Depends(gestiona_notificaciones)):
    n = notificacion_service.generar(db, id_orden, forzar=True)
    if n is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "No se pudo notificar: la orden no existe, su estado no se notifica o ms-ordenes no responde")
    return n


# ---------- Reportes ----------
def _o_503(funcion, *args):
    try:
        return funcion(*args)
    except reportes_service.externos.ServicioNoDisponible as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e))


@router.get("/reportes/ordenes", tags=["Reportes"], summary="Órdenes pendientes y finalizadas, carga por técnico")
def reporte_ordenes(u: UsuarioToken = Depends(ve_ordenes)):
    return _o_503(reportes_service.ordenes, u.token)


@router.get("/reportes/finanzas", tags=["Reportes"], summary="Ingresos y pagos pendientes (cartera)")
def reporte_finanzas(desde: date | None = None, hasta: date | None = None, u: UsuarioToken = Depends(ve_finanzas)):
    return _o_503(reportes_service.finanzas, u.token, desde, hasta)


@router.get("/reportes/inventario", tags=["Reportes"], summary="Repuestos con existencias bajas y valor del inventario")
def reporte_inventario(u: UsuarioToken = Depends(ve_inventario)):
    return _o_503(reportes_service.inventario, u.token)


@router.get("/reportes/garantias", tags=["Reportes"], summary="Garantías vigentes, por vencer y reclamaciones")
def reporte_garantias(u: UsuarioToken = Depends(ve_ordenes)):
    return _o_503(reportes_service.garantias, u.token)


@router.get("/reportes/panel", response_model=PanelOut, tags=["Reportes"],
            summary="Tablero del administrador (todas las secciones)")
def panel(db: Session = Depends(get_db), u: UsuarioToken = Depends(solo_admin)):
    return reportes_service.panel(db, u.token)
