// Cliente del API. Todo pasa por nginx (/api/v1), así que el SPA y el API
// comparten origen y no hay CORS ni URL absoluta embebida.
//
// Cubre las 30 operaciones del contrato (16 rutas): autenticación, panel,
// estudiantes (+ boleta), cursos, matrículas (+ notas), notas y usuarios.
const BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'
const CLAVE_TOKEN = 'gs08.token'
const CLAVE_USUARIO = 'gs08.usuario'

export function token() {
  return localStorage.getItem(CLAVE_TOKEN)
}

export function usuarioGuardado() {
  const crudo = localStorage.getItem(CLAVE_USUARIO)
  return crudo ? JSON.parse(crudo) : null
}

export function guardarSesion(datos) {
  localStorage.setItem(CLAVE_TOKEN, datos.access_token)
  localStorage.setItem(CLAVE_USUARIO, JSON.stringify(datos.usuario))
}

export function cerrarSesion() {
  localStorage.removeItem(CLAVE_TOKEN)
  localStorage.removeItem(CLAVE_USUARIO)
}

function mensajeDeError(datos, estado) {
  if (datos && typeof datos.detail === 'string') return datos.detail
  if (datos && Array.isArray(datos.errores) && datos.errores.length) return datos.errores[0].mensaje
  if (datos && Array.isArray(datos.detail) && datos.detail.length) return datos.detail[0].msg
  if (estado === 403) return 'Tu rol no tiene permiso para esta operación.'
  if (estado === 401) return 'La sesión venció. Vuelve a entrar.'
  return `No se pudo completar la operación (HTTP ${estado}).`
}

function cadenaDe(parametros = {}) {
  const limpios = Object.entries(parametros).filter(
    ([, v]) => v !== '' && v !== null && v !== undefined,
  )
  return new URLSearchParams(limpios).toString()
}

export async function pedir(ruta, { metodo = 'GET', cuerpo, parametros } = {}) {
  const cabeceras = {}
  if (cuerpo !== undefined) cabeceras['Content-Type'] = 'application/json'
  const sesion = token()
  if (sesion) cabeceras.Authorization = `Bearer ${sesion}`

  const consulta = cadenaDe(parametros)
  const respuesta = await fetch(`${BASE}${ruta}${consulta ? `?${consulta}` : ''}`, {
    method: metodo,
    headers: cabeceras,
    body: cuerpo !== undefined ? JSON.stringify(cuerpo) : undefined,
  })
  const texto = await respuesta.text()
  let datos = null
  if (texto) {
    try {
      datos = JSON.parse(texto)
    } catch {
      datos = null
    }
  }
  if (!respuesta.ok) {
    const error = new Error(mensajeDeError(datos, respuesta.status))
    error.estado = respuesta.status
    error.datos = datos
    throw error
  }
  return datos
}

export const api = {
  // --- autenticación ---
  login: (usuario, password) => pedir('/auth/login', { metodo: 'POST', cuerpo: { usuario, password } }),
  yo: () => pedir('/auth/yo'),

  // --- salud y panel ---
  salud: () => pedir('/health'),
  panel: () => pedir('/dashboard'),

  // --- estudiantes ---
  estudiantes: (parametros) => pedir('/estudiantes', { parametros }),
  estudiante: (id) => pedir(`/estudiantes/${id}`),
  crearEstudiante: (cuerpo) => pedir('/estudiantes', { metodo: 'POST', cuerpo }),
  editarEstudiante: (id, cuerpo) => pedir(`/estudiantes/${id}`, { metodo: 'PUT', cuerpo }),
  eliminarEstudiante: (id, confirmar) =>
    pedir(`/estudiantes/${id}`, { metodo: 'DELETE', parametros: { confirmar } }),
  boleta: (id, periodo) => pedir(`/estudiantes/${id}/boleta`, { parametros: { periodo } }),

  // --- cursos ---
  cursos: (parametros) => pedir('/cursos', { parametros }),
  curso: (id) => pedir(`/cursos/${id}`),
  crearCurso: (cuerpo) => pedir('/cursos', { metodo: 'POST', cuerpo }),
  editarCurso: (id, cuerpo) => pedir(`/cursos/${id}`, { metodo: 'PUT', cuerpo }),
  eliminarCurso: (id, confirmar) => pedir(`/cursos/${id}`, { metodo: 'DELETE', parametros: { confirmar } }),

  // --- matrículas ---
  matriculas: (parametros) => pedir('/matriculas', { parametros }),
  matricula: (id) => pedir(`/matriculas/${id}`),
  crearMatricula: (cuerpo) => pedir('/matriculas', { metodo: 'POST', cuerpo }),
  editarMatricula: (id, cuerpo) => pedir(`/matriculas/${id}`, { metodo: 'PUT', cuerpo }),
  eliminarMatricula: (id) => pedir(`/matriculas/${id}`, { metodo: 'DELETE' }),

  // --- notas ---
  notas: (matriculaId) => pedir(`/matriculas/${matriculaId}/notas`),
  registrarNota: (matriculaId, cuerpo) =>
    pedir(`/matriculas/${matriculaId}/notas`, { metodo: 'POST', cuerpo }),
  editarNota: (notaId, cuerpo) => pedir(`/notas/${notaId}`, { metodo: 'PUT', cuerpo }),
  eliminarNota: (notaId) => pedir(`/notas/${notaId}`, { metodo: 'DELETE' }),

  // --- usuarios ---
  usuarios: () => pedir('/usuarios'),
  usuario: (id) => pedir(`/usuarios/${id}`),
  crearUsuario: (cuerpo) => pedir('/usuarios', { metodo: 'POST', cuerpo }),
  editarUsuario: (id, cuerpo) => pedir(`/usuarios/${id}`, { metodo: 'PUT', cuerpo }),
  eliminarUsuario: (id) => pedir(`/usuarios/${id}`, { metodo: 'DELETE' }),
}
