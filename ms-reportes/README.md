# MS7 – Reportes, notificaciones y auditoría

Séptimo y último microservicio. No tiene un flujo propio: **observa a los otros seis**.

- Puerto: **8007**
- Base de datos propia: **db_reportes** (PostgreSQL, puerto 5438 en tu PC)
- Tablas: `registro_auditoria`, `notificacion`
- **Lee de:** ms-clientes, ms-ordenes, ms-reparaciones, ms-inventario y ms-facturacion (solo GET).

## 1. Auditoría centralizada

Cada microservicio tiene el archivo `app/core/auditoria.py` (idéntico en todos) y lo activa con
dos líneas en su `main.py`. Es un **middleware**: intercepta cada petición POST, PUT, PATCH o DELETE
y, cuando termina, envía a MS7 un evento con:

| Campo | Ejemplo |
|---|---|
| servicio | ms-facturacion |
| acción legible | Registrar pago |
| ruta | /facturas/1/pagos |
| recurso afectado | 1 (de la ruta, o el id creado leído de la respuesta) |
| código y éxito | 201, exitosa / 403, acceso denegado |
| usuario y roles | 5, CAJA (leídos del token) |
| IP y duración | 127.0.0.1, 34 ms |

Decisiones de diseño:

- **No bloquea:** el envío se hace en un hilo aparte. Si MS7 está apagado, la operación funciona igual.
- **No guarda contraseñas:** nunca se envía el cuerpo de la petición.
- **No se puede falsificar:** el evento va firmado con un token de servicio (rol `SERVICIO`).
  Un usuario, aunque sea administrador, recibe 403 si intenta registrar un evento, y un servicio
  no puede firmar eventos a nombre de otro.
- **No se puede alterar:** un trigger de PostgreSQL (`tg_auditoria_inmutable`) rechaza cualquier
  `UPDATE` o `DELETE` sobre `registro_auditoria`, incluso por SQL directo:

  ```
  ERROR: La auditoría no se puede modificar ni borrar (operación DELETE bloqueada)
  ```

Para desactivarla en un servicio: `AUDITORIA_URL=` (vacío) en su `.env`.

## 2. Notificaciones al cliente (envío simulado)

Cuando MS7 recibe un evento exitoso de ms-ordenes (orden creada o cambio de estado), consulta la
orden en MS3 y el cliente en MS2 y genera el mensaje:

| Estado | Mensaje |
|---|---|
| RECIBIDO | Recibimos su equipo |
| ESPERANDO_APROBACION | El diagnóstico está listo; hay un presupuesto para aprobar |
| EN_REPARACION | Gracias por aprobar; su equipo está en reparación |
| LISTO_ENTREGA | Su equipo está listo para recoger |
| ENTREGADO | Equipo entregado; recuerde la garantía |
| CANCELADO | La orden fue cancelada |

Canal: CORREO si el cliente tiene correo; si no, SMS al teléfono. El envío es **simulado**
(se registra como ENVIADA). Para hacerlo real bastaría con conectar un servicio de correo en
`notificacion_service.generar()`. Una restricción `UNIQUE (id_orden, tipo)` evita duplicados.
Si MS2 no responde, la notificación queda FALLIDA y se puede reenviar.

Para consultar MS3 y MS2 por su cuenta, MS7 usa un **token de sistema** de 2 minutos firmado con
la clave compartida.

## 3. Reportes

Usan el token del usuario que consulta, así cada servicio sigue aplicando sus permisos.

| Ruta | Contenido | Quién |
|---|---|---|
| /reportes/ordenes | Pendientes (por prioridad), finalizadas, por estado, carga por técnico, días promedio hasta la entrega | Admin, recepción |
| /reportes/finanzas | Ingresos por método de pago y cartera (pagos pendientes) | Admin, caja |
| /reportes/inventario | Repuestos con stock bajo y valor del inventario | Admin, inventario |
| /reportes/garantias | Vigentes, por vencer en 15 días, reclamaciones abiertas | Admin, recepción |
| /reportes/panel | Todo lo anterior más el resumen de auditoría | Admin |

El **panel tolera fallos**: si un servicio está caído, solo esa sección dice `disponible: false`
y las demás se muestran normalmente.

## Endpoints

| Método | Ruta | Quién |
|---|---|---|
| POST | /auditoria/eventos | Solo microservicios |
| GET | /auditoria (`servicio`, `id_usuario`, `metodo`, `solo_fallidos`, `desde`, `hasta`, `limite`, `desplazamiento`) | Admin |
| GET | /auditoria/resumen (`?horas=24`) | Admin |
| GET | /notificaciones (`id_orden`, `id_cliente`, `estado`) | Admin, recepción |
| POST | /notificaciones/ordenes/{id} | Admin, recepción (reenvío) |
| GET | /reportes/... | Ver tabla anterior |

## Ejecutar en Windows (modo desarrollo)

```bat
cd C:\Users\MAICOL\sistema-reparaciones\ms-reportes
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

Luego `reiniciar-datos.bat` y `iniciar.bat`.

## Pruebas

```bat
venv\Scripts\python.exe -m pytest -v
```

Incluye pruebas del middleware de auditoría (`tests/test_middleware.py`) con una app de ejemplo.
