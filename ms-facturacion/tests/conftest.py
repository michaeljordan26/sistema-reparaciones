"""Pruebas con SQLite en memoria. ms-ordenes e ms-inventario se SIMULAN en memoria."""
import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "clave-solo-para-pruebas"
os.environ["IVA_PORCENTAJE"] = "19"

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.clients import externos
from app.database.session import Base, get_db
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Fake:
    def __init__(self):
        self.ordenes = {1: {"id_orden": 1, "codigo": "OT-000001", "estado_actual": "ESPERANDO_APROBACION"},
                        2: {"id_orden": 2, "codigo": "OT-000002", "estado_actual": "RECIBIDO"}}
        self.repuestos = {4: {"id_repuesto": 4, "codigo": "JACK-DC", "nombre": "Jack DC", "precio_venta": 35000,
                              "activo": True},
                          9: {"id_repuesto": 9, "codigo": "VIEJO", "nombre": "Inactivo", "precio_venta": 1,
                              "activo": False}}
        self.consumo = {"lineas": [], "total_materiales": 0}
        self.ordenes_caidas = False

    def obtener_orden(self, i, t):
        return self.ordenes.get(i)

    def cambiar_estado_orden(self, i, estado, obs, t):
        if self.ordenes_caidas:
            raise HTTPException(503, "El servicio de órdenes no está disponible")
        self.ordenes[i]["estado_actual"] = estado
        return self.ordenes[i]

    def obtener_repuesto(self, i, t):
        return self.repuestos.get(i)

    def consumo_orden(self, i, t):
        return self.consumo


@pytest.fixture()
def fake(monkeypatch):
    f = Fake()
    for n in ["obtener_orden", "cambiar_estado_orden", "obtener_repuesto", "consumo_orden"]:
        monkeypatch.setattr(externos, n, getattr(f, n))
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


def headers(rol: str, id_usuario: int) -> dict:
    payload = {"sub": str(id_usuario), "roles": [rol], "exp": datetime.now(timezone.utc) + timedelta(minutes=30)}
    return {"Authorization": f"Bearer {jwt.encode(payload, 'clave-solo-para-pruebas', algorithm='HS256')}"}


ADMIN = headers("ADMINISTRADOR", 1)
RECEPCION = headers("RECEPCIONISTA", 2)
TECNICO = headers("TECNICO", 3)
CAJA = headers("CAJA", 5)
