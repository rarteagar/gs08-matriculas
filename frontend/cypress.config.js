import { defineConfig } from 'cypress'

// Prueba de extremo a extremo del recorrido principal: entrar, panel, buscar un
// estudiante, matricularlo, registrarle notas y ver la boleta.
//
// El SPA se sirve por nginx en el mismo origen que el API, así que basta con
// apuntar baseUrl al stack levantado (`docker compose up -d`):
//
//   CYPRESS_usuario=admin CYPRESS_clave=… npm run e2e
//
// Las credenciales NO viven en el repositorio: se pasan por variables de entorno
// (o por un cypress.env.json local, que está ignorado por git).
export default defineConfig({
  e2e: {
    baseUrl: process.env.CYPRESS_baseUrl || 'http://localhost:8080',
    specPattern: 'cypress/e2e/**/*.cy.js',
    video: false,
    screenshotOnRunFailure: true,
    viewportWidth: 1280,
    viewportHeight: 800,
    setupNodeEvents() {},
  },
})
