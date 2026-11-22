# MS1 – Usuarios y Autenticación

Primer microservicio del **Sistema de gestión de reparación de equipos de cómputo**.
Cubre los casos de uso CU01–CU06 del documento: iniciar sesión, registrar y gestionar usuarios,
asignar roles, registrar técnicos y validar el acceso según el rol.

- Puerto: **8001**
- Base de datos propia: **db_usuarios** (PostgreSQL)
- Tablas: `usuario`, `rol`, `usuario_rol`, `tecnico`

## Estructura

```
ms-usuarios/
├── app/
│   ├── main.py              # Crea la app FastAPI y registra las rutas
│   ├── seed.py              # Datos de prueba (roles y usuarios)
│   ├── core/
│   │   ├── config.py        # Lee variables del archivo .env
│   │   ├── security.py      # Hash bcrypt y tokens JWT
│   │   └── deps.py          # Usuario actual y control de roles (401/403)
│   ├── database/session.py  # Conexión SQLAlchemy a PostgreSQL
│   ├── models/usuario.py    # Tablas (ORM)
│   ├── schemas/usuario.py   # Validaciones Pydantic (entrada/salida)
│   ├── services/            # Reglas de negocio
│   └── routers/             # Endpoints: auth, usuarios, tecnicos
├── alembic/                 # Migraciones de la base de datos
├── tests/                   # Pruebas pytest (usan SQLite en memoria)
├── postman/                 # Colección para importar en Postman
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Ejecutar en Windows (modo desarrollo)

Requisitos: Python 3.12, Docker Desktop abierto.

```powershell
# 1. Desde la carpeta sistema-reparaciones: levantar solo la base de datos
docker compose up -d db-usuarios

# 2. Entrar al microservicio y crear el entorno virtual
cd ms-usuarios
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Crear el archivo .env a partir del ejemplo
copy .env.example .env

# 4. Crear las tablas y cargar datos de prueba
alembic upgrade head
python -m app.seed

# 5. Levantar el servidor
uvicorn app.main:app --reload --port 8001
```

Abrir http://127.0.0.1:8001/docs

## Ejecutar todo con Docker

```powershell
docker compose up --build
```

## Pruebas

```powershell
pytest -v
```

## Usuarios de prueba

| Usuario | Contraseña | Rol |
|---|---|---|
| admin | Admin123* | ADMINISTRADOR |
| recepcion | Recepcion123* | RECEPCIONISTA |
| tecnico1 | Tecnico123* | TECNICO |
| tecnico2 | Tecnico123* | TECNICO |
| caja | Caja1234* | CAJA |
| inventario | Inventario123* | INVENTARIO |

> Son credenciales de demostración. Cámbialas antes de cualquier uso real.

## Endpoints

| Método | Ruta | Quién puede |
|---|---|---|
| POST | /auth/login | Público |
| GET | /auth/me | Autenticado |
| GET | /auth/validar | Autenticado (lo usan los otros microservicios) |
| GET | /roles | Administrador |
| POST / GET | /usuarios | Administrador |
| GET / PUT | /usuarios/{id} | Administrador |
| PATCH | /usuarios/{id}/desactivar | Administrador |
| PUT | /usuarios/{id}/roles | Administrador |
| POST | /tecnicos | Administrador |
| GET | /tecnicos, /tecnicos/{id} | Autenticado |
| PUT | /tecnicos/{id} | Administrador |
| GET | /health | Público |

## ¿Cómo lo usarán los demás microservicios?

Cada microservicio recibirá el token del usuario y llamará a `GET /auth/validar`
(o verificará el JWT con la misma `JWT_SECRET_KEY`) para saber quién es y qué roles tiene.
Así ningún otro servicio guarda contraseñas.
