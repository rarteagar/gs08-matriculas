import { useEffect, useState } from 'react'
import { api } from '../api'
import { Avisos } from './Avisos.jsx'
import { Modal } from './Modal.jsx'

// Boleta del estudiante: consume GET /estudiantes/{id}/boleta.
export function Boleta({ estudiante, onCerrar }) {
  const [periodo, setPeriodo] = useState('2026-02')
  const [datos, setDatos] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')

  async function consultar(valorPeriodo = periodo) {
    setCargando(true)
    setError('')
    try {
      setDatos(await api.boleta(estudiante.id, valorPeriodo))
    } catch (fallo) {
      setDatos(null)
      setError(fallo.message)
    } finally {
      setCargando(false)
    }
  }

  useEffect(() => {
    consultar()
    // Solo al abrir: el periodo se consulta con el botón.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <Modal abierto titulo={`Boleta de ${estudiante.nombre_completo}`} onCerrar={onCerrar}>
      <form
        className="flex flex-wrap items-end gap-3"
        onSubmit={(evento) => {
          evento.preventDefault()
          consultar()
        }}
      >
        <div className="w-40">
          <label className="etiqueta" htmlFor="periodo-boleta">
            Periodo (AAAA-MM)
          </label>
          <input
            id="periodo-boleta"
            className="campo"
            value={periodo}
            onChange={(evento) => setPeriodo(evento.target.value)}
          />
        </div>
        <button className="boton-secundario" type="submit" disabled={cargando}>
          Consultar
        </button>
      </form>

      <Avisos error={error} aviso="" />

      {cargando && <p className="mt-4 text-sm text-slate-500">Cargando…</p>}

      {datos && !cargando && (
        <>
          <table className="tabla mt-4">
            <thead>
              <tr>
                <th>Curso</th>
                <th>Créditos</th>
                <th>Notas</th>
                <th className="text-right">Nota del curso</th>
              </tr>
            </thead>
            <tbody>
              {datos.cursos.map((curso) => (
                <tr key={curso.curso_id}>
                  <td>
                    {curso.curso}
                    <span className="block font-mono text-xs text-slate-400">{curso.codigo_curso}</span>
                  </td>
                  <td>{curso.creditos}</td>
                  <td>{curso.cantidad_notas}</td>
                  <td className="text-right font-medium text-slate-800">
                    {curso.nota_texto || 'Sin notas'}
                  </td>
                </tr>
              ))}
              {!datos.cursos.length && (
                <tr>
                  <td colSpan="4" className="py-4 text-center text-slate-500">
                    El estudiante no tiene matrículas en ese periodo.
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          <dl className="mt-4 grid gap-3 sm:grid-cols-3">
            <div className="tarjeta">
              <dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase">
                Promedio ponderado
              </dt>
              <dd className="mt-1 text-2xl font-semibold text-sky-700">
                {datos.promedio_texto || 'Sin notas'}
              </dd>
            </div>
            <div className="tarjeta">
              <dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase">
                Promedio simple
              </dt>
              <dd className="mt-1 text-2xl font-semibold text-slate-700">
                {datos.promedio_simple ?? '—'}
              </dd>
            </div>
            <div className="tarjeta">
              <dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase">
                Créditos con notas
              </dt>
              <dd className="mt-1 text-2xl font-semibold text-slate-700">{datos.creditos_con_notas}</dd>
            </div>
          </dl>
        </>
      )}
    </Modal>
  )
}
