"""Reglas de negocio del inventario.
Toda modificación de stock pasa por _mover(), que:
  1. bloquea la fila del repuesto (SELECT ... FOR UPDATE) para que dos técnicos
     no saquen la última unidad al mismo tiempo,
  2. valida que el stock no quede negativo,
  3. registra el movimiento (kardex) con stock anterior y resultante."""
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.clients import externos
from app.core.security import UsuarioToken
from app.models import SIGNO, MovimientoInventario, Repuesto
from app.schemas.inventario import (AjusteIn, ConsumoLinea, ConsumoOrden, DevolucionIn, EntradaIn,
                                    RepuestoCreate, RepuestoUpdate, SalidaIn)

ESTADOS_PERMITEN_SALIDA = ["EN_REPARACION"]
ESTADOS_PERMITEN_DEVOLUCION = ["EN_REPARACION", "LISTO_ENTREGA"]


# ---------- Repuestos ----------
def obtener_repuesto(db: Session, id_repuesto: int, bloquear: bool = False) -> Repuesto:
    consulta = select(Repuesto).where(Repuesto.id_repuesto == id_repuesto)
    if bloquear:
        consulta = consulta.with_for_update()
    repuesto = db.scalar(consulta)
    if repuesto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Repuesto no encontrado")
    return repuesto


def crear_repuesto(db: Session, datos: RepuestoCreate, usuario: UsuarioToken) -> Repuesto:
    if db.scalar(select(Repuesto).where(Repuesto.codigo == datos.codigo)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un repuesto con ese código")
    valores = datos.model_dump(exclude={"stock_inicial"})
    repuesto = Repuesto(**valores, stock_actual=0)
    db.add(repuesto)
    db.flush()
    if datos.stock_inicial > 0:
        _mover(db, repuesto, "ENTRADA", datos.stock_inicial, usuario.id_usuario,
               motivo="Inventario inicial", precio=datos.precio_costo)
    db.commit()
    db.refresh(repuesto)
    return repuesto


def listar_repuestos(db: Session, buscar: str | None = None, categoria: str | None = None,
                     solo_stock_bajo: bool = False, solo_activos: bool = True) -> list[Repuesto]:
    consulta = select(Repuesto).order_by(Repuesto.categoria, Repuesto.nombre)
    if solo_activos:
        consulta = consulta.where(Repuesto.activo.is_(True))
    if buscar:
        patron = f"%{buscar.strip()}%"
        consulta = consulta.where(or_(Repuesto.codigo.ilike(patron), Repuesto.nombre.ilike(patron),
                                      Repuesto.marca.ilike(patron)))
    if categoria:
        consulta = consulta.where(Repuesto.categoria == categoria.strip().upper())
    if solo_stock_bajo:
        consulta = consulta.where(Repuesto.stock_actual <= Repuesto.stock_minimo)
    return list(db.scalars(consulta).all())


def actualizar_repuesto(db: Session, id_repuesto: int, datos: RepuestoUpdate) -> Repuesto:
    repuesto = obtener_repuesto(db, id_repuesto)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        if campo == "categoria" and valor:
            valor = valor.strip().upper()
        setattr(repuesto, campo, valor)
    db.commit()
    db.refresh(repuesto)
    return repuesto


# ---------- Movimientos ----------
def _mover(db: Session, repuesto: Repuesto, tipo: str, cantidad: int, id_usuario: int,
           motivo: str | None = None, id_orden: int | None = None,
           precio: Decimal | None = None) -> MovimientoInventario:
    anterior = repuesto.stock_actual
    resultante = anterior + SIGNO[tipo] * cantidad
    if resultante < 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Stock insuficiente de {repuesto.codigo}: hay {anterior}, se piden {cantidad}")
    repuesto.stock_actual = resultante
    mov = MovimientoInventario(repuesto=repuesto, tipo=tipo, cantidad=cantidad, stock_anterior=anterior,
                               stock_resultante=resultante, precio_unitario=precio, id_orden=id_orden,
                               motivo=motivo, id_usuario=id_usuario)
    db.add(mov)
    return mov


def _validar_orden(id_orden: int, usuario: UsuarioToken, estados: list[str]) -> None:
    orden = externos.obtener_orden(id_orden, usuario.token)
    if orden is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"La orden {id_orden} no existe")
    if orden and orden.get("estado_actual") not in estados:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"La orden está en {orden.get('estado_actual')}; solo se permite en {', '.join(estados)}")


def _neto_en_orden(db: Session, id_repuesto: int, id_orden: int) -> int:
    def total(tipo: str) -> int:
        return db.scalar(select(func.coalesce(func.sum(MovimientoInventario.cantidad), 0)).where(
            MovimientoInventario.id_repuesto == id_repuesto, MovimientoInventario.id_orden == id_orden,
            MovimientoInventario.tipo == tipo)) or 0
    return total("SALIDA") - total("DEVOLUCION")


