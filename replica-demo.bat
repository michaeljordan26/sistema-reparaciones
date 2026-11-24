@echo off
REM Sprint 7 - Demostracion de la replicacion de PostgreSQL (db-facturacion -> db-facturacion-replica)
REM Requisito: docker-iniciar.bat (los 17 contenedores encendidos)
cd /d %~dp0
set PSQL_P=docker exec db-facturacion psql -U taller -d db_facturacion -P pager=off
set PSQL_R=docker exec db-facturacion-replica psql -U taller -d db_facturacion -P pager=off

echo.
echo === 1. La PRIMARIA ve a su replica conectada (streaming) ===
%PSQL_P% -c "SELECT client_addr AS replica, state, sync_state, replay_lag FROM pg_stat_replication;"

echo === 2. La REPLICA esta en modo recuperacion (solo lectura) ===
%PSQL_R% -c "SELECT pg_is_in_recovery() AS es_replica, now() - pg_last_xact_replay_timestamp() AS retraso;"

echo === 3. Los mismos datos en las dos ===
%PSQL_P% -t -c "SELECT 'Primaria: ' || count(*) || ' pagos, ' || coalesce(sum(monto),0) || ' pesos' FROM pago WHERE NOT anulado;"
%PSQL_R% -t -c "SELECT 'Replica:  ' || count(*) || ' pagos, ' || coalesce(sum(monto),0) || ' pesos' FROM pago WHERE NOT anulado;"

echo === 4. Escribir en la REPLICA no esta permitido ===
%PSQL_R% -c "UPDATE pago SET monto = 0 WHERE id_pago = 1;"

echo.
echo Para ver un cambio en vivo: registra un pago en la aplicacion y vuelve a ejecutar este archivo.
pause
