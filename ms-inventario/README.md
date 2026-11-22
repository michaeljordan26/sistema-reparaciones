# MS5 – Inventario y repuestos

Quinto microservicio. Registra repuestos, consulta existencias, registra entradas, salidas,
devoluciones y ajustes, descuenta los repuestos usados en una reparación y reporta el stock bajo.

- Puerto: **8005**
- Base de datos propia: **db_inventario** (PostgreSQL, puerto 5436 en tu PC)
- Tablas: `repuesto`, `movimiento_inventario` (kardex)
- **Depende de:** ms-ordenes (8003) para validar la orden al sacar repuestos.

## Cómo se evita el stock negativo (tres capas)

| Capa | Dónde | Qué hace |
|---|---|---|
| 1. Validación | `services/inventario_service.py` → `_mover()` | Si el resultado quedaría < 0, responde 400 "Stock insuficiente" |
| 2. Bloqueo de fila | `SELECT ... FOR UPDATE` | Si dos técnicos piden la última unidad al mismo tiempo, el segundo espera al primero y después ve el stock ya descontado |
| 3. Restricción en la base | `CHECK (stock_actual >= 0)` | Aunque alguien escriba SQL a mano, PostgreSQL rechaza el valor negativo |

**Prueba de concurrencia realizada:** 10 peticiones simultáneas pidieron 1 unidad de un repuesto
con stock 2. Resultado: 2 respuestas 201, 8 respuestas 400 y stock final 0.

## Kardex

El stock **no se edita directamente** (el `PUT` lo ignora). Cada cambio crea un
`movimiento_inventario` con `stock_anterior` y `stock_resultante`, el usuario, la fecha y el motivo.
Los movimientos nunca se borran: el stock se puede reconstruir sumando el kardex.

| Tipo | Efecto | Quién | Regla |
|---|---|---|---|
| ENTRADA | + | Admin, inventario | Puede actualizar el precio de costo |
| SALIDA | − | Admin, inventario, técnico | La orden debe existir y estar **EN_REPARACION** (el presupuesto ya fue aprobado). Guarda el precio de venta del momento |
| DEVOLUCION | + | Admin, inventario, técnico | No se puede devolver más de lo que salió para esa orden |
| AJUSTE_POSITIVO / AJUSTE_NEGATIVO | ± | Admin, inventario | Motivo obligatorio (conteo físico, daño, pérdida) |

## Ejecutar en Windows (modo desarrollo)

```powershell
cd C:\Users\MAICOL\sistema-reparaciones
docker compose up -d db-inventario

cd ms-inventario
py -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
venv\Scripts\python.exe -m alembic upgrade head
venv\Scripts\python.exe -m app.seed
venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8005
```

O simplemente `reiniciar-datos.bat` + `iniciar.bat`, que ya incluyen este servicio.

## Endpoints

| Método | Ruta | Quién |
|---|---|---|
| POST | /repuestos | Admin, inventario |
| GET | /repuestos (`?buscar=`, `?categoria=`, `?stock_bajo=true`) | Autenticado |
| GET | /repuestos/stock-bajo | Autenticado (reporte) |
| GET / PUT | /repuestos/{id} | Consultar: autenticado. Editar: admin, inventario |
| POST | /repuestos/{id}/entradas | Admin, inventario |
| POST | /repuestos/{id}/salidas | Admin, inventario, técnico |
| POST | /repuestos/{id}/devoluciones | Admin, inventario, técnico |
| POST | /repuestos/{id}/ajustes | Admin, inventario |
| GET | /repuestos/{id}/movimientos | Autenticado (kardex) |
| GET | /movimientos (`?id_orden=`, `?tipo=`) | Autenticado |
| GET | /ordenes/{id}/consumo | Autenticado (lo usará ms-facturacion para el valor de materiales) |

## Datos de prueba

8 repuestos. **SSD-NVME-1TB** y **TECL-HP-15** quedan en stock bajo para mostrar el reporte.

## Pruebas

```powershell
venv\Scripts\python.exe -m pytest -v
```
