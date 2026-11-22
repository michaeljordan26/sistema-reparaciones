"""Reglas de negocio de las órdenes de trabajo."""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients import externos
from app.core import estados as E
from app.core.security import UsuarioToken
from app.models import Asignacion, HistorialEstado, OrdenTrabajo
from app.schemas.orden import AsignarTecnico, CambioEstado, OrdenCreate


def _registrar_historial(db: Session, orden: OrdenTrabajo, anterior: str | None, nuevo: str,
                         usuario_id: int, observacion: str | None) -> None:
    db.add(HistorialEstado(orden=orden, estado_anterior=anterior, estado_nuevo=nuevo,
                           id_usuario=usuario_id, observacion=observacion))


def obtener_orden(db: Session, id_orden: int) -> OrdenTrabajo:
    orden = db.get(OrdenTrabajo, id_orden)
    if orden is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Orden no encontrada")
    return orden


# ---------- CU12 Crear orden ----------
def crear_orden(db: Session, datos: OrdenCreate, usuario: UsuarioToken) -> OrdenTrabajo:
    equipo = externos.obtener_equipo(datos.id_equipo, usuario.token)
    if equipo is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El equipo no existe en el servicio de clientes")
    if equipo.get("estado") != "ACTIVO" or equipo.get("cliente", {}).get("estado") != "ACTIVO":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El equipo o su cliente están inactivos")

    abierta = db.scalar(select(OrdenTrabajo).where(OrdenTrabajo.id_equipo == datos.id_equipo,
                                                   OrdenTrabajo.estado_actual.in_(E.PENDIENTES)))
    if abierta:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"El equipo ya tiene una orden abierta ({abierta.codigo})")

    orden = OrdenTrabajo(**datos.model_dump(), id_cliente=equipo["id_cliente"],
                         estado_actual=E.RECIBIDO, id_usuario_recepcion=usuario.id_usuario)
    db.add(orden)
    _registrar_historial(db, orden, None, E.RECIBIDO, usuario.id_usuario, "Equipo recibido en el taller")
    db.commit()
    db.refresh(orden)
    return orden


# ---------- CU13 / CU17 Consultar ----------
def listar_ordenes(db: Session, grupo: str | None = None, estado: str | None = None,
                   id_equipo: int | None = None, id_cliente: int | None = None,
                   id_tecnico: int | None = None, id_usuario_tecnico: int | None = None) -> list[OrdenTrabajo]:
    consulta = select(OrdenTrabajo).order_by(OrdenTrabajo.id_orden.desc())
    if grupo == "pendientes":
        consulta = consulta.where(OrdenTrabajo.estado_actual.in_(E.PENDIENTES))
    elif grupo == "finalizadas":
        consulta = consulta.where(OrdenTrabajo.estado_actual.in_(E.FINALIZADOS))
    if estado:
        consulta = consulta.where(OrdenTrabajo.estado_actual == estado)
    if id_equipo:
        consulta = consulta.where(OrdenTrabajo.id_equipo == id_equipo)
    if id_cliente:
        consulta = consulta.where(OrdenTrabajo.id_cliente == id_cliente)
    if id_tecnico or id_usuario_tecnico:
        consulta = consulta.join(Asignacion).where(Asignacion.estado_asignacion == "ACTIVA")
        if id_tecnico:
            consulta = consulta.where(Asignacion.id_tecnico == id_tecnico)
        if id_usuario_tecnico:
            consulta = consulta.where(Asignacion.id_usuario_tecnico == id_usuario_tecnico)
    return list(db.scalars(consulta).all())


