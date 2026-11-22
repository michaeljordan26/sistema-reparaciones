@echo off
REM Levanta TODO el sistema en Docker: 7 bases de datos, 7 microservicios y la interfaz.
REM Cierra antes las ventanas de iniciar.bat (usan los mismos puertos).
cd /d %~dp0

docker info >nul 2>&1
if errorlevel 1 (
  echo ERROR: Docker no esta encendido. Abre Docker Desktop y espera a que diga Engine running.
  pause
  exit /b 1
)

echo Construyendo y levantando los contenedores.
echo La primera vez tarda varios minutos porque descarga imagenes e instala dependencias...
docker compose up --build -d
if errorlevel 1 (
  echo.
  echo ERROR al levantar los contenedores. Revisa el mensaje de arriba.
  pause
  exit /b 1
)

echo.
echo Esperando a que los servicios terminen de arrancar...
timeout /t 20 >nul
docker compose ps
echo.
echo Abriendo http://localhost:5173 ...
start "" http://localhost:5173
echo Para ver los registros de un servicio:  docker compose logs -f ms-ordenes
echo Para apagar todo:                       docker-detener.bat
pause
