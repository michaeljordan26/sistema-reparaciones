@echo off
REM Apaga los contenedores. Los datos se conservan (volúmenes).
REM Para borrar también los datos:  docker compose down -v
cd /d %~dp0
docker compose down
echo Contenedores detenidos. Los datos se conservan.
pause
