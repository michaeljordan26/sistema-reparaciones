# Sprint 7 – Replicación de PostgreSQL

`db-facturacion` (primaria, puerto 5437) se replica en `db-facturacion-replica` (solo lectura, puerto **5440**)
con **replicación por streaming** de PostgreSQL 16.

1. La primaria acepta conexiones de replicación (`pg_hba.conf` de esta carpeta, línea `host replication`).
2. La réplica, la primera vez, copia la primaria con `pg_basebackup -R -X stream`. La opción `-R` crea
   `standby.signal` y guarda en `postgresql.auto.conf` cómo conectarse a la primaria.
3. Desde ahí, cada cambio que se confirma en la primaria (el WAL) se envía a la réplica en milisegundos.

Se eligió `db_facturacion` porque tiene el dinero del taller: una copia en otro servidor protege frente
a la pérdida de la primaria, y los reportes pesados se pueden leer de la réplica sin cargar la base que
registra los pagos.

## Demostración

Con Docker Compose encendido, doble clic en **`replica-demo.bat`**:

| Paso | Qué se ve |
|---|---|
| 1 | `pg_stat_replication` en la primaria: la réplica conectada en estado `streaming` |
| 2 | `pg_is_in_recovery() = t` en la réplica y el retraso (milisegundos) |
| 3 | El mismo número de pagos y el mismo total en las dos bases |
| 4 | `ERROR: cannot execute UPDATE in a read-only transaction` al intentar escribir en la réplica |

En DBeaver: nueva conexión PostgreSQL, puerto **5440**, base `db_facturacion`, usuario `taller`.

## Si la réplica no arranca

```bat
docker compose logs db-facturacion-replica
```

Para empezar la réplica de cero (vuelve a copiar la primaria):

```bat
docker compose rm -sf db-facturacion-replica
docker volume rm sistema-reparaciones_pgdata-facturacion-replica
docker compose up -d db-facturacion-replica
```
