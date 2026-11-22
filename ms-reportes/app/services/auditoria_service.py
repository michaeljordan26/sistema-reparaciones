"""Registro y consulta de la auditoría."""
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import RegistroAuditoria
from app.schemas.reportes import EventoIn

from app.core.tiempo import COLOMBIA

# Descripción legible de las operaciones más importantes: (servicio, método, ruta) -> texto
ACCIONES = {
    ("ms-usuarios", "POST", "/auth/login"): "Inicio de sesión",
    ("ms-usuarios", "POST", "/usuarios"): "Crear usuario",
    ("ms-usuarios", "PUT", "/usuarios/{id_usuario}"): "Actualizar usuario",
    ("ms-usuarios", "PATCH", "/usuarios/{id_usuario}/desactivar"): "Desactivar usuario",
    ("ms-usuarios", "PUT", "/usuarios/{id_usuario}/roles"): "Cambiar roles de usuario",
    ("ms-usuarios", "POST", "/tecnicos"): "Registrar técnico",
    ("ms-usuarios", "PUT", "/tecnicos/{id_tecnico}"): "Actualizar técnico",
    ("ms-clientes", "POST", "/clientes"): "Registrar cliente",
    ("ms-clientes", "PUT", "/clientes/{id_cliente}"): "Actualizar cliente",
    ("ms-clientes", "PATCH", "/clientes/{id_cliente}/desactivar"): "Desactivar cliente",
    ("ms-clientes", "POST", "/equipos"): "Registrar equipo",
    ("ms-clientes", "PUT", "/equipos/{id_equipo}"): "Actualizar equipo",
    ("ms-ordenes", "POST", "/ordenes"): "Crear orden de trabajo",
    ("ms-ordenes", "POST", "/ordenes/{id_orden}/asignar"): "Asignar técnico a orden",
    ("ms-ordenes", "PATCH", "/ordenes/{id_orden}/estado"): "Cambiar estado de orden",
    ("ms-reparaciones", "POST", "/diagnosticos"): "Registrar diagnóstico",
    ("ms-reparaciones", "POST", "/reparaciones"): "Iniciar reparación",
    ("ms-reparaciones", "POST", "/reparaciones/{id_reparacion}/repuestos"): "Usar repuesto en reparación",
    ("ms-reparaciones", "DELETE", "/reparaciones/{id_reparacion}/repuestos/{id_repuesto_utilizado}"): "Quitar repuesto de reparación",
    ("ms-reparaciones", "POST", "/reparaciones/{id_reparacion}/finalizar"): "Finalizar reparación",
    ("ms-reparaciones", "PATCH", "/garantias/{id_garantia}/anular"): "Anular garantía",
    ("ms-reparaciones", "POST", "/garantias/{id_garantia}/reclamaciones"): "Registrar reclamación de garantía",
    ("ms-reparaciones", "PATCH", "/reclamaciones/{id_reclamacion}"): "Resolver reclamación",
    ("ms-inventario", "POST", "/repuestos"): "Registrar repuesto",
    ("ms-inventario", "PUT", "/repuestos/{id_repuesto}"): "Actualizar repuesto",
    ("ms-inventario", "POST", "/repuestos/{id_repuesto}/entradas"): "Entrada de inventario",
    ("ms-inventario", "POST", "/repuestos/{id_repuesto}/salidas"): "Salida de inventario",
    ("ms-inventario", "POST", "/repuestos/{id_repuesto}/devoluciones"): "Devolución al inventario",
    ("ms-inventario", "POST", "/repuestos/{id_repuesto}/ajustes"): "Ajuste de inventario",
    ("ms-facturacion", "POST", "/presupuestos"): "Crear presupuesto",
    ("ms-facturacion", "POST", "/presupuestos/{id_presupuesto}/respuesta"): "Respuesta del cliente al presupuesto",
    ("ms-facturacion", "PATCH", "/presupuestos/{id_presupuesto}/anular"): "Anular presupuesto",
    ("ms-facturacion", "POST", "/facturas"): "Generar factura",
    ("ms-facturacion", "PATCH", "/facturas/{id_factura}/anular"): "Anular factura",
    ("ms-facturacion", "POST", "/facturas/{id_factura}/pagos"): "Registrar pago",
    ("ms-facturacion", "PATCH", "/pagos/{id_pago}/anular"): "Anular pago",
}


