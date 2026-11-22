from datetime import date, timedelta
from app.core.tiempo import hoy

from app.models import Garantia
from tests.conftest import ADMIN, ANDREA, CARLOS, RECEPCION, TestingSession

DIAG = {"id_orden": 1, "hallazgos": "No carga, el jack DC está flojo", "causa_probable": "Jack de carga dañado",
        "solucion_propuesta": "Reemplazar el jack DC", "requiere_repuestos": True, "tiempo_estimado_horas": 1.5}
FIN = {"actividades_realizadas": "Se reemplazó el jack DC y se probó la carga", "resultado": "EXITOSA"}


def diagnosticar(client, h=CARLOS):
    return client.post("/diagnosticos", json=DIAG, headers=h)


def preparar_reparacion(client, fake):
    """Diagnóstico + aprobación (simulada) + reparación iniciada. Devuelve id_reparacion."""
    diagnosticar(client)
    fake.ordenes[1]["estado_actual"] = "EN_REPARACION"   # MS6 / recepción aprobó el presupuesto
    return client.post("/reparaciones", json={"id_orden": 1}, headers=CARLOS).json()["id_reparacion"]


# ---------- Diagnóstico ----------
def test_diagnostico_mueve_orden_a_espera(client, fake):
    r = diagnosticar(client)
    assert r.status_code == 201 and r.json()["id_tecnico"] == 1
    assert fake.ordenes[1]["estado_actual"] == "ESPERANDO_APROBACION"


def test_diagnostico_duplicado_409(client, fake):
    diagnosticar(client)
    fake.ordenes[1]["estado_actual"] = "EN_DIAGNOSTICO"
    assert diagnosticar(client).status_code == 409


def test_diagnostico_orden_en_otro_estado_400(client):
    assert client.post("/diagnosticos", json={**DIAG, "id_orden": 2}, headers=ADMIN).status_code == 400


def test_diagnostico_orden_inexistente_400(client):
    assert client.post("/diagnosticos", json={**DIAG, "id_orden": 99}, headers=ADMIN).status_code == 400


def test_tecnico_no_asignado_403(client):
    assert diagnosticar(client, ANDREA).status_code == 403


def test_recepcionista_no_diagnostica_403(client):
    assert diagnosticar(client, RECEPCION).status_code == 403


def test_si_ordenes_falla_no_se_guarda_diagnostico(client, fake):
    fake.ordenes_caidas = True
    assert diagnosticar(client).status_code == 503
    assert client.get("/ordenes/1/diagnostico", headers=ADMIN).status_code == 404
    fake.ordenes_caidas = False
    assert diagnosticar(client).status_code == 201   # se puede reintentar


# ---------- Reparación ----------
def test_no_repara_sin_diagnostico(client, fake):
    fake.ordenes[1]["estado_actual"] = "EN_REPARACION"
    assert client.post("/reparaciones", json={"id_orden": 1}, headers=CARLOS).status_code == 400


def test_no_repara_sin_aprobacion(client):
    diagnosticar(client)   # queda en ESPERANDO_APROBACION
    r = client.post("/reparaciones", json={"id_orden": 1}, headers=CARLOS)
    assert r.status_code == 400 and "EN_REPARACION" in r.json()["detail"]


def test_usar_repuesto_descuenta_stock(client, fake):
    id_rep = preparar_reparacion(client, fake)
    r = client.post(f"/reparaciones/{id_rep}/repuestos", json={"id_repuesto": 1, "cantidad": 2}, headers=CARLOS)
    assert r.status_code == 201
    assert fake.stock[1] == 3
    assert r.json()["total_repuestos"] == 70000 and r.json()["repuestos"][0]["codigo"] == "JACK-DC"


def test_stock_insuficiente_se_propaga(client, fake):
    id_rep = preparar_reparacion(client, fake)
    r = client.post(f"/reparaciones/{id_rep}/repuestos", json={"id_repuesto": 1, "cantidad": 9}, headers=CARLOS)
    assert r.status_code == 400 and "Stock insuficiente" in r.json()["detail"]
    assert fake.stock[1] == 5


def test_quitar_repuesto_lo_devuelve(client, fake):
    id_rep = preparar_reparacion(client, fake)
    d = client.post(f"/reparaciones/{id_rep}/repuestos", json={"id_repuesto": 1, "cantidad": 2}, headers=CARLOS).json()
    id_ru = d["repuestos"][0]["id_repuesto_utilizado"]
    r = client.delete(f"/reparaciones/{id_rep}/repuestos/{id_ru}", headers=CARLOS)
    assert r.json()["repuestos"] == [] and fake.stock[1] == 5


