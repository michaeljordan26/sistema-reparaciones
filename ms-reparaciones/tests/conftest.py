"""Pruebas con SQLite en memoria. ms-usuarios, ms-ordenes y ms-inventario se SIMULAN
con una clase falsa que guarda estados y stock en memoria."""
import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "clave-solo-para-pruebas"

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

# id_usuario -> id_tecnico (como respondería ms-usuarios /auth/validar)
TECNICOS = {3: 1, 4: 2}


class Fake:
    def __init__(self):
        self.ordenes = {
            1: {"id_orden": 1, "codigo": "OT-000001", "estado_actual": "EN_DIAGNOSTICO", "id_equipo": 5,
                "id_cliente": 9, "asignacion_activa": {"id_tecnico": 1}},
            2: {"id_orden": 2, "codigo": "OT-000002", "estado_actual": "RECIBIDO", "id_equipo": 6,
                "id_cliente": 9, "asignacion_activa": None},
        }
        self.stock = {1: 5}
        self.repuestos = {1: {"id_repuesto": 1, "codigo": "JACK-DC", "nombre": "Jack DC", "precio_venta": 35000}}
        self.mov = 0
        self.ordenes_caidas = False

    def validar_usuario(self, token):
        uid = int(jwt.decode(token, "clave-solo-para-pruebas", algorithms=["HS256"])["sub"])
        return {"id_usuario": uid, "id_tecnico": TECNICOS.get(uid)}

    def obtener_orden(self, i, t):
        return self.ordenes.get(i)

    def cambiar_estado_orden(self, i, estado, obs, t):
        if self.ordenes_caidas:
            raise HTTPException(503, "El servicio de órdenes no está disponible")
        self.ordenes[i]["estado_actual"] = estado
        return self.ordenes[i]

    def sacar_repuesto(self, i, cantidad, id_orden, motivo, t):
        if self.stock[i] < cantidad:
            raise HTTPException(400, "[inventario] Stock insuficiente")
        self.stock[i] -= cantidad
        self.mov += 1
        return {"id_movimiento": self.mov, "precio_unitario": self.repuestos[i]["precio_venta"]}

    def devolver_repuesto(self, i, cantidad, id_orden, motivo, t):
        self.stock[i] += cantidad
        return {}

    def obtener_repuesto(self, i, t):
        return self.repuestos.get(i)


@pytest.fixture()
def fake(monkeypatch):
    f = Fake()
    for nombre in ["validar_usuario", "obtener_orden", "cambiar_estado_orden", "sacar_repuesto",
                   "devolver_repuesto", "obtener_repuesto"]:
        monkeypatch.setattr(externos, nombre, getattr(f, nombre))
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


CARLOS = headers("TECNICO", 3)       # técnico 1, asignado a la orden 1
ANDREA = headers("TECNICO", 4)       # técnico 2
RECEPCION = headers("RECEPCIONISTA", 2)
ADMIN = headers("ADMINISTRADOR", 1)
