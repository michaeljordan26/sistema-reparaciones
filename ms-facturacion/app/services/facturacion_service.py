"""Reglas de negocio de presupuestos, facturas y pagos.

Flujo del dinero:
  orden ESPERANDO_APROBACION → presupuesto (mano de obra + repuestos estimados)
  → cliente APRUEBA → orden EN_REPARACION  |  cliente RECHAZA → orden LISTO_ENTREGA (sin reparar, sin cobro)
  → reparación terminada (LISTO_ENTREGA) → factura (mano de obra presupuestada + repuestos REALMENTE usados)
  → abonos / pagos → saldo 0 → ms-ordenes permite la entrega.
"""
from datetime import date, datetime, time, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.clients import externos
from app.core.config import settings
from app.core.security import UsuarioToken
from app.core.tiempo import COLOMBIA, hoy as hoy_colombia
from app.models import DetalleFactura, DetallePresupuesto, Factura, Pago, Presupuesto, RespuestaPresupuesto
from app.schemas.facturacion import (AnularIn, CarteraLinea, CarteraOut, FacturaCreate, IngresosOut, PagoIn,
                                     PresupuestoCreate, RespuestaIn, SaldoOrden)

CENTAVO = Decimal("0.01")


def dinero(valor) -> Decimal:
    return Decimal(str(valor)).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def _totales(detalles: list) -> dict:
    materiales = sum((d.subtotal for d in detalles if d.tipo == "REPUESTO"), Decimal(0))
    mano_obra = sum((d.subtotal for d in detalles if d.tipo == "MANO_OBRA"), Decimal(0))
    subtotal = dinero(materiales + mano_obra)
    iva = dinero(subtotal * settings.IVA_PORCENTAJE / 100)
    return {"subtotal_materiales": dinero(materiales), "subtotal_mano_obra": dinero(mano_obra),
            "subtotal": subtotal, "iva_porcentaje": settings.IVA_PORCENTAJE, "iva": iva, "total": subtotal + iva}


def _orden(id_orden: int, usuario: UsuarioToken) -> dict:
    orden = externos.obtener_orden(id_orden, usuario.token)
    if orden is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"La orden {id_orden} no existe")
    return orden


def _exigir_estado(orden: dict, estado: str) -> None:
    if orden["estado_actual"] != estado:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"La orden {orden['codigo']} está en {orden['estado_actual']}; se requiere {estado}")


# ======================= PRESUPUESTOS =======================
def obtener_presupuesto(db: Session, id_presupuesto: int) -> Presupuesto:
    p = db.get(Presupuesto, id_presupuesto)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Presupuesto no encontrado")
    return p


def presupuesto_de_orden(db: Session, id_orden: int) -> Presupuesto | None:
    """El presupuesto más reciente que no esté anulado."""
    return db.scalar(select(Presupuesto).where(Presupuesto.id_orden == id_orden, Presupuesto.estado != "ANULADO")
                     .order_by(Presupuesto.id_presupuesto.desc()))


