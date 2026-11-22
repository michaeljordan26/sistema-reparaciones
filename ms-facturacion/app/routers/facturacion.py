"""Presupuestos, respuestas del cliente, facturas, pagos, saldos y reportes de dinero."""
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (UsuarioToken, atiende_cliente, caja, cobra, get_current_user,
                               puede_presupuestar, solo_admin)
from app.database.session import get_db
from app.schemas.facturacion import (AnularIn, CarteraOut, FacturaCreate, FacturaOut, IngresosOut, PagoIn,
                                     PagoOut, PresupuestoCreate, PresupuestoOut, RespuestaIn, SaldoOrden)
from app.services import facturacion_service as svc

router = APIRouter()


# ---------- Presupuestos ----------
@router.post("/presupuestos", response_model=PresupuestoOut, status_code=status.HTTP_201_CREATED,
             tags=["Presupuestos"], summary="Crear presupuesto (orden ESPERANDO_APROBACION)")
def crear_presupuesto(datos: PresupuestoCreate, db: Session = Depends(get_db),
                      u: UsuarioToken = Depends(puede_presupuestar)):
    return svc.crear_presupuesto(db, datos, u)


@router.get("/presupuestos/{id_presupuesto}", response_model=PresupuestoOut, tags=["Presupuestos"])
def obtener_presupuesto(id_presupuesto: int, db: Session = Depends(get_db),
                        _: UsuarioToken = Depends(get_current_user)):
    return svc.obtener_presupuesto(db, id_presupuesto)


@router.get("/ordenes/{id_orden}/presupuesto", response_model=PresupuestoOut, tags=["Presupuestos"],
            summary="Presupuesto vigente de una orden (lo consulta ms-ordenes)")
def presupuesto_orden(id_orden: int, db: Session = Depends(get_db), _: UsuarioToken = Depends(get_current_user)):
    p = svc.presupuesto_de_orden(db, id_orden)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La orden no tiene presupuesto")
    return p


@router.post("/presupuestos/{id_presupuesto}/respuesta", response_model=PresupuestoOut, tags=["Presupuestos"],
             summary="Registrar aprobación o rechazo del cliente (mueve la orden en ms-ordenes)")
def responder(id_presupuesto: int, datos: RespuestaIn, db: Session = Depends(get_db),
              u: UsuarioToken = Depends(atiende_cliente)):
    return svc.responder_presupuesto(db, id_presupuesto, datos, u)


@router.patch("/presupuestos/{id_presupuesto}/anular", response_model=PresupuestoOut, tags=["Presupuestos"],
              summary="Anular presupuesto pendiente (para elaborar uno nuevo)")
def anular_presupuesto(id_presupuesto: int, datos: AnularIn, db: Session = Depends(get_db),
                       _: UsuarioToken = Depends(caja)):
    return svc.anular_presupuesto(db, id_presupuesto, datos)


# ---------- Facturas ----------
@router.post("/facturas", response_model=FacturaOut, status_code=status.HTTP_201_CREATED, tags=["Facturas"],
             summary="Generar factura (orden LISTO_ENTREGA con presupuesto aprobado)")
def generar_factura(datos: FacturaCreate, db: Session = Depends(get_db), u: UsuarioToken = Depends(caja)):
    return svc.generar_factura(db, datos, u)


@router.get("/facturas", response_model=list[FacturaOut], tags=["Facturas"],
            summary="Listar facturas (filtrar por estado u orden)")
def listar_facturas(estado: Literal["PENDIENTE", "PARCIAL", "PAGADA", "ANULADA"] | None = None,
                    id_orden: int | None = None, db: Session = Depends(get_db),
                    _: UsuarioToken = Depends(get_current_user)):
    return svc.listar_facturas(db, estado, id_orden)


@router.get("/facturas/{id_factura}", response_model=FacturaOut, tags=["Facturas"])
def obtener_factura(id_factura: int, db: Session = Depends(get_db), _: UsuarioToken = Depends(get_current_user)):
    return svc.obtener_factura(db, id_factura)


@router.patch("/facturas/{id_factura}/anular", response_model=FacturaOut, tags=["Facturas"],
              summary="Anular factura sin pagos (solo administrador)")
def anular_factura(id_factura: int, datos: AnularIn, db: Session = Depends(get_db),
                   _: UsuarioToken = Depends(solo_admin)):
    return svc.anular_factura(db, id_factura, datos)


# ---------- Pagos ----------
@router.post("/facturas/{id_factura}/pagos", response_model=PagoOut, status_code=status.HTTP_201_CREATED,
             tags=["Pagos"], summary="Registrar pago o abono (no puede superar el saldo)")
def pagar(id_factura: int, datos: PagoIn, db: Session = Depends(get_db), u: UsuarioToken = Depends(cobra)):
    return svc.registrar_pago(db, id_factura, datos, u)


@router.patch("/pagos/{id_pago}/anular", response_model=PagoOut, tags=["Pagos"],
              summary="Anular un pago registrado por error (solo administrador)")
def anular_pago(id_pago: int, datos: AnularIn, db: Session = Depends(get_db), _: UsuarioToken = Depends(solo_admin)):
    return svc.anular_pago(db, id_pago, datos)


@router.get("/ordenes/{id_orden}/saldo", response_model=SaldoOrden, tags=["Pagos"],
            summary="Saldo pendiente de una orden (lo consulta ms-ordenes antes de entregar)")
def saldo(id_orden: int, db: Session = Depends(get_db), _: UsuarioToken = Depends(get_current_user)):
    return svc.saldo_de_orden(db, id_orden)


# ---------- Reportes ----------
@router.get("/reportes/ingresos", response_model=IngresosOut, tags=["Reportes"],
            summary="Ingresos por rango de fechas (por defecto, últimos 30 días)")
def reporte_ingresos(desde: date | None = None, hasta: date | None = None, db: Session = Depends(get_db),
                     _: UsuarioToken = Depends(caja)):
    return svc.ingresos(db, desde, hasta)


@router.get("/reportes/cartera", response_model=CarteraOut, tags=["Reportes"],
            summary="Facturas con saldo pendiente (pagos pendientes)")
def reporte_cartera(db: Session = Depends(get_db), _: UsuarioToken = Depends(caja)):
    return svc.cartera(db)
