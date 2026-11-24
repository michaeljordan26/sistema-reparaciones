# Scripts SQL (Sprint 4 · Base transaccional)

## ddl/ — definición de las tablas
Generados con `alembic upgrade head --sql`; son la misma definición que las migraciones.
Con Docker o con `reiniciar-datos.bat` NO hace falta ejecutarlos: los servicios crean las tablas solos.

| Archivo | Base | Puerto |
|---|---|---|
| 00_crear_bases.sql | (servidor, como postgres) | — |
| 01_db_usuarios.sql | db_usuarios | 5432 |
| 02_db_clientes.sql | db_clientes | 5433 |
| 03_db_ordenes.sql | db_ordenes | 5434 |
| 04_db_reparaciones.sql | db_reparaciones | 5435 |
| 05_db_inventario.sql | db_inventario | 5436 |
| 06_db_facturacion.sql | db_facturacion | 5437 |
| 07_db_reportes.sql | db_reportes | 5438 |

## dml/ — ejemplos para DBeaver
INSERT, SELECT con JOIN y GROUP BY, UPDATE, DELETE, transacciones y violaciones de
restricciones. Los cambios terminan en ROLLBACK: se pueden ejecutar muchas veces.

En DBeaver: abra el script, elija la conexión de su base y pulse Alt+X.
Los mensajes de las restricciones aparecen en la pestaña "Salida".
