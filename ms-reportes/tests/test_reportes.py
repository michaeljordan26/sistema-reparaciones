from tests.conftest import ADMIN, CAJA, RECEPCION, TECNICO, servicio


def evento(**cambios):
    base = {"servicio": "ms-ordenes", "metodo": "PATCH", "ruta": "/ordenes/7/estado",
            "ruta_plantilla": "/ordenes/{id_orden}/estado", "recurso_id": "7", "codigo_estado": 200,
            "id_usuario": 2, "roles": ["RECEPCIONISTA"], "duracion_ms": 30, "ip": "127.0.0.1"}
    return {**base, **cambios}


def enviar(client, h=None, **cambios):
    return client.post("/auditoria/eventos", json=evento(**cambios), headers=h or servicio(cambios.get("servicio", "ms-ordenes")))


# ---------- Auditoría ----------
def test_solo_servicios_registran_eventos(client):
    assert client.post("/auditoria/eventos", json=evento()).status_code == 401
    assert enviar(client, h=ADMIN).status_code == 403          # un usuario, aunque sea admin, no puede
    assert enviar(client, h=servicio("ms-clientes")).status_code == 403   # suplantar otro servicio


def test_registra_y_describe_la_accion(client):
    assert enviar(client).status_code == 201
    enviar(client, servicio="ms-facturacion", metodo="POST", ruta="/facturas/1/pagos",
           ruta_plantilla="/facturas/{id_factura}/pagos", codigo_estado=400, recurso_id="1")
    d = client.get("/auditoria", headers=ADMIN).json()
    assert d["total"] == 2
    assert d["registros"][0]["accion"] == "Registrar pago (rechazado)" and d["registros"][0]["exito"] is False
    assert d["registros"][1]["accion"] == "Cambiar estado de orden"


def test_filtros_y_paginacion(client):
    for _ in range(3):
        enviar(client)
    enviar(client, servicio="ms-usuarios", metodo="POST", ruta="/auth/login", ruta_plantilla="/auth/login",
           codigo_estado=401, recurso_id=None, id_usuario=None, roles=[])
    assert client.get("/auditoria", params={"servicio": "ms-ordenes"}, headers=ADMIN).json()["total"] == 3
    assert client.get("/auditoria", params={"solo_fallidos": True}, headers=ADMIN).json()["total"] == 1
    p = client.get("/auditoria", params={"limite": 2, "desplazamiento": 2}, headers=ADMIN).json()
    assert p["total"] == 4 and len(p["registros"]) == 2


def test_resumen_auditoria(client):
    enviar(client)
    enviar(client, servicio="ms-usuarios", metodo="POST", ruta="/auth/login", ruta_plantilla="/auth/login",
           codigo_estado=401, recurso_id=None)
    enviar(client, codigo_estado=403)
    r = client.get("/auditoria/resumen", headers=ADMIN).json()
    assert r["total_operaciones"] == 3 and r["accesos_denegados"] == 2 and r["inicios_sesion_fallidos"] == 1


def test_solo_admin_consulta_auditoria(client):
    assert client.get("/auditoria", headers=RECEPCION).status_code == 403


# ---------- Notificaciones ----------
def test_cambio_de_estado_genera_notificacion(client):
    enviar(client)
    n = client.get("/notificaciones", headers=RECEPCION).json()
    assert len(n) == 1
    assert n[0]["tipo"] == "LISTO_ENTREGA" and n[0]["canal"] == "CORREO" and n[0]["destinatario"] == "maria@correo.com"
    assert "María" in n[0]["mensaje"] and "Lenovo" in n[0]["mensaje"] and n[0]["estado"] == "ENVIADA"


def test_no_duplica_notificaciones(client):
    enviar(client)
    enviar(client)
    assert len(client.get("/notificaciones", headers=RECEPCION).json()) == 1


def test_operacion_fallida_no_notifica(client):
    enviar(client, codigo_estado=400)
    enviar(client, servicio="ms-clientes", metodo="POST", ruta="/clientes", ruta_plantilla="/clientes")
    assert client.get("/notificaciones", headers=RECEPCION).json() == []


def test_si_clientes_cae_queda_fallida(client, fake):
    fake.caido.add("clientes")
    enviar(client)
    n = client.get("/notificaciones", headers=RECEPCION).json()[0]
    assert n["estado"] == "FALLIDA" and "clientes" in n["detalle_error"]
    fake.caido.clear()
    r = client.post("/notificaciones/ordenes/7", headers=RECEPCION).json()   # reenvío manual
    assert r["estado"] == "ENVIADA" and r["id_notificacion"] == n["id_notificacion"]


def test_tecnico_no_ve_notificaciones(client):
    assert client.get("/notificaciones", headers=TECNICO).status_code == 403


# ---------- Reportes ----------
def test_reporte_ordenes(client):
    d = client.get("/reportes/ordenes", headers=RECEPCION).json()
    assert d["pendientes"] == 2 and d["finalizadas"] == 1 and d["sin_tecnico"] == 1
    assert d["lista_pendientes"][0]["codigo"] == "OT-000002"         # URGENTE primero
    assert d["carga_por_tecnico"] == {"Carlos Pérez": 1} and d["dias_promedio_hasta_entrega"] == 2.0


def test_reporte_inventario(client):
    d = client.get("/reportes/inventario", headers=headers_inv()).json()
    assert d["valor_inventario_costo"] == 80000 + 1000000 and [r["codigo"] for r in d["stock_bajo"]] == ["RAM"]


def headers_inv():
    from tests.conftest import headers
    return headers("INVENTARIO", 6)


def test_permisos_reportes(client):
    assert client.get("/reportes/finanzas", headers=RECEPCION).status_code == 403
    assert client.get("/reportes/finanzas", headers=CAJA).json()["cartera"]["total_por_cobrar"] == 50000
    assert client.get("/reportes/panel", headers=CAJA).status_code == 403


def test_reporte_con_servicio_caido_503(client, fake):
    fake.caido.add("órdenes")
    assert client.get("/reportes/ordenes", headers=RECEPCION).status_code == 503


def test_panel_tolera_servicios_caidos(client, fake):
    fake.caido.add("inventario")
    d = client.get("/reportes/panel", headers=ADMIN).json()
    assert d["ordenes"]["disponible"] and d["finanzas"]["disponible"] and d["auditoria"]["disponible"]
    assert d["inventario"]["disponible"] is False and "inventario" in d["inventario"]["error"]
    assert d["garantias"]["datos"]["por_vencer_15_dias"] == 1 and d["garantias"]["datos"]["reclamaciones_abiertas"] == 1
