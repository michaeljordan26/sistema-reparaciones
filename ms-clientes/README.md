# MS2 – Clientes y Equipos

Segundo microservicio del sistema. Cubre CU07–CU10: registrar, consultar y actualizar
clientes y los equipos que entregan para servicio.

- Puerto: **8002**
- Base de datos propia: **db_clientes** (PostgreSQL, puerto 5433 en tu PC)
- Tablas: `cliente`, `equipo` (1:N)

## ¿Cómo sabe quién es el usuario si no tiene tabla de usuarios?

Este servicio **no guarda usuarios ni contraseñas**. El usuario inicia sesión en
ms-usuarios (8001), que le entrega un token JWT firmado. MS2 verifica la firma de ese
token con la misma `JWT_SECRET_KEY` y lee de él el id y los roles.
Por eso la clave debe ser **idéntica** en los `.env` de ambos servicios.

## Ejecutar en Windows (modo desarrollo)

```powershell
# Desde sistema-reparaciones: base de datos de este servicio
docker compose up -d db-clientes

cd ms-clientes
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8002
```

Abrir http://127.0.0.1:8002/docs

**Para autorizarte en Swagger:** inicia sesión en http://127.0.0.1:8001/docs
(`POST /auth/login`), copia el `access_token` y pégalo en el botón **Authorize** de MS2.

## Permisos

| Operación | Roles |
|---|---|
| Registrar / actualizar cliente o equipo | ADMINISTRADOR, RECEPCIONISTA |
| Consultar clientes y equipos | Cualquier usuario autenticado |
| Desactivar / reactivar cliente | ADMINISTRADOR |

## Reglas de negocio aplicadas

- **RN01**: tipo + número de documento únicos (restricción en la base de datos).
- **RN02**: cada equipo pertenece a un solo cliente; un cliente puede tener varios.
- El número de serie es único y se guarda en mayúsculas sin espacios.
- No se registran equipos a clientes inactivos.
- **RN13**: los clientes no se eliminan, se desactivan; así se conserva el historial.

## Endpoints

| Método | Ruta |
|---|---|
| POST / GET | /clientes (`?buscar=` por documento, nombre o teléfono) |
| GET / PUT | /clientes/{id} |
| GET | /clientes/{id}/equipos |
| PATCH | /clientes/{id}/desactivar, /clientes/{id}/activar |
| POST / GET | /equipos (`?numero_serie=`, `?id_cliente=`) |
| GET / PUT | /equipos/{id} (el GET incluye el cliente; lo usará ms-ordenes) |
| GET | /health |

## Pruebas

```powershell
pytest -v
```

> El historial de servicios del equipo (CU11) se agrega cuando exista ms-ordenes.
