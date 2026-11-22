"""Reglas de negocio de diagnósticos, reparaciones y garantías.

Este servicio coordina operaciones que tocan VARIOS microservicios. Como no existe una
transacción que abarque varias bases de datos, se usa el patrón SAGA simplificado:
  - primero se valida todo,
  - se ejecuta el paso remoto,
  - si el paso local falla después, se ejecuta una COMPENSACIÓN (deshacer el paso remoto).
"""
import logging
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.clients import externos
from app.core.config import settings
from app.core.security import UsuarioToken
from app.core.tiempo import hoy as hoy_colombia
from app.models import Diagnostico, Garantia, ReclamacionGarantia, Reparacion, RepuestoUtilizado
from app.schemas.reparacion import (AnularGarantia, DiagnosticoCreate, FinalizarReparacion, ReclamacionCreate,
                                    ReclamacionResolver, ReparacionCreate, RepuestoUsoIn)

log = logging.getLogger("ms-reparaciones")


# ---------- Utilidades ----------
def _orden(id_orden: int, usuario: UsuarioToken) -> dict:
    orden = externos.obtener_orden(id_orden, usuario.token)
    if orden is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"La orden {id_orden} no existe")
    return orden


def _exigir_estado(orden: dict, estado: str) -> None:
    if orden["estado_actual"] != estado:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"La orden {orden['codigo']} está en {orden['estado_actual']}; se requiere {estado}")


