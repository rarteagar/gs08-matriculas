@echo off
setlocal
title GS08 - Matriculas y Notas
cd /d "%~dp0"

echo ============================================================
echo    GS08 - Matriculas y Notas
echo    Sistema academico de demostracion
echo ============================================================
echo.

where docker >nul 2>nul
if errorlevel 1 goto SIN_DOCKER

docker info >nul 2>nul
if errorlevel 1 (
  echo [!] Docker esta instalado pero no esta iniciado.
  echo     Abre Docker Desktop, espera a que diga "Engine running"
  echo     y vuelve a ejecutar este archivo.
  goto FIN
)

echo [1/3] Construyendo y levantando el sistema...
echo       La primera vez tarda 3 a 5 minutos. Ten paciencia.
docker compose up -d --build
if errorlevel 1 (
  echo.
  echo [!] Algo fallo al levantar el sistema. Ultimas lineas del registro:
  docker compose logs --tail 40
  goto FIN
)

echo.
echo [2/3] Esperando a que la aplicacion responda...
set /a intento=0
:ESPERA
set /a intento+=1
curl -sf -o nul http://localhost:8080/api/v1/health
if not errorlevel 1 goto LISTO
if %intento% GEQ 60 (
  echo [!] La aplicacion no respondio en 3 minutos.
  echo     Revisa el detalle con:  docker compose logs --tail 60
  goto FIN
)
set /a resto=%intento% %% 10
if %resto%==0 echo       ... esperando (%intento% de 60)
ping -n 4 127.0.0.1 >nul
goto ESPERA

:LISTO
echo.
echo [3/3] Listo. Abriendo el navegador...
start "" http://localhost:8080
echo.
echo ------------------------------------------------------------
echo   Direccion:   http://localhost:8080
echo   Usuario:     admin
echo   Contrasena:  Admin123!
echo ------------------------------------------------------------
echo.
echo   Recorrido sugerido (5 minutos):
echo     1. Inicia sesion con el usuario y la contrasena de arriba.
echo     2. Panel: los cuatro indicadores.
echo     3. Estudiantes: busca "huaman" y aparece "Huaman" con tilde.
echo     4. Matriculas: crea una, agrega tres notas y abre la boleta.
echo     5. Auditoria (solo admin): la bitacora de cada operacion.
echo.
echo   Para detener el sistema ejecuta:  detener.bat
goto FIN

:SIN_DOCKER
echo [!] No se encontro Docker en este equipo.
echo.
echo     Instala Docker Desktop (gratis), reinicia si te lo pide y
echo     vuelve a ejecutar este archivo:
echo     https://www.docker.com/products/docker-desktop/
start "" https://www.docker.com/products/docker-desktop/

:FIN
echo.
pause