def crear_presupuesto(db: Session, datos: PresupuestoCreate, usuario: UsuarioToken) -> Presupuesto:
    orden = _orden(datos.id_orden, usuario)
    _exigir_estado(orden, "ESPERANDO_APROBACION")
    vigente = db.scalar(select(Presupuesto).where(Presupuesto.id_orden == datos.id_orden,
                                                  Presupuesto.estado.in_(["PENDIENTE", "APROBADO"])))
    if vigente:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"La orden ya tiene el presupuesto {vigente.codigo} en estado {vigente.estado}")

    detalles = [DetallePresupuesto(tipo="MANO_OBRA", descripcion=m.descripcion, cantidad=m.horas,
                                   precio_unitario=dinero(m.valor_hora), subtotal=dinero(m.horas * m.valor_hora))
                for m in datos.mano_obra]
    for r in datos.repuestos:
        rep = externos.obtener_repuesto(r.id_repuesto, usuario.token)
        if rep is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"El repuesto {r.id_repuesto} no existe")
        if not rep.get("activo", True):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"El repuesto {rep['codigo']} está inactivo")
        precio = dinero(rep["precio_venta"])
        detalles.append(DetallePresupuesto(tipo="REPUESTO", id_repuesto=r.id_repuesto,
                                           descripcion=f"{rep['codigo']} - {rep['nombre']}"[:200],
                                           cantidad=r.cantidad, precio_unitario=precio,
                                           subtotal=dinero(precio * r.cantidad)))
    hoy = hoy_colombia()
    p = Presupuesto(id_orden=datos.id_orden, fecha=hoy,
                    fecha_vencimiento=hoy + timedelta(days=settings.VALIDEZ_PRESUPUESTO_DIAS),
                    observaciones=datos.observaciones, estado="PENDIENTE", id_usuario=usuario.id_usuario,
                    detalles=detalles, **_totales(detalles))
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def responder_presupuesto(db: Session, id_presupuesto: int, datos: RespuestaIn,
                          usuario: UsuarioToken) -> Presupuesto:
    p = obtener_presupuesto(db, id_presupuesto)
    if p.estado != "PENDIENTE":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"El presupuesto ya está {p.estado}")
    if p.vencido:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"El presupuesto venció el {p.fecha_vencimiento}; anúlelo y elabore uno nuevo")
    orden = _orden(p.id_orden, usuario)
    _exigir_estado(orden, "ESPERANDO_APROBACION")

    # 1) Paso local: se confirma primero, porque ms-ordenes va a consultar este presupuesto
    p.estado = datos.decision
    db.add(RespuestaPresupuesto(presupuesto=p, id_usuario=usuario.id_usuario, **datos.model_dump()))
    db.commit()

    # 2) Paso remoto: mover la orden. Si falla, COMPENSACIÓN (se deshace el paso 1).
    if datos.decision == "APROBADO":
        nuevo, texto = "EN_REPARACION", f"Presupuesto {p.codigo} aprobado por {datos.nombre_responde}"
    else:
        nuevo, texto = "LISTO_ENTREGA", f"Presupuesto {p.codigo} rechazado: se devuelve sin reparar"
    try:
        externos.cambiar_estado_orden(p.id_orden, nuevo, texto, usuario.token)
    except HTTPException:
        db.delete(p.respuesta)
        p.estado = "PENDIENTE"
        db.commit()
        raise
    db.refresh(p)
    return p


def anular_presupuesto(db: Session, id_presupuesto: int, datos: AnularIn) -> Presupuesto:
    p = obtener_presupuesto(db, id_presupuesto)
    if p.estado != "PENDIENTE":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Solo se anulan presupuestos PENDIENTES")
    p.estado = "ANULADO"
    p.observaciones = f"{p.observaciones or ''} [ANULADO: {datos.motivo}]".strip()[:500]
    db.commit()
    db.refresh(p)
    return p


# ======================= FACTURAS =======================
def obtener_factura(db: Session, id_factura: int, bloquear: bool = False) -> Factura:
    consulta = select(Factura).where(Factura.id_factura == id_factura)
    if bloquear:
        consulta = consulta.with_for_update()
    f = db.scalar(consulta)
    if f is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Factura no encontrada")
    return f


def factura_de_orden(db: Session, id_orden: int) -> Factura | None:
    return db.scalar(select(Factura).where(Factura.id_orden == id_orden, Factura.anulada.is_(False)))


def generar_factura(db: Session, datos: FacturaCreate, usuario: UsuarioToken) -> Factura:
    if factura_de_orden(db, datos.id_orden):
        raise HTTPException(status.HTTP_409_CONFLICT, "La orden ya tiene una factura activa")
    orden = _orden(datos.id_orden, usuario)
    _exigir_estado(orden, "LISTO_ENTREGA")
    p = presupuesto_de_orden(db, datos.id_orden)
    if p is None or p.estado != "APROBADO":
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "La orden no tiene presupuesto aprobado (si fue rechazado, no se factura)")

    # Mano de obra: la presupuestada. Materiales: lo REALMENTE usado según ms-inventario.
    detalles = [DetalleFactura(tipo="MANO_OBRA", descripcion=d.descripcion, cantidad=d.cantidad,
                               precio_unitario=d.precio_unitario, subtotal=d.subtotal)
                for d in p.detalles if d.tipo == "MANO_OBRA"]
    consumo = externos.consumo_orden(datos.id_orden, usuario.token)
    for linea in consumo["lineas"]:
        precio = dinero(linea["precio_unitario"])
        detalles.append(DetalleFactura(tipo="REPUESTO", id_repuesto=linea["id_repuesto"],
                                       descripcion=f"{linea['codigo']} - {linea['nombre']}"[:200],
                                       cantidad=linea["cantidad"], precio_unitario=precio,
                                       subtotal=dinero(precio * linea["cantidad"])))
    f = Factura(id_orden=datos.id_orden, id_presupuesto=p.id_presupuesto, id_usuario=usuario.id_usuario,
                detalles=detalles, **_totales(detalles))
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def anular_factura(db: Session, id_factura: int, datos: AnularIn) -> Factura:
    f = obtener_factura(db, id_factura)
    if f.anulada:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La factura ya está anulada")
    if f.total_pagado > 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se puede anular una factura con pagos; anule los pagos primero")
    f.anulada = True
    f.motivo_anulacion = datos.motivo
    db.commit()
    db.refresh(f)
    return f


