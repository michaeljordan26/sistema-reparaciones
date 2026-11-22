from tests.conftest import auth_headers, login

NUEVO_TECNICO = {
    "nombres": "Pedro", "apellidos": "López", "correo": "pedro@test.com",
    "nombre_usuario": "pedro", "contrasena": "Pedro1234*", "roles": ["TECNICO"],
}


def test_health(client):
    assert client.get("/health").json()["estado"] == "ok"


def test_login_correcto_devuelve_token(client):
    r = login(client, "admin", "Admin123*")
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"


def test_login_con_correo(client):
    assert login(client, "admin@test.com", "Admin123*").status_code == 200


def test_login_clave_incorrecta(client):
    assert login(client, "admin", "malaclave").status_code == 401


def test_sin_token_responde_401(client):
    assert client.get("/usuarios").status_code == 401


def test_token_falso_responde_401(client):
    assert client.get("/auth/me", headers={"Authorization": "Bearer abc.def.ghi"}).status_code == 401


def test_me_devuelve_roles(client):
    r = client.get("/auth/me", headers=auth_headers(client))
    assert r.json()["roles"][0]["nombre"] == "ADMINISTRADOR"


def test_contrasena_no_se_expone(client):
    r = client.get("/usuarios", headers=auth_headers(client))
    assert "contrasena_hash" not in r.text and "Admin123" not in r.text


def test_admin_crea_usuario(client):
    r = client.post("/usuarios", json=NUEVO_TECNICO, headers=auth_headers(client))
    assert r.status_code == 201
    assert r.json()["roles"][0]["nombre"] == "TECNICO"


def test_usuario_duplicado_409(client):
    h = auth_headers(client)
    client.post("/usuarios", json=NUEVO_TECNICO, headers=h)
    assert client.post("/usuarios", json=NUEVO_TECNICO, headers=h).status_code == 409


def test_contrasena_corta_422(client):
    datos = {**NUEVO_TECNICO, "contrasena": "123"}
    assert client.post("/usuarios", json=datos, headers=auth_headers(client)).status_code == 422


def test_recepcionista_no_puede_crear_usuarios(client):
    h = auth_headers(client, "recepcion", "Recepcion123*")
    assert client.post("/usuarios", json=NUEVO_TECNICO, headers=h).status_code == 403


def test_crear_perfil_tecnico_y_listar(client):
    h = auth_headers(client)
    id_usuario = client.post("/usuarios", json=NUEVO_TECNICO, headers=h).json()["id_usuario"]
    r = client.post("/tecnicos", json={"id_usuario": id_usuario, "especialidad": "Portátiles"}, headers=h)
    assert r.status_code == 201
    # La recepcionista sí puede ver la lista de técnicos (la necesita para asignar órdenes)
    lista = client.get("/tecnicos", headers=auth_headers(client, "recepcion", "Recepcion123*"))
    assert lista.status_code == 200 and len(lista.json()) == 1


def test_tecnico_requiere_rol_tecnico(client):
    h = auth_headers(client)
    r = client.post("/tecnicos", json={"id_usuario": 2, "especialidad": "Redes"}, headers=h)
    assert r.status_code == 400


def test_usuario_desactivado_no_puede_entrar(client):
    h = auth_headers(client)
    assert client.patch("/usuarios/2/desactivar", headers=h).status_code == 200
    assert login(client, "recepcion", "Recepcion123*").status_code == 401


def test_admin_no_se_desactiva_a_si_mismo(client):
    assert client.patch("/usuarios/1/desactivar", headers=auth_headers(client)).status_code == 400


def test_asignar_roles(client):
    r = client.put("/usuarios/2/roles", json={"roles": ["RECEPCIONISTA", "CAJA"]}, headers=auth_headers(client))
    assert {x["nombre"] for x in r.json()["roles"]} == {"RECEPCIONISTA", "CAJA"}


def test_validar_token_para_otros_microservicios(client):
    r = client.get("/auth/validar", headers=auth_headers(client, "recepcion", "Recepcion123*"))
    assert r.status_code == 200 and r.json()["roles"] == ["RECEPCIONISTA"]
