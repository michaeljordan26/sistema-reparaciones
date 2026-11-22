"""Carga roles y usuarios de prueba. Ejecutar: python -m app.seed
Es seguro ejecutarlo varias veces (no duplica datos)."""
from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models import Rol, Tecnico, Usuario

ROLES = {
    "ADMINISTRADOR": "Gestiona usuarios, roles, inventario y pagos",
    "RECEPCIONISTA": "Registra clientes, equipos y órdenes de trabajo",
    "TECNICO": "Diagnostica, repara, usa repuestos y genera garantías",
    "CAJA": "Gestiona presupuestos, facturas, pagos y saldos",
    "INVENTARIO": "Gestiona repuestos, existencias y movimientos",
}

USUARIOS = [
    # (nombres, apellidos, correo, usuario, contraseña, roles, especialidad_tecnico)
    ("Admin", "Sistema", settings.ADMIN_EMAIL, "admin", settings.ADMIN_PASSWORD, ["ADMINISTRADOR"], None),
    ("Laura", "Gómez", "recepcion@taller.com", "recepcion", "Recepcion123*", ["RECEPCIONISTA"], None),
    ("Carlos", "Pérez", "tecnico1@taller.com", "tecnico1", "Tecnico123*", ["TECNICO"], "Portátiles y hardware"),
    ("Andrea", "Ruiz", "tecnico2@taller.com", "tecnico2", "Tecnico123*", ["TECNICO"], "Software y redes"),
    ("Jorge", "Díaz", "caja@taller.com", "caja", "Caja1234*", ["CAJA"], None),
    ("Sofía", "Mora", "inventario@taller.com", "inventario", "Inventario123*", ["INVENTARIO"], None),
]


def run():
    db = SessionLocal()
    try:
        for nombre, desc in ROLES.items():
            if not db.scalar(select(Rol).where(Rol.nombre == nombre)):
                db.add(Rol(nombre=nombre, descripcion=desc))
        db.commit()

        for nombres, apellidos, correo, user, clave, roles, especialidad in USUARIOS:
            if db.scalar(select(Usuario).where(Usuario.nombre_usuario == user)):
                continue
            u = Usuario(nombres=nombres, apellidos=apellidos, correo=correo.lower(), nombre_usuario=user,
                        contrasena_hash=hash_password(clave),
                        roles=list(db.scalars(select(Rol).where(Rol.nombre.in_(roles)))))
            db.add(u)
            db.flush()
            if especialidad:
                db.add(Tecnico(id_usuario=u.id_usuario, especialidad=especialidad))
        db.commit()
        print("Datos de prueba cargados correctamente.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