def _tecnico_de_la_orden(orden: dict, usuario: UsuarioToken) -> tuple[int, int]:
    """Devuelve (id_tecnico, id_usuario_tecnico). Un técnico solo trabaja SUS órdenes; el admin, cualquiera."""
    asignacion = orden.get("asignacion_activa")
    if asignacion is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La orden no tiene técnico asignado")
    if usuario.tiene_rol("ADMINISTRADOR"):
        return asignacion["id_tecnico"], usuario.id_usuario
    yo = externos.validar_usuario(usuario.token)
    if yo.get("id_tecnico") != asignacion["id_tecnico"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Esta orden no está asignada a usted")
    return asignacion["id_tecnico"], usuario.id_usuario


def _guardar(db: Session):
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise


# ---------- CU Diagnóstico ----------
def obtener_diagnostico_por_orden(db: Session, id_orden: int) -> Diagnostico | None:
    return db.scalar(select(Diagnostico).where(Diagnostico.id_orden == id_orden))


def registrar_diagnostico(db: Session, datos: DiagnosticoCreate, usuario: UsuarioToken) -> Diagnostico:
    if obtener_diagnostico_por_orden(db, datos.id_orden):
        raise HTTPException(status.HTTP_409_CONFLICT, "La orden ya tiene un diagnóstico registrado")
    orden = _orden(datos.id_orden, usuario)
    _exigir_estado(orden, "EN_DIAGNOSTICO")
    id_tecnico, id_usuario_tec = _tecnico_de_la_orden(orden, usuario)

    diag = Diagnostico(**datos.model_dump(), id_tecnico=id_tecnico, id_usuario_tecnico=id_usuario_tec)
    db.add(diag)
    db.flush()  # valida restricciones locales ANTES de tocar otro servicio
    try:
        externos.cambiar_estado_orden(datos.id_orden, "ESPERANDO_APROBACION",
                                      f"Diagnóstico: {datos.causa_probable}", usuario.token)
    except HTTPException:
        db.rollback()  # el paso remoto falló: no se guarda el diagnóstico
        raise
    _guardar(db)
    db.refresh(diag)
    return diag


# ---------- CU Reparación ----------
def obtener_reparacion(db: Session, id_reparacion: int) -> Reparacion:
    rep = db.get(Reparacion, id_reparacion)
    if rep is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reparación no encontrada")
    return rep


def obtener_reparacion_por_orden(db: Session, id_orden: int) -> Reparacion | None:
    return db.scalar(select(Reparacion).where(Reparacion.id_orden == id_orden))


def iniciar_reparacion(db: Session, datos: ReparacionCreate, usuario: UsuarioToken) -> Reparacion:
    if obtener_reparacion_por_orden(db, datos.id_orden):
        raise HTTPException(status.HTTP_409_CONFLICT, "La orden ya tiene una reparación registrada")
    diag = obtener_diagnostico_por_orden(db, datos.id_orden)
    if diag is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se puede reparar sin un diagnóstico registrado")
    orden = _orden(datos.id_orden, usuario)
    _exigir_estado(orden, "EN_REPARACION")   # el presupuesto ya fue aprobado
    id_tecnico, id_usuario_tec = _tecnico_de_la_orden(orden, usuario)
    rep = Reparacion(id_orden=datos.id_orden, id_diagnostico=diag.id_diagnostico, id_tecnico=id_tecnico,
                     id_usuario_tecnico=id_usuario_tec, actividades_realizadas=datos.actividades_realizadas)
    db.add(rep)
    _guardar(db)
    db.refresh(rep)
    return rep


def _reparacion_editable(db: Session, id_reparacion: int, usuario: UsuarioToken) -> tuple[Reparacion, dict]:
    rep = obtener_reparacion(db, id_reparacion)
    if rep.estado != "EN_PROCESO":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La reparación ya está finalizada")
    orden = _orden(rep.id_orden, usuario)
    _exigir_estado(orden, "EN_REPARACION")
    _tecnico_de_la_orden(orden, usuario)
    return rep, orden


def agregar_repuesto(db: Session, id_reparacion: int, datos: RepuestoUsoIn, usuario: UsuarioToken) -> Reparacion:
    rep, orden = _reparacion_editable(db, id_reparacion, usuario)
    # Paso remoto: ms-inventario descuenta el stock (y valida que alcance)
    mov = externos.sacar_repuesto(datos.id_repuesto, datos.cantidad, rep.id_orden,
                                  f"Reparación {orden['codigo']}", usuario.token)
    repuesto = externos.obtener_repuesto(datos.id_repuesto, usuario.token) or {}
    try:
        rep.repuestos.append(RepuestoUtilizado(
            id_repuesto=datos.id_repuesto, id_movimiento=mov["id_movimiento"],
            codigo=repuesto.get("codigo", f"#{datos.id_repuesto}"), nombre=repuesto.get("nombre", "Repuesto"),
            cantidad=datos.cantidad, precio_unitario=mov["precio_unitario"] or 0))
        _guardar(db)
    except SQLAlchemyError:
        # COMPENSACIÓN: el stock ya se descontó en ms-inventario; se devuelve
        log.error("Fallo al guardar el repuesto utilizado; se compensa con una devolución")
        externos.devolver_repuesto(datos.id_repuesto, datos.cantidad, rep.id_orden,
                                   "Compensación automática por error", usuario.token)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "No se pudo registrar el repuesto; el stock fue devuelto")
    db.refresh(rep)
    return rep


def quitar_repuesto(db: Session, id_reparacion: int, id_ru: int, usuario: UsuarioToken) -> Reparacion:
    rep, orden = _reparacion_editable(db, id_reparacion, usuario)
    ru = next((r for r in rep.repuestos if r.id_repuesto_utilizado == id_ru), None)
    if ru is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ese repuesto no está registrado en la reparación")
    externos.devolver_repuesto(ru.id_repuesto, ru.cantidad, rep.id_orden,
                               f"Retirado de la reparación {orden['codigo']}", usuario.token)
    rep.repuestos.remove(ru)
    _guardar(db)
    db.refresh(rep)
    return rep


