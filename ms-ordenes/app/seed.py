"""Órdenes de prueba. Usan los IDs que crean los seed de ms-usuarios y ms-clientes:
  equipo 2 (HP, cliente 2), equipo 4 (Dell, cliente 3), técnico 1 = usuario 3 (Carlos Pérez).
El equipo 1 (Lenovo de María) queda libre para la demostración en vivo.
Ejecutar: python -m app.seed (no duplica datos)."""
from sqlalchemy import select

from app.database.session import SessionLocal
from app.models import Asignacion, HistorialEstado, OrdenTrabajo

ADMIN = 1
RECEPCION = 2


def run():
    db = SessionLocal()
    try:
        if db.scalar(select(OrdenTrabajo)):
            print("Ya existen órdenes; no se cargó nada.")
            return
        o1 = OrdenTrabajo(id_equipo=4, id_cliente=3, descripcion_problema="Pantalla con líneas verticales",
                          accesorios_recibidos="Cargador", prioridad="ALTA", estado_actual="RECIBIDO",
                          id_usuario_recepcion=RECEPCION)
        o1.historial.append(HistorialEstado(estado_anterior=None, estado_nuevo="RECIBIDO",
                                            id_usuario=RECEPCION, observacion="Equipo recibido en el taller"))
        o2 = OrdenTrabajo(id_equipo=2, id_cliente=2, descripcion_problema="Equipo lento y ventilador ruidoso",
                          prioridad="MEDIA", estado_actual="EN_DIAGNOSTICO", id_usuario_recepcion=RECEPCION)
        o2.historial.extend([
            HistorialEstado(estado_anterior=None, estado_nuevo="RECIBIDO", id_usuario=RECEPCION,
                            observacion="Equipo recibido en el taller"),
            HistorialEstado(estado_anterior="RECIBIDO", estado_nuevo="RECIBIDO", id_usuario=ADMIN,
                            observacion="Técnico asignado: Carlos Pérez"),
            HistorialEstado(estado_anterior="RECIBIDO", estado_nuevo="EN_DIAGNOSTICO", id_usuario=3,
                            observacion="Inicio de revisión"),
        ])
        o2.asignaciones.append(Asignacion(id_tecnico=1, id_usuario_tecnico=3, nombre_tecnico="Carlos Pérez"))
        db.add_all([o1, o2])
        db.commit()
        print("Datos de prueba cargados correctamente.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
