"""Lógica de negocio del microservicio (las rutas solo llaman a estas funciones)."""
from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models import Rol, Tecnico, Usuario
from app.schemas.usuario import TecnicoCreate, TecnicoUpdate, UsuarioCreate, UsuarioUpdate


def _obtener_roles(db: Session, nombres: list[str]) -> list[Rol]:
    roles = db.scalars(select(Rol).where(Rol.nombre.in_(nombres))).all()
    if len(roles) != len(set(nombres)):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Uno o más roles no existen")
    return list(roles)


def autenticar(db: Session, usuario_o_correo: str, contrasena: str) -> Usuario | None:
    usuario = db.scalar(select(Usuario).where(
        or_(Usuario.nombre_usuario == usuario_o_correo, Usuario.correo == usuario_o_correo.lower())
    ))
    if usuario is None or not usuario.activo or not verify_password(contrasena, usuario.contrasena_hash):
        return None
    return usuario


def crear_usuario(db: Session, datos: UsuarioCreate) -> Usuario:
    existe = db.scalar(select(Usuario).where(or_(
        Usuario.correo == datos.correo.lower(), Usuario.nombre_usuario == datos.nombre_usuario)))
    if existe:
        raise HTTPException(status.HTTP_409_CONFLICT, "El correo o el nombre de usuario ya existe")
    usuario = Usuario(
        nombres=datos.nombres, apellidos=datos.apellidos, correo=datos.correo.lower(),
        nombre_usuario=datos.nombre_usuario, contrasena_hash=hash_password(datos.contrasena),
        roles=_obtener_roles(db, datos.roles),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def obtener_usuario(db: Session, id_usuario: int) -> Usuario:
    usuario = db.get(Usuario, id_usuario)
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    return usuario


def listar_usuarios(db: Session, solo_activos: bool = False) -> list[Usuario]:
    consulta = select(Usuario).order_by(Usuario.id_usuario)
    if solo_activos:
        consulta = consulta.where(Usuario.activo.is_(True))
    return list(db.scalars(consulta).all())


def actualizar_usuario(db: Session, id_usuario: int, datos: UsuarioUpdate) -> Usuario:
    usuario = obtener_usuario(db, id_usuario)
    cambios = datos.model_dump(exclude_unset=True)
    if "correo" in cambios:
        cambios["correo"] = cambios["correo"].lower()
        otro = db.scalar(select(Usuario).where(Usuario.correo == cambios["correo"], Usuario.id_usuario != id_usuario))
        if otro:
            raise HTTPException(status.HTTP_409_CONFLICT, "El correo ya está en uso")
    if "contrasena" in cambios:
        usuario.contrasena_hash = hash_password(cambios.pop("contrasena"))
    for campo, valor in cambios.items():
        setattr(usuario, campo, valor)
    db.commit()
    db.refresh(usuario)
    return usuario


def desactivar_usuario(db: Session, id_usuario: int, id_actual: int) -> Usuario:
    if id_usuario == id_actual:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No puede desactivar su propio usuario")
    usuario = obtener_usuario(db, id_usuario)
    usuario.activo = False  # Desactivación lógica: el historial no se pierde
    db.commit()
    db.refresh(usuario)
    return usuario


def asignar_roles(db: Session, id_usuario: int, roles: list[str]) -> Usuario:
    usuario = obtener_usuario(db, id_usuario)
    usuario.roles = _obtener_roles(db, roles)
    db.commit()
    db.refresh(usuario)
    return usuario


# ---------- Técnicos ----------

def crear_tecnico(db: Session, datos: TecnicoCreate) -> Tecnico:
    usuario = obtener_usuario(db, datos.id_usuario)
    if "TECNICO" not in {r.nombre for r in usuario.roles}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El usuario debe tener el rol TECNICO")
    if db.scalar(select(Tecnico).where(Tecnico.id_usuario == datos.id_usuario)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Este usuario ya tiene perfil de técnico")
    tecnico = Tecnico(**datos.model_dump())
    db.add(tecnico)
    db.commit()
    db.refresh(tecnico)
    return tecnico


def obtener_tecnico(db: Session, id_tecnico: int) -> Tecnico:
    tecnico = db.get(Tecnico, id_tecnico)
    if tecnico is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Técnico no encontrado")
    return tecnico


def listar_tecnicos(db: Session, estado: str | None = None) -> list[Tecnico]:
    consulta = select(Tecnico).order_by(Tecnico.id_tecnico)
    if estado:
        consulta = consulta.where(Tecnico.estado_laboral == estado)
    return list(db.scalars(consulta).all())


def actualizar_tecnico(db: Session, id_tecnico: int, datos: TecnicoUpdate) -> Tecnico:
    tecnico = obtener_tecnico(db, id_tecnico)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(tecnico, campo, valor)
    db.commit()
    db.refresh(tecnico)
    return tecnico
