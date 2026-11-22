@echo off
REM Borra TODOS los datos y los vuelve a crear con los datos de prueba.
REM Cierra antes las ventanas de los microservicios.
cd /d %~dp0

echo Borrando y recreando las bases de datos...
docker compose down -v
docker compose up -d db-usuarios db-clientes db-ordenes db-reparaciones db-inventario db-facturacion db-reportes
if errorlevel 1 (
  echo ERROR: no se pudo iniciar Docker. Abre Docker Desktop y vuelve a intentar.
  pause
  exit /b 1
)

echo Esperando a que PostgreSQL este listo...
:esperar
timeout /t 2 >nul
docker exec db-usuarios pg_isready -U taller -d db_usuarios >nul 2>&1 || goto esperar
docker exec db-clientes pg_isready -U taller -d db_clientes >nul 2>&1 || goto esperar
docker exec db-ordenes  pg_isready -U taller -d db_ordenes  >nul 2>&1 || goto esperar
docker exec db-reparaciones pg_isready -U taller -d db_reparaciones >nul 2>&1 || goto esperar
docker exec db-inventario pg_isready -U taller -d db_inventario >nul 2>&1 || goto esperar
docker exec db-facturacion pg_isready -U taller -d db_facturacion >nul 2>&1 || goto esperar
docker exec db-reportes pg_isready -U taller -d db_reportes >nul 2>&1 || goto esperar
timeout /t 4 >nul

call :migrar ms-usuarios
call :migrar ms-clientes
call :migrar ms-ordenes
call :migrar ms-inventario
call :migrar ms-reparaciones
call :migrar ms-facturacion
call :migrar ms-reportes

echo.
echo ==========================================
echo  Datos reiniciados. Ahora abre iniciar.bat
echo ==========================================
pause
exit /b 0

:migrar
echo.
echo ===== %1 =====
pushd %1
set PY=python
if exist venv\Scripts\python.exe set PY=venv\Scripts\python.exe
%PY% -m alembic upgrade head || echo *** ERROR en la migracion de %1 ***
%PY% -m app.seed || echo *** ERROR cargando datos de %1 ***
popd
exit /b 0
