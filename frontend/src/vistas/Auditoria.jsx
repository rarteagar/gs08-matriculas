import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import { Avisos } from '../componentes/Avisos.jsx'
import { TablaBitacora } from '../componentes/Bitacora.jsx'

// Pantalla de la bitácora: lo que el API guarda en la segunda base (MongoDB) para cada
// operación de escritura, más la consulta de la boleta archivada. Solo la ve el rol
// admin (su scope es `auditoria:leer`), así que el enlace del menú es solo para admin.
const ENTIDADES = ['todas', 'estudiante', 'curso', 'matricula', 'nota', 'usuario', 'sesión']
const ACCIONES = ['todas', 'crear', 'editar', 'eliminar']
const LIMITES = [10, 25, 50, 100]

// Qué decir en la línea de estado. Ojo: "apagada" solo se dice cuando el API lo
// confirmó; si la consulta falló (sesión vencida, red) no se puede afirmar eso.
function estadoDeLaBitacora(datos, cargando) {
  if (!datos) return cargando ? 'Consultando la bitácora…' : 'No se pudo consultar la bitácora.'
  if (!datos.activa) return 'La bitácora está apagada en este entorno (sin MONGO_URL).'
  return `${datos.total} operación(es) con ese filtro · ${datos.total_bitacora} en la bitácora`
}

export default function Auditoria() {
  const [entidad, setEntidad] = useState('todas')
  const [accion, setAccion] = useState('todas')
  const [limite, setLimite] = useState(25)
  const [datos, setDatos] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')

  const [estudianteId, setEstudianteId] = useState('')
  const [periodo, setPeriodo] = useState('2026-02')
  const [archivada, setArchivada] = useState(null)
  const [errorBoleta, setErrorBoleta] = useState('')

  const cargar = useCallback(async () => {
    setCargando(true)
    setError('')
    try {
      const respuesta = await api.auditoria({
        entidad: entidad === 'todas' ? '' : entidad,
        accion: accion === 'todas' ? '' : accion,
        limite,
      })
      setDatos(respuesta)
    } catch (fallo) {
      setError(fallo.message)
    } finally {
      setCargando(false)
    }
  }, [entidad, accion, limite])

  useEffect(() => {
    cargar()
  }, [cargar])

  async function verArchivada(evento) {
    evento.preventDefault()
    setErrorBoleta('')
    setArchivada(null)
    try {
      setArchivada(await api.boletaArchivada(estudianteId, periodo))
    } catch (fallo) {
      setErrorBoleta(fallo.message)
    }
  }

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-900">Auditoría</h1>
      <p className="text-sm text-slate-500">
        Cada alta, edición o baja del API queda registrada en la segunda base (MongoDB): quién la hizo,
        desde qué petición, con qué resultado y cuánto tardó.
      </p>

      <div className="tarjeta mt-4">
        <form className="flex flex-wrap items-end gap-3" onSubmit={(evento) => { evento.preventDefault(); cargar() }}>
          <div className="w-44">
            <label className="etiqueta" htmlFor="filtro-entidad">
              Entidad
            </label>
            <select id="filtro-entidad" className="campo" value={entidad} onChange={(evento) => setEntidad(evento.target.value)}>
              {ENTIDADES.map((valor) => (
                <option key={valor} value={valor}>
                  {valor === 'todas' ? 'Todas' : valor}
                </option>
              ))}
            </select>
          </div>
          <div className="w-40">
            <label className="etiqueta" htmlFor="filtro-accion">
              Acción
            </label>
            <select id="filtro-accion" className="campo" value={accion} onChange={(evento) => setAccion(evento.target.value)}>
              {ACCIONES.map((valor) => (
                <option key={valor} value={valor}>
                  {valor === 'todas' ? 'Todas' : valor}
                </option>
              ))}
            </select>
          </div>
          <div className="w-28">
            <label className="etiqueta" htmlFor="filtro-limite">
              Mostrar
            </label>
            <select id="filtro-limite" className="campo" value={limite} onChange={(evento) => setLimite(Number(evento.target.value))}>
              {LIMITES.map((valor) => (
                <option key={valor} value={valor}>
                  {valor}
                </option>
              ))}
            </select>
          </div>
          <button className="boton-secundario" type="submit" disabled={cargando}>
            {cargando ? 'Actualizando…' : 'Actualizar'}
          </button>
        </form>

        <p className="mt-3 text-sm text-slate-600" role="status">
          {estadoDeLaBitacora(datos, cargando)}
        </p>
        {datos?.detalle && <p className="mt-2 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">{datos.detalle}</p>}
      </div>

      <Avisos error={error} aviso="" />

      <TablaBitacora items={datos?.items ?? []} cargando={cargando && !datos?.items?.length} />

      <div className="tarjeta mt-4">
        <h2 className="text-sm font-semibold text-slate-900">Boleta archivada</h2>
        <p className="mt-1 text-sm text-slate-500">
          La boleta emitida queda guardada como documento en la segunda base. Consulta acá la copia de un
          estudiante y periodo.
        </p>
        <form className="mt-4 flex flex-wrap items-end gap-3" onSubmit={verArchivada}>
          <div className="w-32">
            <label className="etiqueta" htmlFor="boleta-estudiante">
              Estudiante (id)
            </label>
            <input
              id="boleta-estudiante"
              className="campo"
              inputMode="numeric"
              required
              value={estudianteId}
              onChange={(evento) => setEstudianteId(evento.target.value)}
            />
          </div>
          <div className="w-36">
            <label className="etiqueta" htmlFor="boleta-periodo">
              Periodo (AAAA-MM)
            </label>
            <input
              id="boleta-periodo"
              className="campo"
              required
              pattern="[0-9]{4}-[0-9]{2}"
              value={periodo}
              onChange={(evento) => setPeriodo(evento.target.value)}
            />
          </div>
          <button className="boton-secundario" type="submit">
            Ver archivada
          </button>
        </form>

        <Avisos error={errorBoleta} aviso="" />

        {archivada && (
          <div className="mt-4 rounded-lg border border-slate-200 p-4">
            {archivada.archivada ? (
              <dl className="grid gap-2 text-sm sm:grid-cols-3">
                <div>
                  <dt className="text-xs text-slate-500 uppercase">Generada</dt>
                  <dd className="text-slate-700">{archivada.generado_en}</dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-500 uppercase">Por</dt>
                  <dd className="text-slate-700">{archivada.generado_por}</dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-500 uppercase">Promedio del periodo</dt>
                  <dd className="font-semibold text-slate-900">
                    {archivada.boleta?.promedio_texto ?? '—'} · {archivada.boleta?.cursos?.length ?? 0} curso(s)
                  </dd>
                </div>
              </dl>
            ) : (
              <p className="text-sm text-slate-600" role="status">
                {archivada.activa
                  ? 'No hay una boleta archivada de ese estudiante y periodo.'
                  : 'La segunda base está apagada en este entorno, así que no hay boletas archivadas.'}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
