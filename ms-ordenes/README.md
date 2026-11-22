# MS3 – Órdenes de trabajo

Tercer microservicio. Cubre CU12–CU17 (crear orden, consultar, asignar técnico,
cambiar estado, historial, pendientes y finalizadas) y CU11 (historial de servicios del equipo).

- Puerto: **8003**
- Base de datos propia: **db_ordenes** (PostgreSQL, puerto 5434 en tu PC)
- Tablas: `orden_trabajo`, `historial_estado`, `asignacion`
- **Depende de:** ms-usuarios (8001) y ms-clientes (8002), que deben estar encendidos.

## Comunicación con otros microservicios

```
              token del usuario
Cliente ──► MS3 /ordenes ──GET /equipos/{id}──► MS2  (¿existe el equipo? ¿de qué cliente es?)
                         ──GET /tecnicos/{id}─► MS1  (¿existe el técnico? ¿está ACTIVO?)
                         ──GET /ordenes/{id}/saldo► MS6 (cuando exista: ¿debe dinero?)
```

MS3 reenvía el token del usuario; cada servicio vuelve a revisar los permisos.
Si un servicio está apagado, MS3 responde **503** con un mensaje claro.

`id_equipo`, `id_cliente`, `id_tecnico` e `id_usuario` son **referencias lógicas**:
no son claves foráneas físicas, porque esos datos viven en otras bases de datos.

## Estados de la orden

```
RECIBIDO ──► EN_DIAGNOSTICO ──► ESPERANDO_APROBACION ──► EN_REPARACION ──► LISTO_ENTREGA ──► ENTREGADO
   │               │                    │  └── (presupuesto rechazado) ──────────┘
   └───────────────┴────────────────────┴──► CANCELADO
```

## Reglas de negocio aplicadas

| Regla | Cómo se aplica |
|---|---|
| RN03 | La orden solo se crea si el equipo existe y está activo en MS2 |
| RN04 | No se pasa a diagnóstico ni a reparación sin técnico asignado |
| RN11 / RF15 | Solo se entrega desde LISTO_ENTREGA, solo lo hace recepción/admin y (con MS6) sin saldo pendiente |
| RN13 / RNF05 | Cada cambio queda en `historial_estado` con fecha, usuario y observación; nada se borra |
| RNF10 | Las transiciones de estado inválidas se rechazan con 400 |
| Extra | Un equipo no puede tener dos órdenes abiertas a la vez |
| Extra | Una sola asignación activa por orden (índice único parcial); al reasignar, la anterior queda REASIGNADA |
| Permisos | El técnico solo mueve **sus** órdenes y no puede entregar ni cancelar |

## Ejecutar en Windows (modo desarrollo)

Necesitas **tres terminales** (MS1, MS2 y MS3). En la tercera:

```powershell
cd C:\proyectos\sistema-reparaciones
docker compose up -d db-ordenes

cd ms-ordenes
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8003
```

Abrir http://127.0.0.1:8003/docs, pegar en **Authorize** un token obtenido en el MS1.

## Endpoints

| Método | Ruta | Quién |
|---|---|---|
| GET | /ordenes/estados | Público |
| POST | /ordenes | Admin, recepción |
| GET | /ordenes (`?grupo=pendientes|finalizadas`, `estado`, `id_equipo`, `id_cliente`, `id_tecnico`) | Autenticado |
| GET | /ordenes/mis-ordenes | Técnico (y personal del taller) |
| GET | /ordenes/{id} | Autenticado |
| POST | /ordenes/{id}/asignar | Admin, recepción |
| PATCH | /ordenes/{id}/estado | Admin, recepción, técnico asignado |
| GET | /ordenes/{id}/historial | Autenticado |
| GET | /equipos/{id}/historial | Autenticado (CU11) |

## Pruebas

```powershell
pytest -v
```

Las pruebas **simulan** MS1 y MS2 con `monkeypatch`, así que corren aunque estén apagados.
