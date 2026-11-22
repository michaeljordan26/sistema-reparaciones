"""Pruebas con SQLite en memoria. Los microservicios externos se SIMULAN con
monkeypatch, así las pruebas no necesitan que MS1 y MS2 estén encendidos."""
import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "clave-solo-para-pruebas"
os.environ["FACTURACION_URL"] = ""

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.clients import externos
from app.database.session import Base, get_db
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# "Base de datos" falsa de los otros servicios
EQUIPOS = {
    1: {"id_equipo": 1, "id_cliente": 10, "estado": "ACTIVO", "cliente": {"estado": "ACTIVO"}},
    2: {"id_equipo": 2, "id_cliente": 11, "estado": "ACTIVO", "cliente": {"estado": "INACTIVO"}},
}
TECNICOS = {
    1: {"id_tecnico": 1, "id_usuario": 3, "estado_laboral": "ACTIVO",
        "usuario": {"nombres": "Carlos", "apellidos": "Pérez", "activo": True}},
    2: {"id_tecnico": 2, "id_usuario": 4, "estado_laboral": "ACTIVO",
        "usuario": {"nombres": "Andrea", "apellidos": "Ruiz", "activo": True}},
    3: {"id_tecnico": 3, "id_usuario": 7, "estado_laboral": "VACACIONES",
        "usuario": {"nombres": "Luis", "apellidos": "Gil", "activo": True}},
}
SALDO = {"valor": None}   # None = facturación no configurada
PRESUPUESTO = {"estado": "SIN_VERIFICAR"}   # como responde estado_presupuesto()


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(externos, "obtener_equipo", lambda i, t: EQUIPOS.get(i))
    monkeypatch.setattr(externos, "obtener_tecnico", lambda i, t: TECNICOS.get(i))
    monkeypatch.setattr(externos, "saldo_pendiente", lambda i, t: SALDO["valor"])
    monkeypatch.setattr(externos, "estado_presupuesto", lambda i, t: PRESUPUESTO["estado"])
    SALDO["valor"] = None
    PRESUPUESTO["estado"] = "SIN_VERIFICAR"
    Base.metadata.create_all(engine)
    session = TestingSession()
    app.dependency_overrides[get_db] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()
    session.close()
    Base.metadata.drop_all(engine)


def headers(rol: str = "RECEPCIONISTA", id_usuario: int = 2) -> dict:
    payload = {"sub": str(id_usuario), "roles": [rol], "exp": datetime.now(timezone.utc) + timedelta(minutes=30)}
    return {"Authorization": f"Bearer {jwt.encode(payload, 'clave-solo-para-pruebas', algorithm='HS256')}"}


TECNICO_CARLOS = headers("TECNICO", 3)
TECNICO_ANDREA = headers("TECNICO", 4)
