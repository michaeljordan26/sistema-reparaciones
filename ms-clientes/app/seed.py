"""Carga clientes y equipos de prueba. Ejecutar: python -m app.seed (no duplica datos)."""
from sqlalchemy import select

from app.database.session import SessionLocal
from app.models import Cliente, Equipo

CLIENTES = [
    ("CC", "1012345678", "María", "Rodríguez", "3001234567", "maria.rodriguez@correo.com", "Calle 45 # 12-30"),
    ("CC", "79876543", "Juan", "Martínez", "3109876543", "juan.martinez@correo.com", "Carrera 7 # 80-15"),
    ("NIT", "900123456-7", "Soluciones", "Andinas SAS", "6017654321", "compras@andinas.com", "Av. El Dorado # 68-50"),
]

EQUIPOS = [  # (documento del dueño, tipo, marca, modelo, serie, descripción)
    ("1012345678", "PORTATIL", "Lenovo", "IdeaPad 3", "PF3ABC12", "No enciende, cargador original"),
    ("79876543", "ESCRITORIO", "HP", "ProDesk 400 G7", "MXL1234XYZ", "Lento, ruido en el ventilador"),
    ("79876543", "IMPRESORA", "Epson", "L3250", "X8HK004521", "Atasca el papel"),
    ("900123456-7", "PORTATIL", "Dell", "Latitude 5420", "DL5420SN99", "Pantalla con líneas"),
]


def run():
    db = SessionLocal()
    try:
        for tipo, doc, nom, ape, tel, correo, dirc in CLIENTES:
            if not db.scalar(select(Cliente).where(Cliente.numero_documento == doc)):
                db.add(Cliente(tipo_documento=tipo, numero_documento=doc, nombres=nom, apellidos=ape,
                               telefono=tel, correo=correo, direccion=dirc))
        db.commit()
        for doc, tipo, marca, modelo, serie, desc in EQUIPOS:
            if db.scalar(select(Equipo).where(Equipo.numero_serie == serie)):
                continue
            cliente = db.scalar(select(Cliente).where(Cliente.numero_documento == doc))
            db.add(Equipo(id_cliente=cliente.id_cliente, tipo_equipo=tipo, marca=marca, modelo=modelo,
                          numero_serie=serie, descripcion=desc))
        db.commit()
        print("Datos de prueba cargados correctamente.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
