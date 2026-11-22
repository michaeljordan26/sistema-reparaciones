from tests.conftest import headers

CLIENTE = {"tipo_documento": "CC", "numero_documento": "1012345678", "nombres": "María",
           "apellidos": "Rodríguez", "telefono": "3001234567", "correo": "Maria@Correo.com"}


def crear_cliente(client, **cambios):
    return client.post("/clientes", json={**CLIENTE, **cambios}, headers=headers())


def equipo(id_cliente, serie="pf3abc12"):
    return {"id_cliente": id_cliente, "tipo_equipo": "PORTATIL", "marca": "Lenovo",
            "modelo": "IdeaPad 3", "numero_serie": serie, "descripcion": "No enciende"}


# ---------- Seguridad ----------
def test_sin_token_401(client):
    assert client.get("/clientes").status_code == 401


def test_token_expirado_401(client):
    assert client.get("/clientes", headers=headers(minutos=-1)).status_code == 401


def test_token_con_otra_clave_401(client):
    import jwt
    falso = jwt.encode({"sub": "1", "roles": ["ADMINISTRADOR"]}, "clave-falsa", algorithm="HS256")
    assert client.get("/clientes", headers={"Authorization": f"Bearer {falso}"}).status_code == 401


def test_tecnico_no_puede_registrar_cliente(client):
    assert client.post("/clientes", json=CLIENTE, headers=headers("TECNICO")).status_code == 403


def test_tecnico_si_puede_consultar(client):
    crear_cliente(client)
    assert client.get("/clientes", headers=headers("TECNICO")).status_code == 200


# ---------- Clientes ----------
def test_registrar_cliente(client):
    r = crear_cliente(client)
    assert r.status_code == 201
    assert r.json()["correo"] == "maria@correo.com"   # se normaliza a minúsculas


def test_documento_duplicado_409(client):
    crear_cliente(client)
    assert crear_cliente(client).status_code == 409


def test_mismo_numero_otro_tipo_permitido(client):
    crear_cliente(client)
    assert crear_cliente(client, tipo_documento="CE").status_code == 201


def test_telefono_invalido_422(client):
    assert crear_cliente(client, telefono="abc").status_code == 422


def test_buscar_cliente(client):
    crear_cliente(client)
    crear_cliente(client, numero_documento="999999", nombres="Pedro", apellidos="Gil")
    r = client.get("/clientes", params={"buscar": "rodr"}, headers=headers())
    assert [c["nombres"] for c in r.json()] == ["María"]


def test_actualizar_cliente(client):
    id_c = crear_cliente(client).json()["id_cliente"]
    r = client.put(f"/clientes/{id_c}", json={"telefono": "3115550000"}, headers=headers())
    assert r.json()["telefono"] == "3115550000"


def test_cliente_inexistente_404(client):
    assert client.get("/clientes/999", headers=headers()).status_code == 404


def test_solo_admin_desactiva(client):
    id_c = crear_cliente(client).json()["id_cliente"]
    assert client.patch(f"/clientes/{id_c}/desactivar", headers=headers()).status_code == 403
    r = client.patch(f"/clientes/{id_c}/desactivar", headers=headers("ADMINISTRADOR"))
    assert r.json()["estado"] == "INACTIVO"
    # Ya no aparece en la lista de activos, pero sigue existiendo (historial)
    assert client.get("/clientes", headers=headers()).json() == []
    assert client.get(f"/clientes/{id_c}", headers=headers()).status_code == 200


# ---------- Equipos ----------
def test_registrar_equipo_y_listar_por_cliente(client):
    id_c = crear_cliente(client).json()["id_cliente"]
    r = client.post("/equipos", json=equipo(id_c), headers=headers())
    assert r.status_code == 201 and r.json()["numero_serie"] == "PF3ABC12"
    client.post("/equipos", json=equipo(id_c, "OTRASERIE1"), headers=headers())
    assert len(client.get(f"/clientes/{id_c}/equipos", headers=headers()).json()) == 2


def test_equipo_cliente_inexistente_404(client):
    assert client.post("/equipos", json=equipo(999), headers=headers()).status_code == 404


def test_serie_duplicada_409(client):
    id_c = crear_cliente(client).json()["id_cliente"]
    client.post("/equipos", json=equipo(id_c), headers=headers())
    assert client.post("/equipos", json=equipo(id_c, " PF3ABC12 "), headers=headers()).status_code == 409


def test_no_registra_equipo_a_cliente_inactivo(client):
    id_c = crear_cliente(client).json()["id_cliente"]
    client.patch(f"/clientes/{id_c}/desactivar", headers=headers("ADMINISTRADOR"))
    assert client.post("/equipos", json=equipo(id_c), headers=headers()).status_code == 400


def test_detalle_equipo_incluye_cliente(client):
    id_c = crear_cliente(client).json()["id_cliente"]
    id_e = client.post("/equipos", json=equipo(id_c), headers=headers()).json()["id_equipo"]
    r = client.get(f"/equipos/{id_e}", headers=headers("TECNICO"))
    assert r.json()["cliente"]["numero_documento"] == "1012345678"


def test_buscar_equipo_por_serie(client):
    id_c = crear_cliente(client).json()["id_cliente"]
    client.post("/equipos", json=equipo(id_c), headers=headers())
    assert len(client.get("/equipos", params={"numero_serie": "abc"}, headers=headers()).json()) == 1


def test_tipo_equipo_invalido_422(client):
    id_c = crear_cliente(client).json()["id_cliente"]
    assert client.post("/equipos", json={**equipo(id_c), "tipo_equipo": "NEVERA"}, headers=headers()).status_code == 422
