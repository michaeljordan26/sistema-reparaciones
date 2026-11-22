from tests.conftest import TECNICO, headers

RAM = {"codigo": "ram-ddr4-8gb", "nombre": "Memoria RAM DDR4 8GB", "categoria": "memoria ram",
       "marca": "Kingston", "precio_costo": 85000, "precio_venta": 130000, "stock_minimo": 2, "stock_inicial": 5}


def crear(client, **cambios):
    return client.post("/repuestos", json={**RAM, **cambios}, headers=headers())


def salida(client, id_r, cantidad, id_orden=10, h=None):
    return client.post(f"/repuestos/{id_r}/salidas", json={"cantidad": cantidad, "id_orden": id_orden},
                       headers=h or TECNICO)


# ---------- Repuestos ----------
def test_crear_repuesto_con_stock_inicial(client):
    r = crear(client)
    assert r.status_code == 201
    d = r.json()
    assert d["codigo"] == "RAM-DDR4-8GB" and d["categoria"] == "MEMORIA RAM" and d["stock_actual"] == 5
    kardex = client.get(f"/repuestos/{d['id_repuesto']}/movimientos", headers=headers()).json()
    assert kardex[0]["tipo"] == "ENTRADA" and kardex[0]["stock_resultante"] == 5


def test_codigo_duplicado_409(client):
    crear(client)
    assert crear(client).status_code == 409


def test_precio_negativo_422(client):
    assert crear(client, precio_venta=-1).status_code == 422


def test_tecnico_no_crea_repuestos(client):
    assert client.post("/repuestos", json=RAM, headers=TECNICO).status_code == 403


def test_tecnico_si_consulta_existencias(client):
    crear(client)
    assert len(client.get("/repuestos", headers=TECNICO).json()) == 1


def test_put_no_modifica_stock(client):
    id_r = crear(client).json()["id_repuesto"]
    r = client.put(f"/repuestos/{id_r}", json={"precio_venta": 140000, "stock_actual": 999}, headers=headers())
    assert r.json()["precio_venta"] == 140000 and r.json()["stock_actual"] == 5


# ---------- Entradas y salidas ----------
def test_entrada_suma_stock_y_actualiza_costo(client):
    id_r = crear(client).json()["id_repuesto"]
    r = client.post(f"/repuestos/{id_r}/entradas", json={"cantidad": 10, "costo_unitario": 80000}, headers=headers())
    assert r.status_code == 201 and r.json()["stock_resultante"] == 15
    assert client.get(f"/repuestos/{id_r}", headers=headers()).json()["precio_costo"] == 80000


def test_salida_descuenta_stock(client):
    id_r = crear(client).json()["id_repuesto"]
    r = salida(client, id_r, 2)
    assert r.status_code == 201
    assert r.json()["stock_anterior"] == 5 and r.json()["stock_resultante"] == 3
    assert r.json()["precio_unitario"] == 130000


def test_no_permite_stock_negativo(client):
    id_r = crear(client).json()["id_repuesto"]
    r = salida(client, id_r, 6)
    assert r.status_code == 400 and "Stock insuficiente" in r.json()["detail"]
    assert client.get(f"/repuestos/{id_r}", headers=headers()).json()["stock_actual"] == 5


def test_salida_exacta_deja_cero(client):
    id_r = crear(client).json()["id_repuesto"]
    assert salida(client, id_r, 5).json()["stock_resultante"] == 0


def test_salida_orden_inexistente_400(client):
    id_r = crear(client).json()["id_repuesto"]
    assert salida(client, id_r, 1, id_orden=99).status_code == 400


def test_salida_orden_no_en_reparacion_400(client):
    id_r = crear(client).json()["id_repuesto"]
    assert salida(client, id_r, 1, id_orden=11).status_code == 400
    assert salida(client, id_r, 1, id_orden=12).status_code == 400


def test_cantidad_cero_422(client):
    id_r = crear(client).json()["id_repuesto"]
    assert salida(client, id_r, 0).status_code == 422


def test_recepcionista_no_saca_repuestos(client):
    id_r = crear(client).json()["id_repuesto"]
    assert salida(client, id_r, 1, h=headers("RECEPCIONISTA", 2)).status_code == 403


# ---------- Devoluciones y ajustes ----------
def test_devolucion_limitada_a_lo_usado(client):
    id_r = crear(client).json()["id_repuesto"]
    salida(client, id_r, 2)
    url = f"/repuestos/{id_r}/devoluciones"
    assert client.post(url, json={"cantidad": 3, "id_orden": 10}, headers=TECNICO).status_code == 400
    r = client.post(url, json={"cantidad": 1, "id_orden": 10}, headers=TECNICO)
    assert r.status_code == 201 and r.json()["stock_resultante"] == 4


def test_ajuste_negativo_con_motivo(client):
    id_r = crear(client).json()["id_repuesto"]
    url = f"/repuestos/{id_r}/ajustes"
    assert client.post(url, json={"tipo": "NEGATIVO", "cantidad": 1}, headers=headers()).status_code == 422
    r = client.post(url, json={"tipo": "NEGATIVO", "cantidad": 1, "motivo": "Unidad dañada"}, headers=headers())
    assert r.json()["tipo"] == "AJUSTE_NEGATIVO" and r.json()["stock_resultante"] == 4
    assert client.post(url, json={"tipo": "NEGATIVO", "cantidad": 10, "motivo": "Conteo físico"},
                       headers=headers()).status_code == 400


# ---------- Reportes ----------
def test_stock_bajo(client):
    id_r = crear(client).json()["id_repuesto"]
    crear(client, codigo="PASTA", nombre="Pasta térmica", stock_inicial=20)
    assert client.get("/repuestos/stock-bajo", headers=headers()).json() == []
    salida(client, id_r, 3)   # queda en 2 = mínimo
    bajos = client.get("/repuestos/stock-bajo", headers=headers()).json()
    assert [b["codigo"] for b in bajos] == ["RAM-DDR4-8GB"] and bajos[0]["stock_bajo"] is True


def test_consumo_por_orden(client):
    id_ram = crear(client).json()["id_repuesto"]
    id_pasta = crear(client, codigo="PASTA", nombre="Pasta térmica", precio_venta=30000, stock_inicial=20).json()["id_repuesto"]
    salida(client, id_ram, 2)
    salida(client, id_pasta, 1)
    client.post(f"/repuestos/{id_ram}/devoluciones", json={"cantidad": 1, "id_orden": 10}, headers=TECNICO)
    d = client.get("/ordenes/10/consumo", headers=headers()).json()
    assert d["total_materiales"] == 130000 + 30000
    assert {l["codigo"]: l["cantidad"] for l in d["lineas"]} == {"RAM-DDR4-8GB": 1, "PASTA": 1}


def test_sin_token_401(client):
    assert client.get("/repuestos").status_code == 401
