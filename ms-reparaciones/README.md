# MS4 – Diagnósticos, reparaciones y garantías

Cuarto microservicio. Registra el diagnóstico del técnico, la reparación con los repuestos usados,
y las garantías con sus reclamaciones.

- Puerto: **8004**
- Base de datos propia: **db_reparaciones** (PostgreSQL, puerto 5435 en tu PC)
- Tablas: `diagnostico`, `reparacion`, `repuesto_utilizado`, `garantia`, `reclamacion_garantia`
- **Depende de:** ms-usuarios (8001), ms-ordenes (8003) y ms-inventario (8005).

## Qué hace con los otros servicios

| Acción en MS4 | Llamada a otro servicio |
|---|---|
| Registrar diagnóstico | MS3: verifica que la orden esté EN_DIAGNOSTICO y la pasa a **ESPERANDO_APROBACION** |
| Iniciar reparación | MS3: exige que la orden esté **EN_REPARACION** (presupuesto aprobado) |
| Usar repuesto | MS5: `POST /repuestos/{id}/salidas` → descuenta stock |
| Quitar repuesto | MS5: `POST /repuestos/{id}/devoluciones` → devuelve stock |
| Finalizar reparación | MS3: pasa la orden a **LISTO_ENTREGA**; se crea la garantía |
| Saber qué técnico soy | MS1: `GET /auth/validar` → `id_tecnico` |

## Consistencia entre bases de datos (patrón SAGA)

Una operación como "usar un repuesto" cambia **dos bases**: `db_inventario` (stock) y
`db_reparaciones` (repuesto utilizado). No existe una transacción que abarque las dos, así que:

1. Se valida todo primero (orden, estado, técnico).
2. Se ejecuta el paso remoto (MS5 descuenta el stock; él mismo valida y bloquea la fila).
3. Se guarda el registro local.
4. Si el paso 3 falla, se ejecuta una **compensación**: MS4 pide a MS5 una devolución.

En el diagnóstico es al revés: se guarda localmente sin confirmar (`flush`), se cambia el
estado en MS3, y si MS3 falla se hace `rollback`. Así nunca queda un diagnóstico sin que la
orden haya avanzado.

## Reglas de negocio

| Regla | Cómo se aplica |
|---|---|
| Un diagnóstico por orden | `UNIQUE (id_orden)` |
| No se repara sin diagnóstico | 400 al iniciar la reparación |
| No se repara sin aprobación | La orden debe estar EN_REPARACION |
| El técnico solo trabaja sus órdenes | Se compara su `id_tecnico` (MS1) con la asignación activa (MS3); el admin puede todo |
| No se modifica una reparación finalizada | 400 al agregar o quitar repuestos |
| Garantía automática | Al finalizar: 90 días por defecto (`GARANTIA_DIAS_DEFECTO`), configurable; 0 = sin garantía |
| Sin garantía si no se reparó | Resultado NO_REPARABLE → no se crea garantía |
| Estado de la garantía | Calculado por fecha: VIGENTE / VENCIDA; o ANULADA por el admin |
| Reclamar solo si está vigente | 400 si está vencida o anulada |
| Una reclamación abierta a la vez | Índice único parcial `WHERE estado = 'ABIERTA'` |
| Resolver reclamaciones | Solo el administrador |

## Ejecutar en Windows (modo desarrollo)

```bat
cd C:\Users\MAICOL\sistema-reparaciones\ms-reparaciones
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

Luego `reiniciar-datos.bat` y `iniciar.bat` (ya incluyen este servicio).

## Endpoints

| Método | Ruta | Quién |
|---|---|---|
| POST | /diagnosticos | Técnico asignado, admin |
| GET | /ordenes/{id}/diagnostico | Autenticado |
| POST | /reparaciones | Técnico asignado, admin |
| GET | /reparaciones/{id} | Autenticado |
| POST | /reparaciones/{id}/repuestos | Técnico asignado, admin |
| DELETE | /reparaciones/{id}/repuestos/{id_repuesto_utilizado} | Técnico asignado, admin |
| POST | /reparaciones/{id}/finalizar | Técnico asignado, admin |
| GET | /ordenes/{id}/resumen | Autenticado |
| GET | /garantias (`?estado=VIGENTE|VENCIDA|ANULADA`, `id_cliente`, `id_equipo`) | Autenticado |
| GET | /garantias/{id} | Autenticado |
| PATCH | /garantias/{id}/anular | Admin |
| POST | /garantias/{id}/reclamaciones | Recepción, admin |
| PATCH | /reclamaciones/{id} | Admin |

## Datos de prueba

No tiene datos propios: se generan al recorrer el flujo. La colección de Postman crea una orden
nueva para la impresora Epson (equipo 3) y la lleva de principio a fin.

## Pruebas

```bat
venv\Scripts\python.exe -m pytest -v
```

Las pruebas simulan MS1, MS3 y MS5, incluido el caso de "ms-ordenes caído": el diagnóstico
no se guarda y se puede reintentar.
