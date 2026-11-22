"""Repuestos de prueba con su entrada de inventario inicial.
Dos repuestos quedan en stock bajo para demostrar el reporte. Ejecutar: python -m app.seed"""
from decimal import Decimal

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models import MovimientoInventario, Repuesto

ID_USUARIO_INVENTARIO = 6   # usuario "inventario" creado por el seed de ms-usuarios

REPUESTOS = [
    # código, nombre, categoría, marca, costo, venta, stock, mínimo
    ("RAM-DDR4-8GB", "Memoria RAM DDR4 8 GB 3200 MHz", "MEMORIA RAM", "Kingston", 85000, 130000, 12, 3),
    ("SSD-480GB", "Disco sólido SATA 480 GB", "ALMACENAMIENTO", "Kingston", 110000, 165000, 8, 2),
    ("SSD-NVME-1TB", "Disco sólido NVMe 1 TB", "ALMACENAMIENTO", "WD", 230000, 320000, 2, 2),
    ("JACK-DC-LEN", "Jack de carga DC para Lenovo", "CONECTORES", "Genérico", 12000, 35000, 10, 3),
    ("TECL-HP-15", "Teclado para HP 15 (español)", "TECLADOS", "HP", 60000, 110000, 1, 2),
    ("PASTA-TERM", "Pasta térmica 4 g", "CONSUMIBLES", "Arctic", 18000, 30000, 25, 5),
    ("FUENTE-500W", "Fuente de poder ATX 500 W", "FUENTES", "EVGA", 150000, 220000, 4, 1),
    ("PANT-156-FHD", "Pantalla 15.6\" FHD 30 pines", "PANTALLAS", "BOE", 280000, 420000, 3, 1),
]


def run():
    db = SessionLocal()
    try:
        for codigo, nombre, cat, marca, costo, venta, stock, minimo in REPUESTOS:
            if db.scalar(select(Repuesto).where(Repuesto.codigo == codigo)):
                continue
            r = Repuesto(codigo=codigo, nombre=nombre, categoria=cat, marca=marca, precio_costo=Decimal(costo),
                         precio_venta=Decimal(venta), stock_actual=stock, stock_minimo=minimo)
            r.movimientos.append(MovimientoInventario(
                tipo="ENTRADA", cantidad=stock, stock_anterior=0, stock_resultante=stock,
                precio_unitario=Decimal(costo), motivo="Inventario inicial", id_usuario=ID_USUARIO_INVENTARIO))
            db.add(r)
        db.commit()
        print("Datos de prueba cargados correctamente.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
