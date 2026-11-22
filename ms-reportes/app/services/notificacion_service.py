"""Notificaciones al cliente cuando su orden cambia de estado.
Se disparan solas a partir de los eventos de auditoría de ms-ordenes.
El ENVÍO ES SIMULADO: se registra el mensaje como enviado (no se usan servicios de pago)."""
import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.clients import externos
from app.core.security import token_sistema
from app.database.session import SessionLocal
from app.models import Notificacion
from app.schemas.reportes import EventoIn

log = logging.getLogger("notificaciones")

# Se puede reemplazar en las pruebas
fabrica_sesiones = SessionLocal

NOMBRE_EQUIPO = {"PORTATIL": "portátil", "ESCRITORIO": "computador de escritorio", "TODO_EN_UNO": "computador todo en uno",
                 "IMPRESORA": "impresora", "TABLET": "tablet", "SERVIDOR": "servidor", "OTRO": "equipo"}

PLANTILLAS = {
    "RECIBIDO": ("Recibimos su equipo - {codigo}",
                 "Hola {nombre}, recibimos su {equipo} con la orden {codigo}. "
                 "Le avisaremos cuando tengamos el diagnóstico."),
    "ESPERANDO_APROBACION": ("Diagnóstico listo - {codigo}",
                             "Hola {nombre}, ya revisamos su {equipo} (orden {codigo}). "
                             "Tenemos un presupuesto listo: por favor indíquenos si lo aprueba."),
    "EN_REPARACION": ("Su equipo está en reparación - {codigo}",
                      "Hola {nombre}, gracias por aprobar el presupuesto. Su {equipo} ya está en reparación."),
    "LISTO_ENTREGA": ("Su equipo está listo - {codigo}",
                      "Hola {nombre}, su {equipo} (orden {codigo}) está listo para recoger en el taller."),
    "ENTREGADO": ("Equipo entregado - {codigo}",
                  "Hola {nombre}, su {equipo} fue entregado. Gracias por confiar en nosotros. "
                  "Recuerde que la reparación tiene garantía."),
    "CANCELADO": ("Orden cancelada - {codigo}",
                  "Hola {nombre}, la orden {codigo} de su {equipo} fue cancelada. Comuníquese con nosotros si tiene dudas."),
}


def debe_notificar(e: EventoIn) -> bool:
    if e.servicio != "ms-ordenes" or e.codigo_estado >= 300 or not e.recurso_id:
        return False
    return (e.metodo == "POST" and e.ruta_plantilla == "/ordenes") or \
           (e.metodo == "PATCH" and e.ruta_plantilla == "/ordenes/{id_orden}/estado")


def generar(db: Session, id_orden: int, forzar: bool = False) -> Notificacion | None:
    """Crea (o con forzar=True, reenvía) la notificación del estado ACTUAL de la orden."""
    token = token_sistema()
    try:
        orden = externos.orden(id_orden, token)
    except externos.ServicioNoDisponible as e:
        log.warning("No se pudo notificar la orden %s: %s", id_orden, e)
        return None
    if orden is None or orden["estado_actual"] not in PLANTILLAS:
        return None
    tipo = orden["estado_actual"]
    existente = db.scalar(select(Notificacion).where(Notificacion.id_orden == id_orden, Notificacion.tipo == tipo))
    if existente and not forzar:
        return existente

    asunto_t, mensaje_t = PLANTILLAS[tipo]
    datos = {"codigo": orden["codigo"], "nombre": "cliente", "equipo": "equipo"}
    canal, destinatario, estado, error, id_cliente = "SMS", None, "ENVIADA", None, orden.get("id_cliente")
    try:
        eq = externos.equipo(orden["id_equipo"], token)
        if eq:
            cli = eq["cliente"]
            datos["nombre"] = cli["nombres"].split()[0]
            datos["equipo"] = f"{NOMBRE_EQUIPO.get(eq['tipo_equipo'], 'equipo')} {eq['marca']} {eq['modelo']}"
            canal, destinatario = ("CORREO", cli["correo"]) if cli.get("correo") else ("SMS", cli["telefono"])
    except externos.ServicioNoDisponible as e:
        estado, error = "FALLIDA", str(e)[:300]

    n = existente or Notificacion(id_orden=id_orden, tipo=tipo)
    n.id_cliente, n.canal, n.destinatario, n.estado, n.detalle_error = id_cliente, canal, destinatario, estado, error
    n.asunto, n.mensaje = asunto_t.format(**datos)[:150], mensaje_t.format(**datos)
    if existente:
        n.fecha = func.now()
    db.add(n)
    db.commit()
    db.refresh(n)
    log.info("[SIMULADO] %s a %s: %s", canal, destinatario, n.asunto)
    return n


def generar_en_segundo_plano(id_orden: int) -> None:
    db = fabrica_sesiones()
    try:
        generar(db, id_orden)
    except Exception:   # una notificación nunca debe tumbar el servicio
        log.exception("Error generando la notificación de la orden %s", id_orden)
        db.rollback()
    finally:
        db.close()


def listar(db: Session, id_orden: int | None = None, id_cliente: int | None = None,
           estado: str | None = None) -> list[Notificacion]:
    consulta = select(Notificacion).order_by(Notificacion.id_notificacion.desc())
    if id_orden:
        consulta = consulta.where(Notificacion.id_orden == id_orden)
    if id_cliente:
        consulta = consulta.where(Notificacion.id_cliente == id_cliente)
    if estado:
        consulta = consulta.where(Notificacion.estado == estado)
    return list(db.scalars(consulta).all())
