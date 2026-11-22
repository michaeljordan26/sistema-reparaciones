@echo off
REM Sprint 7 - ETL: lleva los datos de las 7 bases de los microservicios al Data Warehouse (db_dw).
REM Se puede ejecutar cuantas veces se quiera (carga completa). Requisito: docker-iniciar.bat
cd /d %~dp0

docker compose up -d db-dw >nul 2>&1
cd dw
if not exist venv\Scripts\python.exe (
  echo Creando el entorno virtual de dw\ - solo la primera vez...
  python -m venv venv
  venv\Scripts\python.exe -m pip install -q -r requirements.txt
)

REM Espera a que db-dw acepte conexiones
set /a intentos=0
:esperar
docker exec db-dw pg_isready -q >nul 2>&1
if not errorlevel 1 goto lista
set /a intentos+=1
if %intentos% geq 30 goto sin_dw
timeout /t 2 >nul
goto esperar

:sin_dw
echo ERROR: db-dw no responde. Revisa: docker compose ps
pause
exit /b 1

:lista
venv\Scripts\python.exe etl.py
echo.
echo Para ver el resultado: DBeaver, puerto 5439, base db_dw  (SELECT * FROM vw_indicadores;)
pause
