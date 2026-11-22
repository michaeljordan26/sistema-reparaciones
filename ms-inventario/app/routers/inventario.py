"""Repuestos, existencias, entradas, salidas, devoluciones, ajustes y consumo por orden."""
from typing import Literal

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import UsuarioToken, get_current_user, gestiona_inventario, puede_consumir
from app.database.session import get_db
from app.schemas.inventario import (AjusteIn, ConsumoOrden, DevolucionIn, EntradaIn, MovimientoConRepuesto,
                                    MovimientoOut, RepuestoCreate, RepuestoOut, RepuestoUpdate, SalidaIn)
from app.services import inventario_service as svc

router = APIRouter()
TipoMov = Literal["ENTRADA", "SALIDA", "DEVOLUCION", "AJUSTE_POSITIVO", "AJUSTE_NEGATIVO"]


# ---------- Repuestos ----------
@router.post("/repuestos", response_model=RepuestoOut, status_code=status.HTTP_201_CREATED,
             tags=["Repuestos"], summary="Registrar repuesto")
def crear(datos: RepuestoCreate, db: Session = Depends(get_db), u: UsuarioToken = Depends(gestiona_inventario)):
    return svc.crear_repuesto(db, datos, u)


@router.get("/repuestos", response_model=list[RepuestoOut], tags=["Repuestos"],
            summary="Consultar existencias (buscar, categoría, solo stock bajo)")
def listar(buscar: str | None = None, categoria: str | None = None, stock_bajo: bool = False,
           solo_activos: bool = True, db: Session = Depends(get_db), _: UsuarioToken = Depends(get_current_user)):
    return svc.listar_repuestos(db, buscar, categoria, stock_bajo, solo_activos)


@router.get("/repuestos/stock-bajo", response_model=list[RepuestoOut], tags=["Repuestos"],
            summary="Repuestos con existencias en el mínimo o por debajo (reporte)")
def stock_bajo(db: Session = Depends(get_db), _: UsuarioToken = Depends(get_current_user)):
    return svc.listar_repuestos(db, solo_stock_bajo=True)


@router.get("/repuestos/{id_repuesto}", response_model=RepuestoOut, tags=["Repuestos"], summary="Consultar repuesto")
def obtener(id_repuesto: int, db: Session = Depends(get_db), _: UsuarioToken = Depends(get_current_user)):
    return svc.obtener_repuesto(db, id_repuesto)


@router.put("/repuestos/{id_repuesto}", response_model=RepuestoOut, tags=["Repuestos"],
            summary="Actualizar datos y precios (el stock se cambia con movimientos)")
def actualizar(id_repuesto: int, datos: RepuestoUpdate, db: Session = Depends(get_db),
               _: UsuarioToken = Depends(gestiona_inventario)):
    return svc.actualizar_repuesto(db, id_repuesto, datos)


# ---------- Movimientos ----------
@router.post("/repuestos/{id_repuesto}/entradas", response_model=MovimientoOut, status_code=201,
             tags=["Movimientos"], summary="Registrar entrada (compra)")
def entrada(id_repuesto: int, datos: EntradaIn, db: Session = Depends(get_db),
            u: UsuarioToken = Depends(gestiona_inventario)):
    return svc.registrar_entrada(db, id_repuesto, datos, u)


@router.post("/repuestos/{id_repuesto}/salidas", response_model=MovimientoOut, status_code=201,
             tags=["Movimientos"], summary="Registrar repuesto usado en una orden (descuenta stock)")
def salida(id_repuesto: int, datos: SalidaIn, db: Session = Depends(get_db),
           u: UsuarioToken = Depends(puede_consumir)):
    return svc.registrar_salida(db, id_repuesto, datos, u)


@router.post("/repuestos/{id_repuesto}/devoluciones", response_model=MovimientoOut, status_code=201,
             tags=["Movimientos"], summary="Devolver al inventario un repuesto no utilizado")
def devolucion(id_repuesto: int, datos: DevolucionIn, db: Session = Depends(get_db),
               u: UsuarioToken = Depends(puede_consumir)):
    return svc.registrar_devolucion(db, id_repuesto, datos, u)


@router.post("/repuestos/{id_repuesto}/ajustes", response_model=MovimientoOut, status_code=201,
             tags=["Movimientos"], summary="Ajuste por conteo físico (motivo obligatorio)")
def ajuste(id_repuesto: int, datos: AjusteIn, db: Session = Depends(get_db),
           u: UsuarioToken = Depends(gestiona_inventario)):
    return svc.registrar_ajuste(db, id_repuesto, datos, u)


@router.get("/repuestos/{id_repuesto}/movimientos", response_model=list[MovimientoOut], tags=["Movimientos"],
            summary="Kardex de un repuesto")
def kardex(id_repuesto: int, db: Session = Depends(get_db), _: UsuarioToken = Depends(get_current_user)):
    svc.obtener_repuesto(db, id_repuesto)
    return svc.listar_movimientos(db, id_repuesto=id_repuesto)


@router.get("/movimientos", response_model=list[MovimientoConRepuesto], tags=["Movimientos"],
            summary="Listar movimientos (filtrar por orden o tipo)")
def movimientos(id_orden: int | None = None, tipo: TipoMov | None = None, db: Session = Depends(get_db),
                _: UsuarioToken = Depends(get_current_user)):
    return svc.listar_movimientos(db, id_orden=id_orden, tipo=tipo)


@router.get("/ordenes/{id_orden}/consumo", response_model=ConsumoOrden, tags=["Movimientos"],
            summary="Repuestos usados en una orden y su valor (lo usará ms-facturacion)")
def consumo(id_orden: int, db: Session = Depends(get_db), _: UsuarioToken = Depends(get_current_user)):
    return svc.consumo_por_orden(db, id_orden)
