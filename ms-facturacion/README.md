# MS6 – Presupuestos, facturación y pagos

Sexto microservicio. Elabora el presupuesto (materiales + mano de obra + IVA), registra la
aprobación o el rechazo del cliente, genera la factura, recibe pagos y abonos y calcula saldos.
**ms-ordenes le pregunta a este servicio** antes de reparar (¿hay presupuesto aprobado?) y antes
de entregar (¿el saldo es 0?).

- Puerto: **8006**
- Base de datos propia: **db_facturacion** (PostgreSQL, puerto 5437 en tu PC)
- Tablas: `presupuesto`, `detalle_presupuesto`, `respuesta_presupuesto`, `factura`, `detalle_factura`, `pago`
- **Depende de:** ms-ordenes (8003) e ms-inventario (8005).

## Flujo del dinero

```
Orden ESPERANDO_APROBACION
   │  POST /presupuestos  (mano de obra + repuestos con precio de MS5 + IVA 19 %)
   ▼
Presupuesto PENDIENTE (válido 15 días)
   │  POST /presupuestos/{id}/respuesta
   ├── APROBADO  → MS3: orden EN_REPARACION
   └── RECHAZADO → MS3: orden LISTO_ENTREGA (se devuelve sin reparar y sin cobro)
                                   ⋮ (MS4 repara y usa repuestos en MS5)
Orden LISTO_ENTREGA
   │  POST /facturas  (mano de obra presupuestada + repuestos REALMENTE usados según MS5)
   ▼
Factura PENDIENTE ─abono─► PARCIAL ─pago final─► PAGADA ─► MS3 permite ENTREGADO
```

## Reglas de negocio

| Regla | Cómo se aplica |
|---|---|
| Presupuesto solo con la orden ESPERANDO_APROBACION | 400 en otro estado |
| Un presupuesto vigente por orden | Índice único parcial `WHERE estado IN ('PENDIENTE','APROBADO')` |
| Al menos una línea de mano de obra | 422 si no hay |
| Totales consistentes | `CHECK (total = subtotal + iva)` y `CHECK (subtotal = round(cantidad * precio, 2))` |
| Validez del presupuesto | 15 días (`VALIDEZ_PRESUPUESTO_DIAS`); vencido no se puede aprobar |
| La respuesta del cliente queda registrada | Quién respondió, por qué medio (presencial, teléfono, correo, WhatsApp) y cuándo |
| No reparar sin aprobación | MS3 consulta `GET /ordenes/{id}/presupuesto` y exige APROBADO |
| Factura con lo realmente usado | Los repuestos salen de `GET /ordenes/{id}/consumo` de MS5, no del presupuesto |
| Una factura activa por orden | Índice único parcial `WHERE anulada = false` |
| No pagar de más | 400 si el pago supera el saldo; `SELECT ... FOR UPDATE` evita dos pagos simultáneos |
| Referencia obligatoria | Para tarjeta, transferencia, Nequi y Daviplata |
| No entregar con deuda | MS3 consulta `GET /ordenes/{id}/saldo` antes de ENTREGADO |
| Corrección de errores | Solo el admin anula pagos; una factura solo se anula si no tiene pagos |

**Prueba de concurrencia realizada:** 5 pagos simultáneos por el total de la misma factura.
Resultado: 1 aceptado (201), 4 rechazados (400) y saldo final exactamente 0.

## Consistencia con ms-ordenes (SAGA con compensación)

Al registrar la respuesta del cliente:
1. Se guarda localmente APROBADO o RECHAZADO (se confirma primero porque MS3 lo va a consultar).
2. Se pide a MS3 que mueva la orden.
3. Si MS3 falla, **se compensa**: el presupuesto vuelve a PENDIENTE y se borra la respuesta,
   para que se pueda reintentar.

## Permisos

| Operación | Roles |
|---|---|
| Crear presupuesto | Admin, técnico, recepción, caja |
| Registrar respuesta del cliente | Admin, recepción, caja |
| Generar factura, anular presupuesto, ver reportes | Admin, caja |
| Registrar pagos y abonos | Admin, caja, recepción |
| Anular pagos o facturas | Admin |

## Ejecutar en Windows (modo desarrollo)

```bat
cd C:\Users\MAICOL\sistema-reparaciones\ms-facturacion
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

Luego `reiniciar-datos.bat` y `iniciar.bat` (ya incluyen este servicio).

## Endpoints

| Método | Ruta |
|---|---|
| POST | /presupuestos |
| GET | /presupuestos/{id} |
| GET | /ordenes/{id}/presupuesto (lo usa MS3) |
| POST | /presupuestos/{id}/respuesta |
| PATCH | /presupuestos/{id}/anular |
| POST / GET | /facturas (`?estado=PENDIENTE|PARCIAL|PAGADA|ANULADA`, `?id_orden=`) |
| GET | /facturas/{id} |
| PATCH | /facturas/{id}/anular |
| POST | /facturas/{id}/pagos |
| PATCH | /pagos/{id}/anular |
| GET | /ordenes/{id}/saldo (lo usa MS3) |
| GET | /reportes/ingresos (`?desde=&hasta=`, por defecto los últimos 30 días) |
| GET | /reportes/cartera |

## Pruebas

```bat
venv\Scripts\python.exe -m pytest -v
```
