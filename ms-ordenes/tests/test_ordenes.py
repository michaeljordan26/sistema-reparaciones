from tests.conftest import PRESUPUESTO, SALDO, TECNICO_ANDREA, TECNICO_CARLOS, headers

ORDEN = {"id_equipo": 1, "descripcion_problema": "No enciende", "accesorios_recibidos": "Cargador",
         "prioridad": "ALTA"}


def crear(client):
    return client.post("/ordenes", json=ORDEN, headers=headers())


def estado(client, id_orden, nuevo, h=None):
    return client.patch(f"/ordenes/{id_orden}/estado", json={"estado": nuevo}, headers=h or headers())


def asignar(client, id_orden, id_tecnico=1):
    return client.post(f"/ordenes/{id_orden}/asignar", json={"id_tecnico": id_tecnico}, headers=headers())


# ---------- Crear ----------
def test_crear_orden(client):
    r = crear(client)
    assert r.status_code == 201
    d = r.json()
    assert d["codigo"] == "OT-000001" and d["estado_actual"] == "RECIBIDO" and d["id_cliente"] == 10
    assert len(d["historial"]) == 1


def test_equipo_inexistente_400(client):
    assert client.post("/ordenes", json={**ORDEN, "id_equipo": 99}, headers=headers()).status_code == 400


def test_cliente_inactivo_400(client):
    assert client.post("/ordenes", json={**ORDEN, "id_equipo": 2}, headers=headers()).status_code == 400


def test_no_dos_ordenes_abiertas_mismo_equipo(client):
    crear(client)
    assert crear(client).status_code == 409


def test_tecnico_no_crea_ordenes(client):
    assert client.post("/ordenes", json=ORDEN, headers=TECNICO_CARLOS).status_code == 403


# ---------- Asignar ----------
def test_asignar_y_reasignar_tecnico(client):
    id_o = crear(client).json()["id_orden"]
    assert asignar(client, id_o, 1).json()["asignacion_activa"]["nombre_tecnico"] == "Carlos Pérez"
    d = asignar(client, id_o, 2).json()
    assert d["asignacion_activa"]["nombre_tecnico"] == "Andrea Ruiz"
    assert [a["estado_asignacion"] for a in d["asignaciones"]] == ["REASIGNADA", "ACTIVA"]


def test_tecnico_en_vacaciones_400(client):
    id_o = crear(client).json()["id_orden"]
    assert asignar(client, id_o, 3).status_code == 400


def test_tecnico_inexistente_400(client):
    id_o = crear(client).json()["id_orden"]
    assert asignar(client, id_o, 99).status_code == 400


# ---------- Estados ----------
def test_no_diagnostica_sin_tecnico(client):
    id_o = crear(client).json()["id_orden"]
    assert estado(client, id_o, "EN_DIAGNOSTICO").status_code == 400


def test_transicion_invalida(client):
    id_o = crear(client).json()["id_orden"]
    r = estado(client, id_o, "ENTREGADO")
    assert r.status_code == 400 and "No se puede pasar" in r.json()["detail"]


def test_flujo_completo_hasta_entrega(client):
    id_o = crear(client).json()["id_orden"]
    asignar(client, id_o, 1)
    for e in ["EN_DIAGNOSTICO", "ESPERANDO_APROBACION", "EN_REPARACION", "LISTO_ENTREGA"]:
        assert estado(client, id_o, e, TECNICO_CARLOS).status_code == 200, e
    r = estado(client, id_o, "ENTREGADO")
    d = r.json()
    assert d["estado_actual"] == "ENTREGADO" and d["fecha_cierre"] is not None
    assert d["asignacion_activa"] is None and d["transiciones_permitidas"] == []
    assert len(d["historial"]) == 7   # recibido + asignación + 5 cambios


def test_tecnico_no_mueve_orden_ajena(client):
    id_o = crear(client).json()["id_orden"]
    asignar(client, id_o, 1)   # asignada a Carlos
    assert estado(client, id_o, "EN_DIAGNOSTICO", TECNICO_ANDREA).status_code == 403


def test_tecnico_no_puede_entregar(client):
    id_o = crear(client).json()["id_orden"]
    asignar(client, id_o, 1)
    for e in ["EN_DIAGNOSTICO", "ESPERANDO_APROBACION", "EN_REPARACION", "LISTO_ENTREGA"]:
        estado(client, id_o, e, TECNICO_CARLOS)
    assert estado(client, id_o, "ENTREGADO", TECNICO_CARLOS).status_code == 403


def test_no_entrega_con_saldo_pendiente(client):
    id_o = crear(client).json()["id_orden"]
    asignar(client, id_o, 1)
    for e in ["EN_DIAGNOSTICO", "ESPERANDO_APROBACION", "EN_REPARACION", "LISTO_ENTREGA"]:
        estado(client, id_o, e, TECNICO_CARLOS)
    SALDO["valor"] = 150000
    r = estado(client, id_o, "ENTREGADO")
    assert r.status_code == 400 and "saldo pendiente" in r.json()["detail"]
    SALDO["valor"] = 0
    assert estado(client, id_o, "ENTREGADO").status_code == 200


def test_cancelar_permite_nueva_orden(client):
    id_o = crear(client).json()["id_orden"]
    assert estado(client, id_o, "CANCELADO").status_code == 200
    assert crear(client).status_code == 201


# ---------- Consultas ----------
def test_pendientes_y_finalizadas(client):
    id_o = crear(client).json()["id_orden"]
    estado(client, id_o, "CANCELADO")
    crear(client)
    h = headers()
    assert len(client.get("/ordenes", params={"grupo": "pendientes"}, headers=h).json()) == 1
    assert len(client.get("/ordenes", params={"grupo": "finalizadas"}, headers=h).json()) == 1


def test_mis_ordenes(client):
    id_o = crear(client).json()["id_orden"]
    asignar(client, id_o, 1)
    assert len(client.get("/ordenes/mis-ordenes", headers=TECNICO_CARLOS).json()) == 1
    assert client.get("/ordenes/mis-ordenes", headers=TECNICO_ANDREA).json() == []


def test_historial_del_equipo(client):
    id_o = crear(client).json()["id_orden"]
    estado(client, id_o, "CANCELADO")
    crear(client)
    assert len(client.get("/equipos/1/historial", headers=headers()).json()) == 2


def test_sin_token_401(client):
    assert client.get("/ordenes").status_code == 401


# ---------- Presupuesto (ms-facturacion) ----------
def preparar_espera(client):
    id_o = crear(client).json()["id_orden"]
    asignar(client, id_o, 1)
    estado(client, id_o, "EN_DIAGNOSTICO", TECNICO_CARLOS)
    estado(client, id_o, "ESPERANDO_APROBACION", TECNICO_CARLOS)
    return id_o


def test_no_repara_sin_presupuesto_aprobado(client):
    id_o = preparar_espera(client)
    for estado_p in [None, "PENDIENTE", "RECHAZADO"]:
        PRESUPUESTO["estado"] = estado_p
        r = estado(client, id_o, "EN_REPARACION")
        assert r.status_code == 400 and "APROBADO" in r.json()["detail"]
    PRESUPUESTO["estado"] = "APROBADO"
    assert estado(client, id_o, "EN_REPARACION").status_code == 200


def test_devolver_sin_reparar_exige_rechazo(client):
    id_o = preparar_espera(client)
    PRESUPUESTO["estado"] = "PENDIENTE"
    assert estado(client, id_o, "LISTO_ENTREGA").status_code == 400
    PRESUPUESTO["estado"] = "RECHAZADO"
    assert estado(client, id_o, "LISTO_ENTREGA").status_code == 200
