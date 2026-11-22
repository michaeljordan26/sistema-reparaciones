@echo off
REM Levanta las bases de datos en Docker y abre una ventana por microservicio.
cd /d %~dp0

echo Levantando bases de datos...
docker compose up -d db-usuarios db-clientes db-ordenes db-reparaciones db-inventario db-facturacion db-reportes
if errorlevel 1 (
  echo ERROR: no se pudo iniciar Docker. Abre Docker Desktop y vuelve a intentar.
  pause
  exit /b 1
)
timeout /t 5 >nul

call :abrir "MS1 Usuarios :8001" ms-usuarios 8001
call :abrir "MS2 Clientes :8002" ms-clientes 8002
call :abrir "MS3 Ordenes  :8003" ms-ordenes  8003
call :abrir "MS4 Reparaciones :8004" ms-reparaciones 8004
call :abrir "MS5 Inventario :8005" ms-inventario 8005
call :abrir "MS6 Facturacion :8006" ms-facturacion 8006
call :abrir "MS7 Reportes :8007" ms-reportes 8007

if not exist frontend\node_modules (
  echo Instalando las dependencias de la interfaz - solo la primera vez...
  pushd frontend
  call npm install
  popd
)
start "Interfaz :5173" cmd /k "cd frontend && npm run dev"

echo Listo. Se abrieron 8 ventanas. Abriendo el navegador...
timeout /t 8 >nul
start "" http://localhost:5173
timeout /t 3 >nul
exit /b 0

:abrir
set PY=python
if exist %2\venv\Scripts\python.exe set PY=venv\Scripts\python.exe
start %1 cmd /k "cd %2 && %PY% -m uvicorn app.main:app --reload --port %3"
exit /b 0
