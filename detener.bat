@echo off
setlocal
title GS08 - detener
cd /d "%~dp0"

echo Deteniendo el sistema...
docker compose down

echo.
echo Listo. Los datos se conservan en los volumenes de Docker
echo (no se borro nada). Para volver a levantarlo: ejecutar.bat
echo.
pause
