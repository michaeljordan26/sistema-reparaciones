from datetime import date, timedelta
from app.core.tiempo import hoy

from app.models import Presupuesto
from tests.conftest import ADMIN, CAJA, RECEPCION, TECNICO, TestingSession

PRESUPUESTO = {"id_orden": 1, "mano_obra": [{"descripcion": "Cambio de jack", "horas": 1.5, "valor_hora": 40000}],
               "repuestos": [{"id_repuesto": 4, "cantidad": 1}]}
APRUEBA = {"decision": "APROBADO", "medio": "TELEFONO", "nombre_responde": "María Rodríguez"}


def crear(client, h=TECNICO, **cambios):
    return client.post("/presupuestos", json={**PRESUPUESTO, **cambios}, headers=h)


def aprobar(client, id_p, decision="APROBADO"):
    return client.post(f"/presupuestos/{id_p}/respuesta", json={**APRUEBA, "decision": decision}, headers=RECEPCION)


def hasta_factura(client, fake, consumo_jack=1):
    """Presupuesto aprobado + reparación terminada + factura. Devuelve la factura."""
    id_p = crear(client).json()["id_presupuesto"]
    aprobar(client, id_p)
    fake.ordenes[1]["estado_actual"] = "LISTO_ENTREGA"
    fake.consumo = {"lineas": [{"id_repuesto": 4, "codigo": "JACK-DC", "nombre": "Jack DC", "cantidad": consumo_jack,
                                "precio_unitario": 35000.0, "subtotal": 35000.0 * consumo_jack}]}
    return client.post("/facturas", json={"id_orden": 1}, headers=CAJA).json()


# ---------- Presupuesto ----------
def test_calcula_materiales_mano_obra_e_iva(client):
    d = crear(client).json()
    assert d["codigo"] == "PR-000001" and d["estado"] == "PENDIENTE"
    assert d["subtotal_mano_obra"] == 60000 and d["subtotal_materiales"] == 35000
    assert d["subtotal"] == 95000 and d["iva"] == 18050 and d["total"] == 113050
    assert d["fecha_vencimiento"] == str(hoy() + timedelta(days=15))


def test_presupuesto_exige_mano_obra(client):
    assert crear(client, mano_obra=[]).status_code == 422


def test_presupuesto_orden_en_otro_estado(client):
    assert crear(client, id_orden=2).status_code == 400


def test_repuesto_inexistente_o_inactivo(client):
    assert crear(client, repuestos=[{"id_repuesto": 99, "cantidad": 1}]).status_code == 400
    assert crear(client, repuestos=[{"id_repuesto": 9, "cantidad": 1}]).status_code == 400


def test_un_presupuesto_vigente_por_orden(client):
    crear(client)
    assert crear(client).status_code == 409


def test_inventario_no_crea_presupuestos(client):
    from tests.conftest import headers
    assert crear(client, h=headers("INVENTARIO", 6)).status_code == 403


# ---------- Respuesta del cliente ----------
def test_aprobar_mueve_orden_a_reparacion(client, fake):
    id_p = crear(client).json()["id_presupuesto"]
    r = aprobar(client, id_p)
    assert r.status_code == 200 and r.json()["estado"] == "APROBADO"
    assert r.json()["respuesta"]["nombre_responde"] == "María Rodríguez"
    assert fake.ordenes[1]["estado_actual"] == "EN_REPARACION"


def test_rechazar_devuelve_sin_reparar(client, fake):
    id_p = crear(client).json()["id_presupuesto"]
    assert aprobar(client, id_p, "RECHAZADO").json()["estado"] == "RECHAZADO"
    assert fake.ordenes[1]["estado_actual"] == "LISTO_ENTREGA"
    assert client.get("/ordenes/1/saldo", headers=RECEPCION).json()["saldo_pendiente"] == 0


def test_no_se_responde_dos_veces(client):
    id_p = crear(client).json()["id_presupuesto"]
    aprobar(client, id_p)
    assert aprobar(client, id_p).status_code == 400


def test_tecnico_no_registra_respuesta(client):
    id_p = crear(client).json()["id_presupuesto"]
    assert client.post(f"/presupuestos/{id_p}/respuesta", json=APRUEBA, headers=TECNICO).status_code == 403


def test_compensacion_si_ordenes_falla(client, fake):
    id_p = crear(client).json()["id_presupuesto"]
    fake.ordenes_caidas = True
    assert aprobar(client, id_p).status_code == 503
    d = client.get(f"/presupuestos/{id_p}", headers=CAJA).json()
    assert d["estado"] == "PENDIENTE" and d["respuesta"] is None      # se deshizo
    fake.ordenes_caidas = False
    assert aprobar(client, id_p).status_code == 200                    # se puede reintentar


def test_presupuesto_vencido_no_se_aprueba(client):
    id_p = crear(client).json()["id_presupuesto"]
    s = TestingSession()
    p = s.get(Presupuesto, id_p)
    p.fecha, p.fecha_vencimiento = hoy() - timedelta(days=20), hoy() - timedelta(days=5)
    s.commit()
    s.close()
    r = aprobar(client, id_p)
    assert r.status_code == 400 and "venció" in r.json()["detail"]


def test_anular_permite_nuevo_presupuesto(client):
    id_p = crear(client).json()["id_presupuesto"]
    assert client.patch(f"/presupuestos/{id_p}/anular", json={"motivo": "Cliente pidió otra cotización"},
                        headers=CAJA).json()["estado"] == "ANULADO"
    assert crear(client).status_code == 201