# ---------- CU14 Asignar técnico ----------
def asignar_tecnico(db: Session, id_orden: int, datos: AsignarTecnico, usuario: UsuarioToken) -> OrdenTrabajo:
    orden = obtener_orden(db, id_orden)
    if orden.estado_actual in E.FINALIZADOS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se puede asignar técnico a una orden finalizada")

    tecnico = externos.obtener_tecnico(datos.id_tecnico, usuario.token)
    if tecnico is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El técnico no existe en el servicio de usuarios")
    if tecnico["estado_laboral"] != "ACTIVO" or not tecnico["usuario"]["activo"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El técnico no está disponible (inactivo o en vacaciones)")

    actual = orden.asignacion_activa
    if actual and actual.id_tecnico == datos.id_tecnico:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ese técnico ya está asignado a la orden")
    if actual:  # Reasignación: se cierra la anterior, no se borra (trazabilidad)
        actual.estado_asignacion = "REASIGNADA"
        actual.fecha_finalizacion = datetime.now(timezone.utc)
        db.flush()

    nombre = f'{tecnico["usuario"]["nombres"]} {tecnico["usuario"]["apellidos"]}'
    orden.asignaciones.append(Asignacion(id_tecnico=datos.id_tecnico, id_usuario_tecnico=tecnico["id_usuario"],
                                         nombre_tecnico=nombre, estado_asignacion="ACTIVA"))
    texto = f"Técnico asignado: {nombre}" + (f". {datos.observacion}" if datos.observacion else "")
    _registrar_historial(db, orden, orden.estado_actual, orden.estado_actual, usuario.id_usuario, texto)
    db.commit()
    db.refresh(orden)
    return orden


# ---------- CU15 Actualizar estado ----------
def cambiar_estado(db: Session, id_orden: int, datos: CambioEstado, usuario: UsuarioToken) -> OrdenTrabajo:
    orden = obtener_orden(db, id_orden)
    actual, nuevo = orden.estado_actual, datos.estado

    if nuevo not in E.TRANSICIONES[actual]:
        permitidos = ", ".join(E.TRANSICIONES[actual]) or "ninguno (estado final)"
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"No se puede pasar de {actual} a {nuevo}. Permitidos: {permitidos}")

    asignacion = orden.asignacion_activa

    # Permisos: el técnico solo mueve SUS órdenes y no puede entregar ni cancelar
    if not usuario.tiene_rol("ADMINISTRADOR", "RECEPCIONISTA"):
        if nuevo not in E.ESTADOS_TECNICO:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo recepción o administración pueden hacer este cambio")
        if asignacion is None or asignacion.id_usuario_tecnico != usuario.id_usuario:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Esta orden no está asignada a usted")

    # RN04: no se diagnostica ni repara sin técnico asignado
    if nuevo in (E.EN_DIAGNOSTICO, E.EN_REPARACION) and asignacion is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Primero debe asignar un técnico a la orden")

    # Aprobación del cliente: la decide el presupuesto en ms-facturacion
    if actual == E.ESPERANDO_APROBACION and nuevo in (E.EN_REPARACION, E.LISTO_ENTREGA):
        requerido = "APROBADO" if nuevo == E.EN_REPARACION else "RECHAZADO"
        estado_p = externos.estado_presupuesto(orden.id_orden, usuario.token)
        if estado_p != "SIN_VERIFICAR" and estado_p != requerido:
            accion = "reparar" if nuevo == E.EN_REPARACION else "devolver sin reparar"
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                f"Para {accion} se requiere un presupuesto {requerido} "
                                f"(estado actual del presupuesto: {estado_p or 'no existe'})")

    # RN11 / RF15: condiciones de cierre para entregar
    if nuevo == E.ENTREGADO:
        saldo = externos.saldo_pendiente(orden.id_orden, usuario.token)
        if saldo is not None and saldo > 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                f"No se puede entregar: la orden tiene un saldo pendiente de ${saldo:,.0f}")

    orden.estado_actual = nuevo
    if nuevo in E.FINALIZADOS:
        orden.fecha_cierre = datetime.now(timezone.utc)
        if asignacion:
            asignacion.estado_asignacion = "FINALIZADA"
            asignacion.fecha_finalizacion = datetime.now(timezone.utc)
    _registrar_historial(db, orden, actual, nuevo, usuario.id_usuario, datos.observacion)
    db.commit()
    db.refresh(orden)
    return orden