def test_finalizar_crea_garantia_y_orden_lista(client, fake):
    id_rep = preparar_reparacion(client, fake)
    r = client.post(f"/reparaciones/{id_rep}/finalizar", json={**FIN, "garantia_dias": 60}, headers=CARLOS)
    d = r.json()
    assert r.status_code == 200 and d["estado"] == "FINALIZADA" and d["fecha_fin"]
    assert d["garantia"]["dias"] == 60 and d["garantia"]["estado"] == "VIGENTE"
    assert fake.ordenes[1]["estado_actual"] == "LISTO_ENTREGA"


def test_garantia_por_defecto_90_dias(client, fake):
    id_rep = preparar_reparacion(client, fake)
    d = client.post(f"/reparaciones/{id_rep}/finalizar", json=FIN, headers=CARLOS).json()
    assert d["garantia"]["dias"] == 90


def test_no_reparable_sin_garantia(client, fake):
    id_rep = preparar_reparacion(client, fake)
    d = client.post(f"/reparaciones/{id_rep}/finalizar", json={**FIN, "resultado": "NO_REPARABLE"},
                    headers=CARLOS).json()
    assert d["garantia"] is None


def test_no_modifica_reparacion_finalizada(client, fake):
    id_rep = preparar_reparacion(client, fake)
    client.post(f"/reparaciones/{id_rep}/finalizar", json=FIN, headers=CARLOS)
    r = client.post(f"/reparaciones/{id_rep}/repuestos", json={"id_repuesto": 1, "cantidad": 1}, headers=CARLOS)
    assert r.status_code == 400


def test_resumen_de_la_orden(client, fake):
    id_rep = preparar_reparacion(client, fake)
    client.post(f"/reparaciones/{id_rep}/finalizar", json=FIN, headers=CARLOS)
    d = client.get("/ordenes/1/resumen", headers=RECEPCION).json()
    assert d["diagnostico"] and d["reparacion"]["estado"] == "FINALIZADA" and d["garantia"]["id_cliente"] == 9


# ---------- Garantías y reclamaciones ----------
def garantia_lista(client, fake):
    id_rep = preparar_reparacion(client, fake)
    return client.post(f"/reparaciones/{id_rep}/finalizar", json=FIN, headers=CARLOS).json()["garantia"]["id_garantia"]


def test_reclamacion_y_resolucion(client, fake):
    id_g = garantia_lista(client, fake)
    url = f"/garantias/{id_g}/reclamaciones"
    r = client.post(url, json={"descripcion": "Volvió a fallar la carga"}, headers=RECEPCION)
    assert r.status_code == 201 and r.json()["estado"] == "ABIERTA"
    assert client.post(url, json={"descripcion": "Otra reclamación más"}, headers=RECEPCION).status_code == 409
    id_rec = r.json()["id_reclamacion"]
    assert client.patch(f"/reclamaciones/{id_rec}", json={"estado": "APROBADA", "respuesta": "Se repara sin costo"},
                        headers=RECEPCION).status_code == 403
    r2 = client.patch(f"/reclamaciones/{id_rec}", json={"estado": "APROBADA", "respuesta": "Se repara sin costo"},
                      headers=ADMIN)
    assert r2.json()["estado"] == "APROBADA"


def test_no_reclama_garantia_vencida(client, fake):
    id_g = garantia_lista(client, fake)
    s = TestingSession()
    g = s.get(Garantia, id_g)
    g.fecha_inicio, g.fecha_fin = hoy() - timedelta(days=100), hoy() - timedelta(days=10)
    s.commit()
    s.close()
    r = client.post(f"/garantias/{id_g}/reclamaciones", json={"descripcion": "Falla después de meses"},
                    headers=RECEPCION)
    assert r.status_code == 400 and "VENCIDA" in r.json()["detail"]
    assert len(client.get("/garantias", params={"estado": "VENCIDA"}, headers=ADMIN).json()) == 1


def test_anular_garantia(client, fake):
    id_g = garantia_lista(client, fake)
    assert client.patch(f"/garantias/{id_g}/anular", json={"motivo": "Equipo abierto por terceros"},
                        headers=ADMIN).json()["estado"] == "ANULADA"
    assert client.post(f"/garantias/{id_g}/reclamaciones", json={"descripcion": "Quiero reclamar esto"},
                       headers=RECEPCION).status_code == 400


def test_sin_token_401(client):
    assert client.get("/garantias").status_code == 401
