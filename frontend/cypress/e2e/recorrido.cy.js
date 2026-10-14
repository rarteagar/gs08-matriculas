// Recorrido principal de extremo a extremo, de punta a punta y con limpieza:
// entrar → panel → buscar (sin tildes) → dar de alta un estudiante → matricularlo →
// registrarle tres notas → ver la boleta → dar de baja lo creado.
//
// Necesita credenciales en el entorno y el stack levantado (docker compose up -d):
//   CYPRESS_usuario=admin CYPRESS_clave=… npm run e2e
describe('Recorrido principal del sistema', () => {
  const marca = Date.now().toString().slice(-6)
  const codigo = `E2E${marca}`
  const dni = `9${marca}`.slice(0, 8)
  const periodo = '2026-02'
  const fecha = new Date().toISOString().slice(0, 10)

  function irA(seccion) {
    cy.contains('nav a', seccion, { timeout: 10000 }).click()
  }

  before(() => {
    cy.iniciarSesion()
  })

  beforeEach(() => {
    cy.sinDialogosNativos()
  })

  it('1. el panel muestra los indicadores del servicio', () => {
    cy.contains('h1', 'Panel')
    cy.contains('Estudiantes activos')
    cy.contains('Cursos activos')
    cy.contains('Matrículas activas')
    cy.contains('Usuarios activos')
    cy.contains('Cursos con más matrículas')
  })

  it('2. el buscador encuentra sin distinguir mayúsculas ni tildes', () => {
    irA('Estudiantes')
    cy.get('#buscar').clear().type('huaman')
    cy.contains('button', 'Buscar').click()
    cy.contains('table.tabla tbody tr', 'Huamán', { timeout: 10000 })
  })

  it('3. da de alta un estudiante y lo deja en la lista', () => {
    irA('Estudiantes')
    cy.get('#codigo').type(codigo)
    cy.get('#dni').type(dni)
    cy.get('#nombres').type('PRUEBA EXTREMO A EXTREMO')
    cy.get('#apellidos').type('CYPRESS')
    cy.contains('button', 'Registrar').click()
    cy.contains('registrado', { timeout: 10000 })
    cy.get('#buscar').clear().type(codigo)
    cy.contains('button', 'Buscar').click()
    cy.contains('table.tabla tbody tr', codigo, { timeout: 10000 }).should('exist')
  })

  it('4. matricula al estudiante en un curso', () => {
    irA('Matrículas')
    cy.get('#estudiante option').contains(codigo).then(($opcion) => {
      cy.get('#estudiante').select($opcion.val())
    })
    cy.get('#curso option:not([disabled])').first().then(($opcion) => {
      cy.get('#curso').select($opcion.val())
    })
    cy.get('#periodo').clear().type(periodo)
    cy.get('#fecha').type(fecha)
    cy.contains('button', 'Matricular').click()
    cy.contains('registrada', { timeout: 10000 })
    cy.filaCon(codigo).should('exist')
  })

  it('5. registra tres notas (14, 16 y 18) y la nota del curso queda en 16.00', () => {
    irA('Matrículas')
    cy.filaCon(codigo).within(() => cy.contains('button', 'Notas').click())
    const notas = [['practica', '14'], ['parcial', '16'], ['final', '18']]
    notas.forEach(([tipo, valor]) => {
      cy.get('#tipo').select(tipo)
      cy.get('#numero').clear().type('1')
      cy.get('#nota').clear().type(valor)
      cy.contains('button', 'Registrar nota').click()
      cy.contains('Nota registrada', { timeout: 10000 })
    })
    cy.get('[role="dialog"] table.tabla tbody tr').should('have.length', 3)
    cy.contains('button', 'Cerrar').click()
  })

  it('6. la boleta del estudiante muestra la nota y el promedio ponderado', () => {
    irA('Estudiantes')
    cy.get('#buscar').clear().type(codigo)
    cy.contains('button', 'Buscar').click()
    cy.filaCon(codigo).within(() => cy.contains('button', 'Boleta').click())
    cy.get('[role="dialog"]', { timeout: 10000 }).within(() => {
      cy.contains('16.00')
      cy.contains('Promedio ponderado')
    })
    cy.contains('button', 'Cerrar').click()
  })

  it('7. deja el sistema como estaba: borra la matrícula y el estudiante de prueba', () => {
    irA('Matrículas')
    cy.filaCon(codigo).within(() => cy.contains('button', 'Eliminar').click())
    cy.contains('button', 'Sí, eliminar').click()
    cy.contains('eliminada', { timeout: 10000 })
    cy.contains('table.tabla tbody tr', codigo).should('not.exist')

    irA('Estudiantes')
    cy.get('#buscar').clear().type(codigo)
    cy.contains('button', 'Buscar').click()
    cy.filaCon(codigo).within(() => cy.contains('button', 'Eliminar').click())
    cy.contains('button', 'Sí, eliminar').click()
    cy.contains('eliminado', { timeout: 10000 })
    cy.contains('table.tabla tbody tr', codigo).should('not.exist')
  })
})