def registrar_entrada(db: Session, id_repuesto: int, datos: EntradaIn, usuario: UsuarioToken):
    repuesto = obtener_repuesto(db, id_repuesto, bloquear=True)
    if not repuesto.activo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El repuesto está inactivo")
    if datos.costo_unitario is not None:
        repuesto.precio_costo = datos.costo_unitario
    mov = _mover(db, repuesto, "ENTRADA", datos.cantidad, usuario.id_usuario, datos.motivo,
                 precio=datos.costo_unitario or repuesto.precio_costo)
    db.commit()
    db.refresh(mov)
    return mov


def registrar_salida(db: Session, id_repuesto: int, datos: SalidaIn, usuario: UsuarioToken):
    """Repuesto utilizado en una reparación: descuenta stock y guarda el precio de venta del momento."""
    _validar_orden(datos.id_orden, usuario, ESTADOS_PERMITEN_SALIDA)
    repuesto = obtener_repuesto(db, id_repuesto, bloquear=True)
    if not repuesto.activo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El repuesto está inactivo")
    mov = _mover(db, repuesto, "SALIDA", datos.cantidad, usuario.id_usuario,
                 datos.motivo or "Usado en reparación", datos.id_orden, repuesto.precio_venta)
    db.commit()
    db.refresh(mov)
    return mov


def registrar_devolucion(db: Session, id_repuesto: int, datos: DevolucionIn, usuario: UsuarioToken):
    """Devuelve al inventario un repuesto que salió para una orden y no se usó."""
    _validar_orden(datos.id_orden, usuario, ESTADOS_PERMITEN_DEVOLUCION)
    repuesto = obtener_repuesto(db, id_repuesto, bloquear=True)
    neto = _neto_en_orden(db, id_repuesto, datos.id_orden)
    if datos.cantidad > neto:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Solo se pueden devolver {neto} unidades de {repuesto.codigo} en esta orden")
    ultima_salida = db.scalar(select(MovimientoInventario).where(
        MovimientoInventario.id_repuesto == id_repuesto, MovimientoInventario.id_orden == datos.id_orden,
        MovimientoInventario.tipo == "SALIDA").order_by(MovimientoInventario.id_movimiento.desc()))
    mov = _mover(db, repuesto, "DEVOLUCION", datos.cantidad, usuario.id_usuario,
                 datos.motivo or "Devolución de repuesto no utilizado", datos.id_orden,
                 ultima_salida.precio_unitario)
    db.commit()
    db.refresh(mov)
    return mov


def registrar_ajuste(db: Session, id_repuesto: int, datos: AjusteIn, usuario: UsuarioToken):
    repuesto = obtener_repuesto(db, id_repuesto, bloquear=True)
    mov = _mover(db, repuesto, f"AJUSTE_{datos.tipo}", datos.cantidad, usuario.id_usuario, datos.motivo)
    db.commit()
    db.refresh(mov)
    return mov


def listar_movimientos(db: Session, id_repuesto: int | None = None, id_orden: int | None = None,
                       tipo: str | None = None) -> list[MovimientoInventario]:
    consulta = select(MovimientoInventario).order_by(MovimientoInventario.id_movimiento.desc())
    if id_repuesto:
        consulta = consulta.where(MovimientoInventario.id_repuesto == id_repuesto)
    if id_orden:
        consulta = consulta.where(MovimientoInventario.id_orden == id_orden)
    if tipo:
        consulta = consulta.where(MovimientoInventario.tipo == tipo)
    return list(db.scalars(consulta).all())


def consumo_por_orden(db: Session, id_orden: int) -> ConsumoOrden:
    movimientos = db.scalars(select(MovimientoInventario).where(
        MovimientoInventario.id_orden == id_orden,
        MovimientoInventario.tipo.in_(["SALIDA", "DEVOLUCION"]))).all()
    acumulado: dict[int, dict] = {}
    for m in movimientos:
        signo = 1 if m.tipo == "SALIDA" else -1
        linea = acumulado.setdefault(m.id_repuesto, {"repuesto": m.repuesto, "cantidad": 0, "valor": Decimal(0)})
        linea["cantidad"] += signo * m.cantidad
        linea["valor"] += signo * m.cantidad * (m.precio_unitario or 0)
    lineas = [
        ConsumoLinea(id_repuesto=r_id, codigo=d["repuesto"].codigo, nombre=d["repuesto"].nombre,
                     cantidad=d["cantidad"], precio_unitario=float(d["valor"] / d["cantidad"]),
                     subtotal=float(d["valor"]))
        for r_id, d in acumulado.items() if d["cantidad"] > 0
    ]
    return ConsumoOrden(id_orden=id_orden, lineas=lineas, total_materiales=sum(l.subtotal for l in lineas))