def finalizar_reparacion(db: Session, id_reparacion: int, datos: FinalizarReparacion,
                         usuario: UsuarioToken) -> Reparacion:
    rep, orden = _reparacion_editable(db, id_reparacion, usuario)
    dias = settings.GARANTIA_DIAS_DEFECTO if datos.garantia_dias is None else datos.garantia_dias
    if datos.resultado == "NO_REPARABLE":
        dias = 0   # no hay garantía sobre algo que no se reparó

    # Paso remoto primero: si ms-ordenes rechaza el cambio, no se modifica nada aquí
    externos.cambiar_estado_orden(rep.id_orden, "LISTO_ENTREGA",
                                  f"Reparación {datos.resultado.lower()}", usuario.token)

    ahora = datetime.now(timezone.utc)
    rep.estado = "FINALIZADA"
    rep.fecha_fin = ahora
    rep.resultado = datos.resultado
    rep.actividades_realizadas = datos.actividades_realizadas
    rep.observaciones = datos.observaciones
    if dias > 0:
        hoy = hoy_colombia()
        cobertura = datos.cobertura_garantia or f"Mano de obra y repuestos instalados. {rep.diagnostico.solucion_propuesta}"
        rep.garantia = Garantia(
            id_orden=rep.id_orden, id_equipo=orden["id_equipo"], id_cliente=orden["id_cliente"],
            fecha_inicio=hoy, fecha_fin=hoy + timedelta(days=dias), dias=dias, cobertura=cobertura[:500],
            condiciones="No cubre golpes, humedad, sobrecargas eléctricas ni manipulación por terceros.")
    _guardar(db)
    db.refresh(rep)
    return rep


# ---------- CU Garantías ----------
def obtener_garantia(db: Session, id_garantia: int) -> Garantia:
    g = db.get(Garantia, id_garantia)
    if g is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Garantía no encontrada")
    return g


def listar_garantias(db: Session, estado: str | None = None, id_cliente: int | None = None,
                     id_equipo: int | None = None) -> list[Garantia]:
    consulta = select(Garantia).order_by(Garantia.id_garantia.desc())
    if id_cliente:
        consulta = consulta.where(Garantia.id_cliente == id_cliente)
    if id_equipo:
        consulta = consulta.where(Garantia.id_equipo == id_equipo)
    hoy = hoy_colombia()
    if estado == "VIGENTE":
        consulta = consulta.where(Garantia.anulada.is_(False), Garantia.fecha_fin >= hoy)
    elif estado == "VENCIDA":
        consulta = consulta.where(Garantia.anulada.is_(False), Garantia.fecha_fin < hoy)
    elif estado == "ANULADA":
        consulta = consulta.where(Garantia.anulada.is_(True))
    return list(db.scalars(consulta).all())


def anular_garantia(db: Session, id_garantia: int, datos: AnularGarantia) -> Garantia:
    g = obtener_garantia(db, id_garantia)
    if g.anulada:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La garantía ya está anulada")
    g.anulada = True
    g.motivo_anulacion = datos.motivo
    _guardar(db)
    db.refresh(g)
    return g


def crear_reclamacion(db: Session, id_garantia: int, datos: ReclamacionCreate,
                      usuario: UsuarioToken) -> ReclamacionGarantia:
    g = obtener_garantia(db, id_garantia)
    if g.estado != "VIGENTE":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"La garantía está {g.estado}; no se puede reclamar")
    if any(r.estado == "ABIERTA" for r in g.reclamaciones):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya hay una reclamación abierta para esta garantía")
    rec = ReclamacionGarantia(id_garantia=id_garantia, descripcion=datos.descripcion,
                              id_usuario_registro=usuario.id_usuario)
    db.add(rec)
    _guardar(db)
    db.refresh(rec)
    return rec


def resolver_reclamacion(db: Session, id_reclamacion: int, datos: ReclamacionResolver,
                         usuario: UsuarioToken) -> ReclamacionGarantia:
    rec = db.get(ReclamacionGarantia, id_reclamacion)
    if rec is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reclamación no encontrada")
    if rec.estado != "ABIERTA":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La reclamación ya fue resuelta")
    rec.estado = datos.estado
    rec.respuesta = datos.respuesta
    rec.fecha_respuesta = datetime.now(timezone.utc)
    rec.id_usuario_respuesta = usuario.id_usuario
    _guardar(db)
    db.refresh(rec)
    return rec
