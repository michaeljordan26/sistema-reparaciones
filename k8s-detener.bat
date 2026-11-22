@echo off
REM Borra el despliegue de Kubernetes (namespace "taller"): pods, servicios y discos de las bases.
REM Los datos de Docker Compose NO se tocan; son independientes.
cd /d %~dp0
echo Esto borra el sistema de Kubernetes y sus datos de prueba.
choice /m "Continuar"
if errorlevel 2 exit /b 0
kubectl delete namespace taller
echo Listo. Para volver a desplegarlo:  k8s-iniciar.bat
pause
