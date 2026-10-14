# GS08 · Matrículas y Notas — SPA (React)

Interfaz del sistema administrativo del Instituto Privado Horizonte. Consume el API REST
del proyecto (FastAPI + PostgreSQL) y cubre las 30 operaciones del contrato: autenticación,
panel, estudiantes con boleta, cursos, matrículas con notas, notas y usuarios.

## Cómo se ejecuta

```bash
npm ci                 # instala dependencias (versiones fijadas en package-lock.json)
npm run dev            # servidor de desarrollo en http://localhost:5173
npm run build          # compila a dist/ (lo que se sirve en producción)
npm run lint           # revisión estática con eslint
npm run test:unit      # pruebas con vitest
npm run test:watch     # pruebas en modo vigilante
npm run storybook      # documentación de componentes en http://localhost:6006
npm run build-storybook # compila el Storybook a storybook-static/ (para publicarlo)
npm run e2e            # recorrido completo con cypress (necesita credenciales, ver abajo)
npm run e2e:open       # abre el panel de Cypress para correr las pruebas a mano
```

En desarrollo, `npm run dev` envía `/api` al API local (`http://localhost:8000`) mediante el
proxy de Vite; se puede apuntar a otro servidor con `VITE_API_PROXY`. En producción el SPA lo
sirve nginx en el mismo origen que el API (`/api/v1` → proxy inverso), así que no hay CORS ni
URL absoluta embebida.

## Estructura

```
src/
  api.js                 cliente único del API: sesión, errores y las 30 operaciones
  App.jsx                cabecera, menú por rol y rutas protegidas
  main.jsx               punto de entrada (React + React Router + estilos)
  estilos.css            hoja base: Tailwind y las clases de la aplicación
  hooks/
    usePaginado.js       listado paginado contra el API (búsqueda, filtros, páginas)
  componentes/
    Avisos.jsx           mensajes en línea e insignias de estado
    Modal.jsx            diálogo propio y confirmación de operaciones destructivas
    TablaRecurso.jsx     tabla reutilizable con buscador, filtros y paginación
    Boleta.jsx           boleta del estudiante (nota de curso y promedio ponderado)
    Notas.jsx            notas de una matrícula (listar, registrar, editar, eliminar)
  vistas/
    Login.jsx            inicio de sesión
    Panel.jsx            indicadores, top de cursos y últimos estudiantes
    Estudiantes.jsx      listado, búsqueda, alta, edición, baja y boleta
    Cursos.jsx           catálogo con créditos y horas
    Matriculas.jsx       matrícula de un estudiante en un curso y periodo
    Usuarios.jsx         cuentas y roles (solo administrador)
  pruebas/               pruebas unitarias y de componente (vitest + testing-library)
```

## Convenciones

- **Idioma.** Nombres de variables, funciones, componentes y textos en español; el código
  sigue el mismo vocabulario que el API (`estudiante_id`, `periodo`, `matricula`).
- **Un cliente del API.** Ninguna vista usa `fetch` directamente: todo pasa por `src/api.js`,
  que agrega el token, arma la consulta y traduce los errores del backend a un mensaje.
- **Errores y avisos dentro de la pantalla.** Prohibido `alert`, `confirm` y `prompt`: los
  mensajes van con `Avisos` y las confirmaciones con `Confirmacion`, cuyos botones dicen qué
  hacen («No, volver» / «Sí, eliminar»).
- **Tablas y listados.** Se arma con `TablaRecurso` + `usePaginado` para que la búsqueda,
  los filtros y la paginación se comporten igual en todas las pantallas.
- **Marcado accesible.** Cada campo con su `<label htmlFor>`, los avisos con `role="alert"`
  o `role="status"`, los diálogos con `role="dialog"` y `aria-modal`, y cierre con `Escape`.
- **Estilos.** Clases de utilidad de Tailwind en el marcado y las clases propias de la
  aplicación (`tarjeta`, `campo`, `etiqueta`, `boton-primario`, `tabla`, `insignia-*`)
  definidas en `estilos.css`; no se agregan hojas de estilo nuevas.
- **Componentes.** Un componente por archivo, con `PascalCase`; los ganchos propios con
  `use` + `camelCase`. Los componentes reutilizables viven en `componentes/`, las pantallas
  en `vistas/`.
- **Estado.** Estado local con `useState`/`useEffect`; no se incorporan librerías de estado
  ni de datos mientras el proyecto no lo necesite.

## Pruebas

`npm run test:unit` corre las pruebas de `src/pruebas/`: el cliente del API (consulta, token y
traducción de errores), la pantalla de acceso y los componentes de aviso y confirmación.

`npm run e2e` corre las pruebas de extremo a extremo de `cypress/e2e/` contra el stack
levantado (`docker compose up -d`, el SPA en `http://localhost:8080`):

- `acceso.cy.js`: el formulario de acceso, el rechazo de credenciales incorrectas con el
  mensaje del backend y que ninguna ruta interna se abra sin sesión.
- `recorrido.cy.js`: el recorrido completo — panel, búsqueda sin tildes, alta de estudiante,
  matrícula, tres notas, boleta con promedio ponderado — y la limpieza de lo creado.

**Las credenciales no viven en el repositorio.** Las pruebas que entran al sistema las leen
del entorno:

```bash
CYPRESS_usuario=admin CYPRESS_clave=… npm run e2e
```

Se puede dejar un `cypress.env.json` local con esas dos claves (está ignorado por git) o
exportarlas en la sesión. Ambas pruebas verifican, además, que la aplicación no use diálogos
nativos del navegador: si aparece un `alert`, `confirm` o `prompt`, fallan.

## Documentación de componentes (Storybook)

`npm run storybook` levanta el Storybook en `http://localhost:6006` con las historias de
`src/componentes/*.stories.jsx`: mensajes e insignias, diálogos y confirmaciones, la tabla de
listado (con datos, vacía y cargando), la boleta y las notas de una matrícula. Cada historia
trae su documentación automática, y las que consultan el API usan una respuesta simulada con
los datos del seed. `npm run build-storybook` genera la versión estática en `storybook-static/`.

## Despliegue

La imagen se construye con el `Dockerfile` (etapa de Node que compila y etapa de nginx que
sirve `dist/` y hace de proxy inverso hacia el API). En el VPS, Coolify construye el servicio
`web` a partir de `docker-compose.coolify.yml`; en local, `docker compose up -d --build web`.
El pipeline de CI compila el frontend y publica el paquete como artefacto.
