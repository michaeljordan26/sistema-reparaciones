"""Diagnósticos, reparaciones (con repuestos) y garantías."""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (UsuarioToken, get_current_user, recepcion_o_admin, solo_admin,
                               tecnico_o_admin)
from app.database.session import get_db
from app.schemas.reparacion import (AnularGarantia, DiagnosticoCreate, DiagnosticoOut, FinalizarReparacion,
                                    GarantiaOut, ReclamacionCreate, ReclamacionOut, ReclamacionResolver,
                                    ReparacionCreate, ReparacionOut, RepuestoUsoIn, ResumenOrden)
from app.services import reparacion_service as svc

router = APIRouter()


# ---------- Diagnósticos ----------
@router.post("/diagnosticos", response_model=DiagnosticoOut, status_code=status.HTTP_201_CREATED,
             tags=["Diagnósticos"], summary="Registrar diagnóstico (pasa la orden a ESPERANDO_APROBACION)")
def crear_diagnostico(datos: DiagnosticoCreate, db: Session = Depends(get_db),
                      u: UsuarioToken = Depends(tecnico_o_admin)):
    return svc.registrar_diagnostico(db, datos, u)


@router.get("/ordenes/{id_orden}/diagnostico", response_model=DiagnosticoOut, tags=["Diagnósticos"],
            summary="Diagnóstico de una orden")
def diagnostico_orden(id_orden: int, db: Session = Depends(get_db), _: UsuarioToken = Depends(get_current_user)):
    d = svc.obtener_diagnostico_por_orden(db, id_orden)
    if d is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La orden no tiene diagnóstico")
    return d


# ---------- Reparaciones ----------
@router.post("/reparaciones", response_model=ReparacionOut, status_code=status.HTTP_201_CREATED,
             tags=["Reparaciones"], summary="Iniciar reparación (orden EN_REPARACION)")
def iniciar(datos: ReparacionCreate, db: Session = Depends(get_db), u: UsuarioToken = Depends(tecnico_o_admin)):
    return svc.iniciar_reparacion(db, datos, u)


@router.get("/reparaciones/{id_reparacion}", response_model=ReparacionOut, tags=["Reparaciones"])
def obtener(id_reparacion: int, db: Session = Depends(get_db), _: UsuarioToken = Depends(get_current_user)):
    return svc.obtener_reparacion(db, id_reparacion)


@router.post("/reparaciones/{id_reparacion}/repuestos", response_model=ReparacionOut, status_code=201,
             tags=["Reparaciones"], summary="Usar un repuesto (descuenta stock en ms-inventario)")
def agregar_repuesto(id_reparacion: int, datos: RepuestoUsoIn, db: Session = Depends(get_db),
                     u: UsuarioToken = Depends(tecnico_o_admin)):
    return svc.agregar_repuesto(db, id_reparacion, datos, u)


@router.delete("/reparaciones/{id_reparacion}/repuestos/{id_repuesto_utilizado}", response_model=ReparacionOut,
               tags=["Reparaciones"], summary="Quitar un repuesto (lo devuelve al inventario)")
def quitar_repuesto(id_reparacion: int, id_repuesto_utilizado: int, db: Session = Depends(get_db),
                    u: UsuarioToken = Depends(tecnico_o_admin)):
    return svc.quitar_repuesto(db, id_reparacion, id_repuesto_utilizado, u)


@router.post("/reparaciones/{id_reparacion}/finalizar", response_model=ReparacionOut, tags=["Reparaciones"],
             summary="Finalizar reparación (orden a LISTO_ENTREGA y crea la garantía)")
def finalizar(id_reparacion: int, datos: FinalizarReparacion, db: Session = Depends(get_db),
              u: UsuarioToken = Depends(tecnico_o_admin)):
    return svc.finalizar_reparacion(db, id_reparacion, datos, u)


@router.get("/ordenes/{id_orden}/resumen", response_model=ResumenOrden, tags=["Reparaciones"],
            summary="Diagnóstico + reparación + garantía de una orden")
def resumen(id_orden: int, db: Session = Depends(get_db), _: UsuarioToken = Depends(get_current_user)):
    rep = svc.obtener_reparacion_por_orden(db, id_orden)
    return ResumenOrden(id_orden=id_orden, diagnostico=svc.obtener_diagnostico_por_orden(db, id_orden),
                        reparacion=rep, garantia=rep.garantia if rep else None)


# ---------- Garantías ----------
@router.get("/garantias", response_model=list[GarantiaOut], tags=["Garantías"],
            summary="Listar garantías (estado, cliente o equipo)")
def listar_garantias(estado: Literal["VIGENTE", "VENCIDA", "ANULADA"] | None = None, id_cliente: int | None = None,
                     id_equipo: int | None = None, db: Session = Depends(get_db),
                     _: UsuarioToken = Depends(get_current_user)):
    return svc.listar_garantias(db, estado, id_cliente, id_equipo)


@router.get("/garantias/{id_garantia}", response_model=GarantiaOut, tags=["Garantías"])
def obtener_garantia(id_garantia: int, db: Session = Depends(get_db), _: UsuarioToken = Depends(get_current_user)):
    return svc.obtener_garantia(db, id_garantia)


@router.patch("/garantias/{id_garantia}/anular", response_model=GarantiaOut, tags=["Garantías"],
              summary="Anular garantía (solo administrador)")
def anular(id_garantia: int, datos: AnularGarantia, db: Session = Depends(get_db),
           _: UsuarioToken = Depends(solo_admin)):
    return svc.anular_garantia(db, id_garantia, datos)


@router.post("/garantias/{id_garantia}/reclamaciones", response_model=ReclamacionOut, status_code=201,
             tags=["Garantías"], summary="Registrar reclamación (solo si la garantía está vigente)")
def reclamar(id_garantia: int, datos: ReclamacionCreate, db: Session = Depends(get_db),
             u: UsuarioToken = Depends(recepcion_o_admin)):
    return svc.crear_reclamacion(db, id_garantia, datos, u)


@router.patch("/reclamaciones/{id_reclamacion}", response_model=ReclamacionOut, tags=["Garantías"],
              summary="Aprobar o rechazar una reclamación (solo administrador)")
def resolver(id_reclamacion: int, datos: ReclamacionResolver, db: Session = Depends(get_db),
             u: UsuarioToken = Depends(solo_admin)):
    return svc.resolver_reclamacion(db, id_reclamacion, datos, u)