def listar_facturas(db: Session, estado: str | None = None, id_orden: int | None = None) -> list[Factura]:
    consulta = select(Factura).order_by(Factura.id_factura.desc())
    if id_orden:
        consulta = consulta.where(Factura.id_orden == id_orden)
    facturas = list(db.scalars(consulta).all())
    return [f for f in facturas if f.estado == estado] if estado else facturas


# ======================= PAGOS =======================
def registrar_pago(db: Session, id_factura: int, datos: PagoIn, usuario: UsuarioToken) -> Pago:
    f = obtener_factura(db, id_factura, bloquear=True)   # evita dos pagos simultáneos que excedan el saldo
    if f.anulada:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La factura está anulada")
    saldo = f.saldo
    if saldo <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"La factura {f.numero} ya está pagada")
    monto = dinero(datos.monto)
    if monto > saldo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"El pago (${monto:,.0f}) supera el saldo pendiente (${saldo:,.0f})")
    pago = Pago(factura=f, monto=monto, metodo=datos.metodo,
                referencia=datos.referencia.strip() if datos.referencia else None,
                tipo="PAGO_TOTAL" if monto == saldo else "ABONO",
                saldo_anterior=saldo, saldo_resultante=saldo - monto, id_usuario=usuario.id_usuario)
    db.add(pago)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(pago)
    return pago


def anular_pago(db: Session, id_pago: int, datos: AnularIn) -> Pago:
    pago = db.get(Pago, id_pago)
    if pago is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pago no encontrado")
    if pago.anulado:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El pago ya está anulado")
    pago.anulado = True
    pago.motivo_anulacion = datos.motivo
    db.commit()
    db.refresh(pago)
    return pago


# ======================= SALDOS Y REPORTES =======================
def saldo_de_orden(db: Session, id_orden: int) -> SaldoOrden:
    f = factura_de_orden(db, id_orden)
    if f:
        return SaldoOrden(id_orden=id_orden, saldo_pendiente=float(f.saldo),
                          detalle=f"Factura {f.numero}: {f.estado}")
    p = presupuesto_de_orden(db, id_orden)
    if p and p.estado == "APROBADO":
        return SaldoOrden(id_orden=id_orden, saldo_pendiente=float(p.total),
                          detalle=f"Presupuesto {p.codigo} aprobado y aún sin facturar")
    return SaldoOrden(id_orden=id_orden, saldo_pendiente=0, detalle="Sin cobros pendientes")


def ingresos(db: Session, desde: date | None, hasta: date | None) -> IngresosOut:
    hasta = hasta or hoy_colombia()
    desde = desde or hasta - timedelta(days=30)
    if desde > hasta:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "'desde' no puede ser posterior a 'hasta'")
    # Los límites se pasan a UTC: así la comparación es correcta en cualquier base de datos
    inicio = datetime.combine(desde, time.min, tzinfo=COLOMBIA).astimezone(timezone.utc)
    fin = datetime.combine(hasta + timedelta(days=1), time.min, tzinfo=COLOMBIA).astimezone(timezone.utc)
    pagos = db.scalars(select(Pago).where(Pago.anulado.is_(False), Pago.fecha >= inicio, Pago.fecha < fin)).all()
    por_metodo: dict[str, float] = {}
    for p in pagos:
        por_metodo[p.metodo] = por_metodo.get(p.metodo, 0) + float(p.monto)
    return IngresosOut(desde=desde, hasta=hasta, total=sum(por_metodo.values()), cantidad_pagos=len(pagos),
                       por_metodo=por_metodo)


def cartera(db: Session) -> CarteraOut:
    facturas = [f for f in listar_facturas(db) if not f.anulada and f.saldo > 0]
    lineas = [CarteraLinea(id_factura=f.id_factura, numero=f.numero, id_orden=f.id_orden, total=float(f.total),
                           total_pagado=float(f.total_pagado), saldo=float(f.saldo), estado=f.estado)
              for f in facturas]
    return CarteraOut(facturas=lineas, total_por_cobrar=sum(l.saldo for l in lineas))
