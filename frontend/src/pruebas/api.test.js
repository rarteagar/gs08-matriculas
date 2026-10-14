import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { api, pedir } from '../api'

// El cliente del API: arma la consulta, manda el token y traduce los errores.
describe('cliente del API', () => {
  beforeEach(() => {
    localStorage.clear()
    global.fetch = vi.fn()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('arma la ruta con los parámetros y descarta los vacíos', async () => {
    global.fetch.mockResolvedValue({ ok: true, status: 200, text: async () => '{"total":0}' })
    await pedir('/estudiantes', { parametros: { q: 'huaman', page: 2, estado: '' } })
    const url = global.fetch.mock.calls[0][0]
    expect(url).toContain('/estudiantes?')
    expect(url).toContain('q=huaman')
    expect(url).toContain('page=2')
    expect(url).not.toContain('estado=')
  })

  it('manda el token de la sesión en la cabecera', async () => {
    localStorage.setItem('gs08.token', 'token-de-prueba')
    global.fetch.mockResolvedValue({ ok: true, status: 200, text: async () => '{}' })
    await api.panel()
    expect(global.fetch.mock.calls[0][1].headers.Authorization).toBe('Bearer token-de-prueba')
  })

  it('usa el mensaje del backend cuando la respuesta falla', async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      status: 409,
      text: async () => '{"detail":"Ya existe una matrícula para ese estudiante y curso en el periodo."}',
    })
    await expect(api.crearMatricula({})).rejects.toThrow(
      'Ya existe una matrícula para ese estudiante y curso en el periodo.',
    )
  })

  it('explica el 403 como falta de permiso del rol', async () => {
    global.fetch.mockResolvedValue({ ok: false, status: 403, text: async () => '' })
    await expect(api.usuarios()).rejects.toThrow('Tu rol no tiene permiso para esta operación.')
  })

  it('olvida la sesión vencida cuando el API responde 401', async () => {
    localStorage.setItem('gs08.token', 'token-vencido')
    global.fetch.mockResolvedValue({
      ok: false,
      status: 401,
      text: async () => '{"detail":"La sesión expiró. Vuelve a iniciar sesión."}',
    })
    await expect(api.panel()).rejects.toThrow('La sesión expiró. Vuelve a iniciar sesión.')
    expect(localStorage.getItem('gs08.token')).toBeNull()
  })

  it('no borra la sesión cuando el 401 viene del propio acceso', async () => {
    localStorage.setItem('gs08.token', 'token-de-otra-sesion')
    global.fetch.mockResolvedValue({
      ok: false,
      status: 401,
      text: async () => '{"detail":"Usuario o clave incorrectos."}',
    })
    await expect(api.login('admin', 'mala')).rejects.toThrow('Usuario o clave incorrectos.')
    expect(localStorage.getItem('gs08.token')).toBe('token-de-otra-sesion')
  })

  it('cubre las operaciones del contrato que usa el SPA (31 métodos)', () => {
    // El contrato expone /health y /api/v1/health con la misma operación, así que el
    // cliente cubre 31 métodos distintos y ninguna ruta que el SPA use queda sin consumir.
    const operaciones = Object.values(api)
    expect(operaciones).toHaveLength(31)
    operaciones.forEach((operacion) => expect(typeof operacion).toBe('function'))

    const esperadas = [
      'login',
      'yo',
      'panel',
      'estudiantes',
      'crearEstudiante',
      'editarEstudiante',
      'eliminarEstudiante',
      'boleta',
      'boletaArchivada',
      'cursos',
      'crearCurso',
      'editarCurso',
      'eliminarCurso',
      'matriculas',
      'crearMatricula',
      'editarMatricula',
      'eliminarMatricula',
      'notas',
      'registrarNota',
      'editarNota',
      'eliminarNota',
      'usuarios',
      'crearUsuario',
      'editarUsuario',
      'eliminarUsuario',
      'auditoria',
    ]
    esperadas.forEach((nombre) => expect(api[nombre]).toBeTypeOf('function'))
  })
})
