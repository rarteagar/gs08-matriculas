// Cliente del API. Todo pasa por nginx (/api/v1), así que el SPA y el API
// comparten origen y no hay CORS ni URL absoluta embebida.
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
  return `No se pudo completar la operación (HTTP ${estado}).`
}

export async function pedir(ruta, { metodo = 'GET', cuerpo } = {}) {
  const cabeceras = {}
  if (cuerpo !== undefined) cabeceras['Content-Type'] = 'application/json'
  const sesion = token()
  if (sesion) cabeceras.Authorization = `Bearer ${sesion}`

  const respuesta = await fetch(`${BASE}${ruta}`, {
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
  login: (usuario, password) => pedir('/auth/login', { metodo: 'POST', cuerpo: { usuario, password } }),
  panel: () => pedir('/dashboard'),
  estudiantes: (parametros = {}) => {
    const cadena = new URLSearchParams(
      Object.entries(parametros).filter(([, v]) => v !== '' && v !== null && v !== undefined),
    ).toString()
    return pedir(`/estudiantes${cadena ? `?${cadena}` : ''}`)
  },
  crearEstudiante: (cuerpo) => pedir('/estudiantes', { metodo: 'POST', cuerpo }),
  editarEstudiante: (id, cuerpo) => pedir(`/estudiantes/${id}`, { metodo: 'PUT', cuerpo }),
  cursos: (parametros = {}) => {
    const cadena = new URLSearchParams(
      Object.entries(parametros).filter(([, v]) => v !== '' && v !== null && v !== undefined),
    ).toString()
    return pedir(`/cursos${cadena ? `?${cadena}` : ''}`)
  },
  matriculas: (parametros = {}) => {
    const cadena = new URLSearchParams(
      Object.entries(parametros).filter(([, v]) => v !== '' && v !== null && v !== undefined),
    ).toString()
    return pedir(`/matriculas${cadena ? `?${cadena}` : ''}`)
  },
  crearMatricula: (cuerpo) => pedir('/matriculas', { metodo: 'POST', cuerpo }),
  editarMatricula: (id, cuerpo) => pedir(`/matriculas/${id}`, { metodo: 'PUT', cuerpo }),
}