# ---------- Factura ----------
def test_factura_usa_consumo_real(client, fake):
    f = hasta_factura(client, fake, consumo_jack=2)   # presupuestó 1 jack, usó 2
    assert f["numero"] == "FV-000001" and f["estado"] == "PENDIENTE"
    assert f["subtotal_materiales"] == 70000 and f["subtotal_mano_obra"] == 60000
    assert f["total"] == 130000 * 1.19


def test_no_factura_sin_reparacion_terminada(client):
    id_p = crear(client).json()["id_presupuesto"]
    aprobar(client, id_p)   # orden EN_REPARACION
    assert client.post("/facturas", json={"id_orden": 1}, headers=CAJA).status_code == 400


def test_no_factura_presupuesto_rechazado(client, fake):
    id_p = crear(client).json()["id_presupuesto"]
    aprobar(client, id_p, "RECHAZADO")
    assert client.post("/facturas", json={"id_orden": 1}, headers=CAJA).status_code == 400


def test_una_factura_activa_por_orden(client, fake):
    hasta_factura(client, fake)
    assert client.post("/facturas", json={"id_orden": 1}, headers=CAJA).status_code == 409


def test_recepcion_no_genera_facturas(client, fake):
    id_p = crear(client).json()["id_presupuesto"]
    aprobar(client, id_p)
    fake.ordenes[1]["estado_actual"] = "LISTO_ENTREGA"
    assert client.post("/facturas", json={"id_orden": 1}, headers=RECEPCION).status_code == 403


# ---------- Pagos y saldo ----------
def test_saldo_con_presupuesto_aprobado_sin_facturar(client, fake):
    id_p = crear(client).json()["id_presupuesto"]
    aprobar(client, id_p)
    s = client.get("/ordenes/1/saldo", headers=RECEPCION).json()
    assert s["saldo_pendiente"] == 113050 and "sin facturar" in s["detalle"]


def test_abono_y_pago_total(client, fake):
    f = hasta_factura(client, fake)   # total 113050
    url = f"/facturas/{f['id_factura']}/pagos"
    a = client.post(url, json={"monto": 50000, "metodo": "EFECTIVO"}, headers=RECEPCION).json()
    assert a["tipo"] == "ABONO" and a["saldo_resultante"] == 63050
    assert client.get("/ordenes/1/saldo", headers=RECEPCION).json()["saldo_pendiente"] == 63050
    assert client.post(url, json={"monto": 70000}, headers=CAJA).status_code == 400       # excede el saldo
    p = client.post(url, json={"monto": 63050, "metodo": "NEQUI", "referencia": "M123"}, headers=CAJA).json()
    assert p["tipo"] == "PAGO_TOTAL" and p["saldo_resultante"] == 0
    assert client.get(f"/facturas/{f['id_factura']}", headers=CAJA).json()["estado"] == "PAGADA"
    assert client.post(url, json={"monto": 1}, headers=CAJA).status_code == 400            # ya pagada
    assert client.get("/ordenes/1/saldo", headers=RECEPCION).json()["saldo_pendiente"] == 0


def test_referencia_obligatoria_si_no_es_efectivo(client, fake):
    f = hasta_factura(client, fake)
    r = client.post(f"/facturas/{f['id_factura']}/pagos", json={"monto": 1000, "metodo": "TARJETA"}, headers=CAJA)
    assert r.status_code == 422


def test_anular_pago_restaura_saldo(client, fake):
    f = hasta_factura(client, fake)
    p = client.post(f"/facturas/{f['id_factura']}/pagos", json={"monto": 113050}, headers=CAJA).json()
    assert client.patch(f"/pagos/{p['id_pago']}/anular", json={"motivo": "Pago digitado dos veces"},
                        headers=CAJA).status_code == 403
    client.patch(f"/pagos/{p['id_pago']}/anular", json={"motivo": "Pago digitado dos veces"}, headers=ADMIN)
    assert client.get(f"/facturas/{f['id_factura']}", headers=CAJA).json()["saldo"] == 113050


def test_no_anula_factura_con_pagos(client, fake):
    f = hasta_factura(client, fake)
    client.post(f"/facturas/{f['id_factura']}/pagos", json={"monto": 1000}, headers=CAJA)
    assert client.patch(f"/facturas/{f['id_factura']}/anular", json={"motivo": "Error en factura"},
                        headers=ADMIN).status_code == 400


# ---------- Reportes ----------
def test_reportes_ingresos_y_cartera(client, fake):
    f = hasta_factura(client, fake)
    url = f"/facturas/{f['id_factura']}/pagos"
    client.post(url, json={"monto": 50000}, headers=CAJA)
    client.post(url, json={"monto": 10000, "metodo": "TRANSFERENCIA", "referencia": "T1"}, headers=CAJA)
    ing = client.get("/reportes/ingresos", headers=CAJA).json()
    assert ing["total"] == 60000 and ing["cantidad_pagos"] == 2
    assert ing["por_metodo"] == {"EFECTIVO": 50000, "TRANSFERENCIA": 10000}
    cart = client.get("/reportes/cartera", headers=CAJA).json()
    assert cart["total_por_cobrar"] == 53050 and cart["facturas"][0]["estado"] == "PARCIAL"
    assert client.get("/reportes/ingresos", headers=TECNICO).status_code == 403


def test_sin_token_401(client):
    assert client.get("/facturas").status_code == 401
