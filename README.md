# Sistema de gestión de reparación de equipos de cómputo

Proyecto de Bases de Datos Avanzadas – Universidad Central.
Arquitectura de microservicios con FastAPI, PostgreSQL (una base por servicio), JWT y Docker Compose.

| # | Microservicio | Puerto API | Puerto BD | Estado |
|---|---|---|---|---|
| 1 | ms-usuarios – Usuarios y autenticación | 8001 | 5432 | 
| 2 | ms-clientes – Clientes y equipos | 8002 | 5433 | 
| 3 | ms-ordenes – Órdenes de trabajo | 8003 | 5434 | 
| 4 | ms-reparaciones – Diagnósticos, reparaciones y garantías | 8004 | 5435 | 
| 5 | ms-inventario – Inventario y repuestos | 8005 | 5436 | 
| 6 | ms-facturacion – Presupuestos, facturación y pagos | 8006 | 5437 | 
| 7 | ms-reportes – Reportes, notificaciones y auditoría | 8007 | 5438 | 

| — | **frontend – Interfaz web (React + Bootstrap)** | **5173** | — | 

Abrir la aplicación en **http://localhost:5173** (usuarios de prueba: `admin / Admin123*`,
`recepcion / Recepcion123*`, `tecnico1 / Tecnico123*`, `caja / Caja1234*`, `inventario / Inventario123*`).

## Modo desarrollo en Windows

- `iniciar.bat`: levanta las bases en Docker, abre una ventana por microservicio y otra para la interfaz, y abre el navegador.
- `reiniciar-datos.bat`: borra todos los datos y los vuelve a crear con datos de prueba.

Orden sugerido para las colecciones de Postman: MS1, MS2, MS3, MS5, MS4, MS6 y MS7.

## Levantar todo con Docker

Con Docker Desktop encendido, doble clic en **`docker-iniciar.bat`** (o `docker compose up --build -d`).
Levanta 17 contenedores: 7 bases de datos, la réplica de db-facturacion, 7 microservicios, el Data Warehouse (db-dw) y la interfaz (nginx)
en **http://localhost:5173**. Cada microservicio aplica sus migraciones y carga sus datos de prueba al arrancar.

| Comando | Para qué |
|---|---|
| `docker compose ps` | Ver el estado de los 17 contenedores |
| `docker compose logs -f ms-ordenes` | Ver los registros de un servicio |
| `docker-detener.bat` / `docker compose down` | Apagar (conserva los datos) |
| `docker compose down -v` | Apagar y **borrar** todos los datos |

No mezcles este modo con `iniciar.bat`: usan los mismos puertos (5173 y 8001-8007).

## Desplegar en Kubernetes (Sprint 6)

Con Kubernetes activado en Docker Desktop, doble clic en **`k8s-iniciar.bat`**. Construye las imágenes,
crea el Secret desde `.env` y aplica los manifiestos de `k8s/`. Abre **http://localhost:30173**.
Para borrarlo: `k8s-detener.bat`. Detalles y comandos de demostración en [`k8s/README.md`](k8s/README.md).

## Data Warehouse, ETL y Power BI (Sprints 7 y 8)

Con Docker Compose encendido: `dw-historico.bat` (una sola vez, crea 6 meses de historia simulada) y luego
`dw-etl.bat` (carga el Data Warehouse `db_dw`, puerto 5439, modelo en estrella). El tablero de Power BI se
conecta a esa base. Paso a paso en [`dw/README.md`](dw/README.md).

Replicación: `db-facturacion` se replica en `db-facturacion-replica` (solo lectura, puerto 5440). Demostración con
`replica-demo.bat`; detalles en [`replicacion/README.md`](replicacion/README.md).
