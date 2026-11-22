"""Prueba del middleware de auditoría que usan los demás microservicios."""
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import auditoria

CLAVE = "clave-solo-para-pruebas"


def app_de_prueba(monkeypatch):
    enviados = []
    monkeypatch.setenv("AUDITORIA_EN_PRUEBAS", "1")
    monkeypatch.setenv("AUDITORIA_URL", "http://auditoria")
    monkeypatch.setattr(auditoria, "despachar", lambda url, token, ev: enviados.append((url, token, ev)))
    app = FastAPI()
    app.add_middleware(auditoria.AuditoriaMiddleware, servicio="ms-prueba", clave=CLAVE)

    @app.post("/cosas")
    def crear():
        return {"id_cosa": 42, "nombre": "x"}

    @app.patch("/cosas/{id_cosa}")
    def editar(id_cosa: int):
        return {"ok": True}

    @app.get("/cosas")
    def listar():
        return []

    @app.post("/login")
    def login():
        tok = jwt.encode({"sub": "9", "roles": ["CAJA"]}, CLAVE, algorithm="HS256")
        return {"access_token": tok}

    return TestClient(app), enviados


def token(sub="3", roles=("TECNICO",)):
    t = jwt.encode({"sub": sub, "roles": list(roles), "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
                   CLAVE, algorithm="HS256")
    return {"Authorization": f"Bearer {t}"}


def test_audita_creacion_con_id_y_usuario(monkeypatch):
    c, enviados = app_de_prueba(monkeypatch)
    r = c.post("/cosas", headers=token())
    assert r.json() == {"id_cosa": 42, "nombre": "x"}          # la respuesta llega intacta
    url, tok, ev = enviados[0]
    assert url == "http://auditoria" and ev["recurso_id"] == "42" and ev["id_usuario"] == 3
    assert ev["roles"] == ["TECNICO"] and ev["servicio"] == "ms-prueba" and ev["codigo_estado"] == 200
    assert jwt.decode(tok, CLAVE, algorithms=["HS256"])["roles"] == ["SERVICIO"]


def test_usa_la_plantilla_de_ruta(monkeypatch):
    c, enviados = app_de_prueba(monkeypatch)
    c.patch("/cosas/5", headers=token())
    ev = enviados[0][2]
    assert ev["ruta"] == "/cosas/5" and ev["ruta_plantilla"] == "/cosas/{id_cosa}" and ev["recurso_id"] == "5"


def test_no_audita_lecturas(monkeypatch):
    c, enviados = app_de_prueba(monkeypatch)
    c.get("/cosas")
    assert enviados == []


def test_login_toma_el_usuario_del_token_emitido(monkeypatch):
    c, enviados = app_de_prueba(monkeypatch)
    c.post("/login")
    assert enviados[0][2]["id_usuario"] == 9


def test_url_vacia_desactiva(monkeypatch):
    c, enviados = app_de_prueba(monkeypatch)
    monkeypatch.setenv("AUDITORIA_URL", "")
    c.post("/cosas")
    assert enviados == []
