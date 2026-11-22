"""Las pruebas usan SQLite en memoria: no necesitan PostgreSQL ni tocan tus datos reales."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET_KEY", "clave-solo-para-pruebas")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.database.session import Base, get_db
from app.main import app
from app.models import Rol, Usuario

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture()
def db():
    Base.metadata.create_all(engine)
    session = TestingSession()
    for nombre in ["ADMINISTRADOR", "RECEPCIONISTA", "TECNICO", "CAJA", "INVENTARIO"]:
        session.add(Rol(nombre=nombre))
    session.commit()
    admin_rol = session.query(Rol).filter_by(nombre="ADMINISTRADOR").one()
    rec_rol = session.query(Rol).filter_by(nombre="RECEPCIONISTA").one()
    session.add_all([
        Usuario(nombres="Admin", apellidos="Test", correo="admin@test.com", nombre_usuario="admin",
                contrasena_hash=hash_password("Admin123*"), roles=[admin_rol]),
        Usuario(nombres="Rece", apellidos="Test", correo="rec@test.com", nombre_usuario="recepcion",
                contrasena_hash=hash_password("Recepcion123*"), roles=[rec_rol]),
    ])
    session.commit()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def login(client, usuario, clave):
    r = client.post("/auth/login", data={"username": usuario, "password": clave})
    return r


def auth_headers(client, usuario="admin", clave="Admin123*"):
    token = login(client, usuario, clave).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