def describir(e: EventoIn) -> str:
    base = ACCIONES.get((e.servicio, e.metodo, e.ruta_plantilla), f"{e.metodo} {e.ruta_plantilla}")
    if e.codigo_estado in (401, 403):
        return f"{base} (acceso denegado)"[:120]
    if e.codigo_estado >= 400:
        return f"{base} (rechazado)"[:120]
    return base[:120]


def registrar(db: Session, e: EventoIn) -> RegistroAuditoria:
    r = RegistroAuditoria(servicio=e.servicio, metodo=e.metodo, ruta=e.ruta, ruta_plantilla=e.ruta_plantilla,
                          accion=describir(e), recurso_id=e.recurso_id, codigo_estado=e.codigo_estado,
                          exito=e.codigo_estado < 400, id_usuario=e.id_usuario,
                          roles=",".join(e.roles)[:120] or None, ip=e.ip, duracion_ms=e.duracion_ms)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def _filtros(consulta, servicio, id_usuario, metodo, solo_fallidos, desde: date | None, hasta: date | None):
    if servicio:
        consulta = consulta.where(RegistroAuditoria.servicio == servicio)
    if id_usuario is not None:
        consulta = consulta.where(RegistroAuditoria.id_usuario == id_usuario)
    if metodo:
        consulta = consulta.where(RegistroAuditoria.metodo == metodo)
    if solo_fallidos:
        consulta = consulta.where(RegistroAuditoria.exito.is_(False))
    if desde:
        consulta = consulta.where(RegistroAuditoria.fecha >= datetime.combine(desde, time.min, tzinfo=COLOMBIA).astimezone(timezone.utc))
    if hasta:
        consulta = consulta.where(RegistroAuditoria.fecha < datetime.combine(hasta + timedelta(days=1), time.min,
                                                                            tzinfo=COLOMBIA).astimezone(timezone.utc))
    return consulta


def listar(db: Session, servicio=None, id_usuario=None, metodo=None, solo_fallidos=False, desde=None, hasta=None,
           limite: int = 100, desplazamiento: int = 0) -> dict:
    base = _filtros(select(RegistroAuditoria), servicio, id_usuario, metodo, solo_fallidos, desde, hasta)
    total = db.scalar(select(func.count()).select_from(base.subquery()))
    registros = db.scalars(base.order_by(RegistroAuditoria.id_registro.desc()).limit(limite)
                           .offset(desplazamiento)).all()
    return {"total": total, "limite": limite, "desplazamiento": desplazamiento, "registros": registros}


def resumen(db: Session, horas: int = 24) -> dict:
    desde = datetime.now(timezone.utc) - timedelta(hours=horas)
    filas = db.execute(select(RegistroAuditoria.servicio, RegistroAuditoria.exito, func.count())
                       .where(RegistroAuditoria.fecha >= desde)
                       .group_by(RegistroAuditoria.servicio, RegistroAuditoria.exito)).all()
    por_servicio: dict[str, dict] = {}
    for servicio, exito, n in filas:
        d = por_servicio.setdefault(servicio, {"exitosas": 0, "rechazadas": 0})
        d["exitosas" if exito else "rechazadas"] += n
    denegados = db.scalar(select(func.count()).where(RegistroAuditoria.fecha >= desde,
                                                     RegistroAuditoria.codigo_estado.in_([401, 403])))
    logins_fallidos = db.scalar(select(func.count()).where(
        RegistroAuditoria.fecha >= desde, RegistroAuditoria.ruta_plantilla == "/auth/login",
        RegistroAuditoria.exito.is_(False)))
    total = sum(d["exitosas"] + d["rechazadas"] for d in por_servicio.values())
    return {"horas": horas, "total_operaciones": total, "accesos_denegados": denegados,
            "inicios_sesion_fallidos": logins_fallidos, "por_servicio": por_servicio}
