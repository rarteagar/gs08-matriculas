// Comandos compartidos por las pruebas de extremo a extremo.
//
// El recorrido principal exige credenciales, y las credenciales no viven en el
// repositorio: se pasan por variables de entorno (CYPRESS_usuario / CYPRESS_clave).
Cypress.Commands.add('iniciarSesion', () => {
  const usuario = Cypress.env('usuario')
  const clave = Cypress.env('clave')
  if (!usuario || !clave) {
    throw new Error(
      'Faltan las credenciales: corre la prueba así → CYPRESS_usuario=… CYPRESS_clave=… npm run e2e',
    )
  }
  cy.visit('/login')
  cy.get('#usuario').clear().type(usuario)
  cy.get('#password').clear().type(clave, { log: false })
  cy.contains('button', 'Entrar').click()
  cy.location('pathname', { timeout: 10000 }).should('eq', '/')
})

// La aplicación no debe abrir diálogos nativos del navegador: si alguno se
// dispara, la prueba falla con el mensaje del diálogo.
Cypress.Commands.add('sinDialogosNativos', () => {
  cy.window().then((win) => {
    cy.stub(win, 'alert').as('alert').throws('La aplicación no debe usar alert()')
    cy.stub(win, 'confirm').as('confirm').throws('La aplicación no debe usar confirm()')
    cy.stub(win, 'prompt').as('prompt').throws('La aplicación no debe usar prompt()')
  })
})

// Busca la fila de una tabla por un texto y devuelve un envoltorio de Cypress.
Cypress.Commands.add('filaCon', (texto) => {
  return cy.contains('table.tabla tbody tr', texto)
})
