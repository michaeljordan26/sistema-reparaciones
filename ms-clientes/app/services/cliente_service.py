"""Reglas de negocio de clientes y equipos."""
from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Cliente, Equipo
from app.schemas.cliente import ClienteCreate, ClienteUpdate, EquipoCreate, EquipoUpdate


# ---------- Clientes ----------
def crear_cliente(db: Session, datos: ClienteCreate) -> Cliente:
    existe = db.scalar(select(Cliente).where(Cliente.tipo_documento == datos.tipo_documento,
                                             Cliente.numero_documento == datos.numero_documento))
    if existe:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un cliente con ese documento")
    datos_dict = datos.model_dump()
    if datos_dict.get("correo"):
        datos_dict["correo"] = datos_dict["correo"].lower()
    cliente = Cliente(**datos_dict)
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


def obtener_cliente(db: Session, id_cliente: int) -> Cliente:
    cliente = db.get(Cliente, id_cliente)
    if cliente is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado")
    return cliente


def listar_clientes(db: Session, buscar: str | None = None, solo_activos: bool = True) -> list[Cliente]:
    consulta = select(Cliente).order_by(Cliente.apellidos, Cliente.nombres)
    if solo_activos:
        consulta = consulta.where(Cliente.estado == "ACTIVO")
    if buscar:
        patron = f"%{buscar.strip()}%"
        consulta = consulta.where(or_(Cliente.numero_documento.ilike(patron), Cliente.nombres.ilike(patron),
                                      Cliente.apellidos.ilike(patron), Cliente.telefono.ilike(patron)))
    return list(db.scalars(consulta).all())


def actualizar_cliente(db: Session, id_cliente: int, datos: ClienteUpdate) -> Cliente:
    cliente = obtener_cliente(db, id_cliente)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        if campo == "correo" and valor:
            valor = valor.lower()
        setattr(cliente, campo, valor)
    db.commit()
    db.refresh(cliente)
    return cliente


def cambiar_estado_cliente(db: Session, id_cliente: int, estado: str) -> Cliente:
    """Desactivación lógica: nunca se borra, para conservar el historial (RN13)."""
    cliente = obtener_cliente(db, id_cliente)
    cliente.estado = estado
    db.commit()
    db.refresh(cliente)
    return cliente


# ---------- Equipos ----------
def crear_equipo(db: Session, datos: EquipoCreate) -> Equipo:
    cliente = obtener_cliente(db, datos.id_cliente)
    if cliente.estado != "ACTIVO":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se pueden registrar equipos a un cliente inactivo")
    if db.scalar(select(Equipo).where(Equipo.numero_serie == datos.numero_serie)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un equipo con ese número de serie")
    equipo = Equipo(**datos.model_dump())
    db.add(equipo)
    db.commit()
    db.refresh(equipo)
    return equipo


def obtener_equipo(db: Session, id_equipo: int) -> Equipo:
    equipo = db.get(Equipo, id_equipo)
    if equipo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Equipo no encontrado")
    return equipo


def listar_equipos(db: Session, numero_serie: str | None = None, id_cliente: int | None = None) -> list[Equipo]:
    consulta = select(Equipo).order_by(Equipo.id_equipo)
    if numero_serie:
        consulta = consulta.where(Equipo.numero_serie.ilike(f"%{numero_serie.strip()}%"))
    if id_cliente:
        consulta = consulta.where(Equipo.id_cliente == id_cliente)
    return list(db.scalars(consulta).all())


def actualizar_equipo(db: Session, id_equipo: int, datos: EquipoUpdate) -> Equipo:
    equipo = obtener_equipo(db, id_equipo)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(equipo, campo, valor)
    db.commit()
    db.refresh(equipo)
    return equipo
