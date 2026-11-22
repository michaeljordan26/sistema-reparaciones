@echo off
REM Sprint 6: despliega todo el sistema en el Kubernetes de Docker Desktop.
REM Requisitos: Docker Desktop con Kubernetes activado y el archivo .env en esta carpeta.
REM Cierra antes iniciar.bat y docker-iniciar.bat (consumen la misma memoria).
cd /d %~dp0

kubectl config use-context docker-desktop >nul 2>&1
if errorlevel 1 (
  echo ERROR: no se encontro el Kubernetes de Docker Desktop.
  echo Activalo en Docker Desktop: Settings - Kubernetes - Enable Kubernetes.
  pause
  exit /b 1
)
kubectl get nodes >nul 2>&1
if errorlevel 1 (
  echo ERROR: Kubernetes todavia no responde. Espera a que el icono de Kubernetes este en verde.
  pause
  exit /b 1
)
if not exist .env (
  echo ERROR: falta el archivo .env. Ejecuta:  copy .env.example .env
  pause
  exit /b 1
)

echo.
echo [1/4] Construyendo las 8 imagenes (la primera vez tarda varios minutos)...
for %%S in (ms-usuarios ms-clientes ms-ordenes ms-reparaciones ms-inventario ms-facturacion ms-reportes frontend) do (
  echo     - taller/%%S:1.0
  docker build -q -t taller/%%S:1.0 %%S >nul
  if errorlevel 1 goto :error_build
)

echo.
echo [2/4] Creando el namespace y el Secret con las claves del .env...
kubectl apply -f k8s\00-namespace.yaml
kubectl create secret generic taller-secretos -n taller --from-env-file=.env --dry-run=client -o yaml | kubectl apply -f -
if errorlevel 1 goto :error

echo.
echo [3/4] Aplicando los manifiestos de la carpeta k8s...
kubectl apply -f k8s\
if errorlevel 1 goto :error

echo.
echo [4/4] Esperando a que los 8 Deployments esten disponibles (hasta 10 minutos)...
kubectl wait --for=condition=available deployment --all -n taller --timeout=600s
kubectl get pods -n taller -o wide

echo.
echo Listo. Abriendo http://localhost:30173 ...
start "" http://localhost:30173
echo.
echo Comandos utiles:
echo   kubectl get pods -n taller
echo   kubectl scale deployment ms-ordenes --replicas=3 -n taller
echo   kubectl logs -f deployment/ms-ordenes -n taller
echo   k8s-detener.bat
pause
exit /b 0

:error_build
echo ERROR al construir una imagen (el mensaje esta arriba). Prueba primero:  docker compose build
pause
exit /b 1

:error
echo ERROR. Revisa el mensaje de arriba.
pause
exit /b 1
