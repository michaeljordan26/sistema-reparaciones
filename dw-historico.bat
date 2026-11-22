@echo off
REM Sprint 7 - Paso unico: genera 6 meses de historia SIMULADA usando la API real.
REM Requisito: el sistema encendido con Docker (docker-iniciar.bat). Tarda 2 a 4 minutos.
cd /d %~dp0dw

if not exist venv\Scripts\python.exe (
  echo Creando el entorno virtual de dw\ - solo la primera vez...
  python -m venv venv
  venv\Scripts\python.exe -m pip install -q -r requirements.txt
  if errorlevel 1 (
    echo ERROR instalando las librerias. Revisa tu conexion a internet.
    pause
    exit /b 1
  )
)

venv\Scripts\python.exe generar_historico.py
if errorlevel 1 (
  pause
  exit /b 1
)
echo.
echo Historia generada. Ahora ejecuta dw-etl.bat para cargar el Data Warehouse.
pause
