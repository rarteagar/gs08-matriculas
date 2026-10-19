# Cómo ejecutar la web en tu computadora

**GS08 · Matrículas y Notas — guía rápida para el docente**

Este paquete permite ejecutar el sistema completo (interfaz, API y bases de datos) en tu propia
computadora, sin depender de internet ni de un servidor. Lo que ves es el mismo sistema que está
publicado en línea.

## Requisitos

| Qué | Detalle |
|---|---|
| Sistema operativo | Windows 10 u 11 (también funciona en macOS o Linux con Docker) |
| Docker Desktop | Instalado y **abierto** (es gratis). Descarga: https://www.docker.com/products/docker-desktop/ |
| Memoria | 4 GB libres |
| Tiempo | La primera ejecución tarda entre 3 y 5 minutos; las siguientes, menos de un minuto |

## Pasos

1. **Instala Docker Desktop** si aún no lo tienes. Ábrelo y espera a que la esquina inferior izquierda
   diga **Engine running**.
2. **Descomprime el ZIP** en una carpeta, por ejemplo `Escritorio\gs08-matriculas`.
3. **Doble clic en `ejecutar.bat`**. El archivo construye y levanta el sistema, espera a que responda y
   abre el navegador solo.
4. Si el navegador no se abre, entra manualmente a **http://localhost:8080**.

## Acceso

| Campo | Valor |
|---|---|
| Usuario | `admin` (o `admin@horizonte.edu.pe`) |
| Contraseña | `Admin123!` |

Son las credenciales de demostración del sistema, con datos ficticios del instituto.

## Recorrido sugerido (5 minutos)

1. **Panel**: los cuatro indicadores (estudiantes, cursos, matrículas activas y usuarios).
2. **Estudiantes**: busca `huaman` y comprueba que encuentra *Huamán* (el buscador ignora tildes y mayúsculas).
3. **Matrículas**: crea una matrícula y abre el diálogo de **notas**: registra tres notas y mira la **boleta**
   con el promedio ponderado por créditos.
4. **Cursos** y **Usuarios**: alta, edición y baja lógica; los borrados piden confirmación.
5. **Auditoría** (solo administrador): la bitácora de cada operación, guardada en la base documental, y la
   consulta de una boleta archivada.
6. **API**: abre http://localhost:8000/docs (Swagger) o http://localhost:8000/graphql (GraphiQL).

## Para detenerlo

Doble clic en **`detener.bat`**. Los datos se conservan: al volver a ejecutar `ejecutar.bat` todo sigue
como lo dejaste. Si quieres empezar de cero, borra el volumen con `docker compose down -v`.

## Si algo falla

| Síntoma | Solución |
|---|---|
| «Docker está instalado pero no está iniciado» | Abre Docker Desktop y espera a *Engine running*; vuelve a ejecutar `ejecutar.bat` |
| «No se encontró Docker» | Instálalo desde el enlace de arriba y reinicia la computadora si te lo pide |
| El puerto 8080 está ocupado | Crea un archivo `.env` junto a `docker-compose.yml` con la línea `WEB_PORT=8090` y entra a http://localhost:8090 |
| Quieres ver qué pasó | En la carpeta del proyecto: `docker compose logs --tail 60` |

## Si prefieres no instalar nada

El sistema también está publicado en **https://gs08-matriculas.mlarca.com** (disponible hasta el
02/11/2026, con las mismas credenciales). La ventaja de ejecutarlo en tu equipo es que funciona sin
conexión y puedes probar los borrados y altas sin afectar la demo publicada.
