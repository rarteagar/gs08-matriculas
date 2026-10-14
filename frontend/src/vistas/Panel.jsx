import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

// Panel: consume /dashboard (indicadores, top de cursos y últimos estudiantes).
export default function Panel() {
  const [datos, setDatos] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let vigente = true
    api
      .panel()
      .then((respuesta) => {
        if (vigente) setDatos(respuesta)
      })
      .catch((fallo) => {
        if (vigente) setError(fallo.message)
      })
      .finally(() => {
        if (vigente) setCargando(false)
      })
    return () => {
      vigente = false
    }
  }, [])

  const indicadores = [
    { clave: 'estudiantes_activos', titulo: 'Estudiantes activos', tono: 'text-sky-700' },
    { clave: 'cursos_activos', titulo: 'Cursos activos', tono: 'text-emerald-700' },
    { clave: 'matriculas_activas', titulo: 'Matrículas activas', tono: 'text-violet-700' },
    { clave: 'usuarios_activos', titulo: 'Usuarios activos', tono: 'text-slate-700' },
  ]

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-900">Panel</h1>
      <p className="text-sm text-slate-500">
        Los indicadores salen del servicio del panel y, debajo, el top de cursos y los últimos estudiantes.
      </p>

      {cargando && <p className="mt-6 text-sm text-slate-500">Cargando…</p>}
      {error && (
        <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700" role="alert">
          {error}
        </p>
      )}

      {datos && !cargando && (
        <>
          <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {indicadores.map((indicador) => (
              <div className="tarjeta" key={indicador.clave}>
                <p className="text-xs font-semibold tracking-wide text-slate-500 uppercase">
                  {indicador.titulo}
                </p>
                <p className={`mt-2 text-3xl font-semibold ${indicador.tono}`}>
                  {datos[indicador.clave]}
                </p>
              </div>
            ))}
          </div>

          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            <div className="tarjeta">
              <h2 className="text-sm font-semibold text-slate-900">Cursos con más matrículas</h2>
              <table className="tabla mt-3">
                <thead>
                  <tr>
                    <th>Curso</th>
                    <th>Créditos</th>
                    <th className="text-right">Matrículas</th>
                  </tr>
                </thead>
                <tbody>
                  {datos.top_cursos.map((curso) => (
                    <tr key={curso.curso_id}>
                      <td>
                        {curso.curso}
                        <span className="block font-mono text-xs text-slate-400">{curso.codigo}</span>
                      </td>
                      <td>{curso.creditos}</td>
                      <td className="text-right">{curso.matriculas}</td>
                    </tr>
                  ))}
                  {!datos.top_cursos.length && (
                    <tr>
                      <td colSpan="3" className="py-4 text-center text-slate-500">
                        Todavía no hay matrículas registradas.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="tarjeta">
              <h2 className="text-sm font-semibold text-slate-900">Últimos estudiantes</h2>
              <table className="tabla mt-3">
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Apellidos y nombres</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {datos.ultimos_estudiantes.map((estudiante) => (
                    <tr key={estudiante.id}>
                      <td className="font-mono text-xs">{estudiante.codigo}</td>
                      <td className="font-medium text-slate-700">{estudiante.nombre_completo}</td>
                      <td className="text-slate-500">{estudiante.estado ? 'Activo' : 'Inactivo'}</td>
                    </tr>
                  ))}
                  {!datos.ultimos_estudiantes.length && (
                    <tr>
                      <td colSpan="3" className="py-4 text-center text-slate-500">
                        Todavía no hay estudiantes registrados.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      <div className="tarjeta mt-6">
        <h2 className="text-sm font-semibold text-slate-900">Ir a</h2>
        <div className="mt-3 flex flex-wrap gap-3">
          <Link className="boton-primario" to="/estudiantes">
            Estudiantes
          </Link>
          <Link className="boton-primario" to="/cursos">
            Cursos
          </Link>
          <Link className="boton-primario" to="/matriculas">
            Matrículas
          </Link>
        </div>
      </div>
    </div>
  )
}
