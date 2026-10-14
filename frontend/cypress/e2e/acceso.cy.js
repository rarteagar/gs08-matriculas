// Pantalla de acceso: no necesita credenciales reales para probarse.
describe('Acceso al sistema', () => {
  beforeEach(() => {
    cy.sinDialogosNativos()
    cy.visit('/login')
  })

  it('muestra el formulario de acceso', () => {
    cy.contains('h1', 'Iniciar sesión')
    cy.get('#usuario').should('be.visible')
    cy.get('#password').should('have.attr', 'type', 'password')
    cy.contains('button', 'Entrar').should('be.enabled')
  })

  it('rechaza credenciales incorrectas mostrando el mensaje del backend, sin diálogos nativos', () => {
    cy.get('#usuario').type('admin')
    cy.get('#password').type('clave-que-no-corresponde', { log: false })
    cy.contains('button', 'Entrar').click()
    cy.get('[role="alert"]', { timeout: 10000 }).should('be.visible').and('not.be.empty')
    cy.location('pathname').should('eq', '/login')
  })

  it('no deja entrar a una pantalla interna sin sesión', () => {
    cy.visit('/estudiantes')
    cy.location('pathname').should('eq', '/login')
    cy.visit('/usuarios')
    cy.location('pathname').should('eq', '/login')
  })
})
