"""Pruebas con SQLite en memoria. Los tokens se fabrican con la clave de prueba,
igual que los emitiría ms-usuarios."""
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

from app.database.session import Base, get_db
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture()
def client():
    Base.metadata.create_all(engine)
    session = TestingSession()
    app.dependency_overrides[get_db] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()
    session.close()
    Base.metadata.drop_all(engine)


def headers(rol: str = "RECEPCIONISTA", minutos: int = 30) -> dict:
    payload = {"sub": "1", "roles": [rol], "exp": datetime.now(timezone.utc) + timedelta(minutes=minutos)}
    token = jwt.encode(payload, "clave-solo-para-pruebas", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}
