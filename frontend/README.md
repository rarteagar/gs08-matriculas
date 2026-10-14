# GS08 · Matrículas y Notas — SPA (React)

Interfaz del sistema administrativo del Instituto Privado Horizonte. Consume el API REST
del proyecto (FastAPI + PostgreSQL) y cubre: autenticación, panel, estudiantes (con boleta y
boleta archivada), cursos, matrículas con notas, notas, usuarios y la **bitácora** (auditoría).

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
  api.js                 cliente único del API: sesión, errores y las operaciones que usa el SPA
  App.jsx                cabecera, menú por rol, rutas protegidas y enlace «Saltar al contenido»
  main.jsx               punto de entrada (React + React Router + estilos)
  estilos.css            hoja base: Tailwind, clases de la aplicación y utilidades de accesibilidad
  hooks/
    usePaginado.js       listado paginado contra el API (búsqueda, filtros, páginas)
  componentes/
    Avisos.jsx           mensajes en línea e insignias de estado
    Modal.jsx            diálogo propio (con foco atrapado) y confirmación de operaciones destructivas
    TablaRecurso.jsx     tabla reutilizable con buscador, filtros y paginación
    Boleta.jsx           boleta del estudiante (nota de curso y promedio ponderado)
    Notas.jsx            notas de una matrícula (listar, registrar, editar, eliminar)
    Bitacora.jsx         tabla de la bitácora documental (la alimenta la vista Auditoría)
  vistas/
    Login.jsx            inicio de sesión
    Panel.jsx            indicadores, top de cursos y últimos estudiantes
    Estudiantes.jsx      listado, búsqueda, alta, edición, baja y boleta
    Cursos.jsx           catálogo con créditos y horas
    Matriculas.jsx       matrícula de un estudiante en un curso y periodo
    Usuarios.jsx         cuentas y roles (solo administrador)
    Auditoria.jsx        bitácora de operaciones y boleta archivada (solo administrador)
  pruebas/               pruebas unitarias, de componente y de accesibilidad (vitest + testing-library)
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
- **Marcado accesible (D-30).** Cada campo con su `<label htmlFor>`, los avisos con `role="alert"`
  o `role="status"`, y los diálogos con `role="dialog"`, `aria-modal` y `aria-labelledby`. Además:
  el foco entra al diálogo al abrirlo, **queda atrapado** dentro (Tab y Shift+Tab dan la vuelta) y
  al cerrarse vuelve al botón que lo abrió; Escape cierra; hay un enlace **«Saltar al contenido»**;
  al cambiar de sección el foco va al contenido y la sección se anuncia (`aria-live`); el menú
  marca la sección actual con `aria-current="page"`; las tablas llevan `<caption>` para lectores
  de pantalla y `scope="col"` en las cabeceras; los botones de cada fila dicen a quién afectan
  («Editar a Huamán, María»); los estados de carga usan `aria-busy`; el foco siempre es visible
  (`:focus-visible`) y se respeta `prefers-reduced-motion`.
- **Estilos.** Clases de utilidad de Tailwind en el marcado y las clases propias de la
  aplicación (`tarjeta`, `campo`, `etiqueta`, `boton-primario`, `tabla`, `insignia-*`) más las
  utilidades de accesibilidad (`salto-contenido`, `solo-lectores`) definidas en `estilos.css`;
  no se agregan hojas de estilo nuevas.
- **Componentes.** Un componente por archivo, con `PascalCase`; los ganchos propios con
  `use` + `camelCase`. Los componentes reutilizables viven en `componentes/`, las pantallas
  en `vistas/`.
- **Estado.** Estado local con `useState`/`useEffect`; no se incorporan librerías de estado
  ni de datos mientras el proyecto no lo necesite.

## Pruebas

`npm run test:unit` corre las **25 pruebas** de `src/pruebas/`: el cliente del API (consulta,
token, traducción de errores y el olvido de la sesión cuando el API responde 401), la pantalla de
acceso, los componentes de aviso y confirmación, la pantalla de auditoría (incluido el caso de la
consulta fallida, que **no** debe decir «la bitácora está apagada») y una **batería de accesibilidad** (`accesibilidad.test.jsx`) que pasa
`axe-core` —el mismo motor del addon a11y de Storybook— sobre el formulario de entrada, la tabla
de listado, el diálogo abierto y la lista de estudiantes con datos, y comprueba con teclado que el
foco entra al diálogo, no se escapa con Tab, vuelve al cerrarse con Escape y que el menú marca la
sección actual. En jsdom no se pueden medir colores, así que el contraste se mide aparte contra el
CSS compilado: **14/14 pares de texto cumplen AA (4.5:1)** y el anillo de foco da 5.93:1 (mínimo
3:1 para componentes). Los pares medidos: texto del cuerpo 13.37, tarjeta 14.66, texto secundario
4.77, etiquetas 7.56, encabezado de tabla 4.77, enlace activo 7.05, botón principal 5.85, botón
secundario 10.34, botón de peligro 6.06, aviso de error 5.51, aviso correcto 7.19, insignia activa
6.68, retirado 6.41 e inactivo 8.40.

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
listado (con datos, vacía y cargando), la boleta, las notas de una matrícula y la **bitácora**
(con registros, vacía y cargando). Cada historia trae su documentación automática, y las que
consultan el API usan una respuesta simulada con los datos del seed. `npm run build-storybook`
genera la versión estática en `storybook-static/`.

## Despliegue

La imagen se construye con el `Dockerfile` (etapa de Node que compila y etapa de nginx que
sirve `dist/` y hace de proxy inverso hacia el API). En el VPS, Coolify construye el servicio
`web` a partir de `docker-compose.coolify.yml`; en local, `docker compose up -d --build web`.
El pipeline de CI compila el frontend y publica el paquete como artefacto.
