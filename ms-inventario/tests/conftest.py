"""Pruebas con SQLite en memoria. ms-ordenes se SIMULA con monkeypatch."""
import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "clave-solo-para-pruebas"

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

ORDENES = {
    10: {"id_orden": 10, "estado_actual": "EN_REPARACION"},
    11: {"id_orden": 11, "estado_actual": "RECIBIDO"},
    12: {"id_orden": 12, "estado_actual": "ENTREGADO"},
}


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(externos, "obtener_orden", lambda i, t: ORDENES.get(i))
    Base.metadata.create_all(engine)
    session = TestingSession()
    app.dependency_overrides[get_db] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()
    session.close()
    Base.metadata.drop_all(engine)


def headers(rol: str = "INVENTARIO", id_usuario: int = 6) -> dict:
    payload = {"sub": str(id_usuario), "roles": [rol], "exp": datetime.now(timezone.utc) + timedelta(minutes=30)}
    return {"Authorization": f"Bearer {jwt.encode(payload, 'clave-solo-para-pruebas', algorithm='HS256')}"}


TECNICO = headers("TECNICO", 3)
