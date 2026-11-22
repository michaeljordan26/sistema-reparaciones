"""Pruebas con SQLite en memoria. Los demás microservicios se SIMULAN."""
import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "clave-solo-para-pruebas"

from datetime import date, datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.clients import externos
from app.database.session import Base, get_db
from app.main import app
from app.services import notificacion_service

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
CLAVE = "clave-solo-para-pruebas"


class Fake:
    def __init__(self):
        self.caido: set[str] = set()
        self.orden_datos = {7: {"id_orden": 7, "codigo": "OT-000007", "estado_actual": "LISTO_ENTREGA",
                                "id_equipo": 1, "id_cliente": 1}}
        self.lista_ordenes = [
            {"id_orden": 1, "codigo": "OT-000001", "estado_actual": "RECIBIDO", "prioridad": "BAJA",
             "fecha_recepcion": "2026-11-01T10:00:00Z", "fecha_cierre": None, "asignacion_activa": None},
            {"id_orden": 2, "codigo": "OT-000002", "estado_actual": "EN_REPARACION", "prioridad": "URGENTE",
             "fecha_recepcion": "2026-11-02T10:00:00Z", "fecha_cierre": None,
             "asignacion_activa": {"nombre_tecnico": "Carlos Pérez"}},
            {"id_orden": 3, "codigo": "OT-000003", "estado_actual": "ENTREGADO", "prioridad": "MEDIA",
             "fecha_recepcion": "2026-11-01T10:00:00Z", "fecha_cierre": "2026-11-03T10:00:00Z",
             "asignacion_activa": None},
        ]

    def _revisar(self, s):
        if s in self.caido:
            raise externos.ServicioNoDisponible(f"El servicio de {s} no está disponible")

    def orden(self, i, t):
        self._revisar("órdenes")
        return self.orden_datos.get(i)

    def equipo(self, i, t):
        self._revisar("clientes")
        return {"tipo_equipo": "PORTATIL", "marca": "Lenovo", "modelo": "IdeaPad 3",
                "cliente": {"nombres": "María José", "correo": "maria@correo.com", "telefono": "3001234567"}}

    def ordenes(self, t):
        self._revisar("órdenes")
        return self.lista_ordenes

    def ingresos(self, t, d, h):
        self._revisar("facturación")
        return {"total": 100000, "cantidad_pagos": 2, "por_metodo": {"EFECTIVO": 100000}}

    def cartera(self, t):
        self._revisar("facturación")
        return {"facturas": [], "total_por_cobrar": 50000}

    def repuestos(self, t):
        self._revisar("inventario")
        return [{"id_repuesto": 1, "codigo": "RAM", "nombre": "RAM", "stock_actual": 1, "stock_minimo": 2,
                 "stock_bajo": True, "precio_costo": 80000},
                {"id_repuesto": 2, "codigo": "SSD", "nombre": "SSD", "stock_actual": 10, "stock_minimo": 2,
                 "stock_bajo": False, "precio_costo": 100000}]

    def garantias_vigentes(self, t):
        self._revisar("reparaciones")
        fin = (date.today() + timedelta(days=5)).isoformat()
        return [{"fecha_fin": fin, "reclamaciones": [{"estado": "ABIERTA"}]}]


@pytest.fixture()
def fake(monkeypatch):
    f = Fake()
    for n in ["orden", "equipo", "ordenes", "ingresos", "cartera", "repuestos", "garantias_vigentes"]:
        monkeypatch.setattr(externos, n, getattr(f, n))
    monkeypatch.setattr(notificacion_service, "fabrica_sesiones", TestingSession)
    return f


@pytest.fixture()
def client(fake):
    Base.metadata.create_all(engine)
    session = TestingSession()
    app.dependency_overrides[get_db] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()
    session.close()
    Base.metadata.drop_all(engine)


def headers(rol: str, id_usuario: int = 1) -> dict:
    payload = {"sub": str(id_usuario), "roles": [rol], "exp": datetime.now(timezone.utc) + timedelta(minutes=30)}
    return {"Authorization": f"Bearer {jwt.encode(payload, CLAVE, algorithm='HS256')}"}


def servicio(nombre: str = "ms-ordenes") -> dict:
    payload = {"sub": f"servicio:{nombre}", "roles": ["SERVICIO"], "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
    return {"Authorization": f"Bearer {jwt.encode(payload, CLAVE, algorithm='HS256')}"}


ADMIN = headers("ADMINISTRADOR")
RECEPCION = headers("RECEPCIONISTA", 2)
CAJA = headers("CAJA", 5)
TECNICO = headers("TECNICO", 3)
