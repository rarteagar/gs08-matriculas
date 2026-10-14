import { useEffect, useState } from 'react'
import { api } from '../api'
import { Avisos } from './Avisos.jsx'
import { Confirmacion, Modal } from './Modal.jsx'

const VACIO = { tipo: 'practica', numero: 1, nota: '', fecha_registro: '', observacion: '' }

const TIPOS = [
  { valor: 'practica', texto: 'Práctica' },
  { valor: 'parcial', texto: 'Parcial' },
  { valor: 'final', texto: 'Final' },
]

// Notas de una matrícula: consume GET y POST /matriculas/{id}/notas y
// PUT y DELETE /notas/{id}.
export function Notas({ matricula, onCerrar, onCambio }) {
  const [notas, setNotas] = useState([])
  const [formulario, setFormulario] = useState({ ...VACIO })
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [aviso, setAviso] = useState('')
  const [porEliminar, setPorEliminar] = useState(null)
  const [eliminando, setEliminando] = useState(false)

  async function cargar() {
    setCargando(true)
    setError('')
    try {
      setNotas(await api.notas(matricula.id))
    } catch (fallo) {
      setError(fallo.message)
    } finally {
      setCargando(false)
    }
  }

  useEffect(() => {
    cargar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function cambiar(campo, valor) {
    setFormulario((actual) => ({ ...actual, [campo]: valor }))
  }

  function editar(nota) {
    setFormulario({
      id: nota.id,
      tipo: nota.tipo,
      numero: nota.numero,
      nota: String(nota.nota),
      fecha_registro: nota.fecha_registro || '',
      observacion: nota.observacion || '',
    })
    setAviso('')
    setError('')
  }

  async function guardar(evento) {
    evento.preventDefault()
    setError('')
    setAviso('')
    const cuerpo = {
      tipo: formulario.tipo,
      numero: Number(formulario.numero),
      nota: Number(formulario.nota),
      fecha_registro: formulario.fecha_registro || null,
      observacion: formulario.observacion.trim() || null,
    }
    try {
      if (formulario.id) {
        await api.editarNota(formulario.id, cuerpo)
        setAviso('Nota actualizada.')
      } else {
        await api.registrarNota(matricula.id, cuerpo)
        setAviso('Nota registrada.')
      }
      setFormulario({ ...VACIO })
      await cargar()
      onCambio?.()
    } catch (fallo) {
      setError(fallo.message)
    }
  }

  async function eliminar() {
    setEliminando(true)
    setError('')
    try {
      await api.eliminarNota(porEliminar.id)
      setAviso('Nota eliminada.')
      setPorEliminar(null)
      await cargar()
      onCambio?.()
    } catch (fallo) {
      setError(fallo.message)
    } finally {
      setEliminando(false)
    }
  }

  return (
    <Modal abierto titulo={`Notas · ${matricula.estudiante} en ${matricula.curso}`} onCerrar={onCerrar}>
      <form className="grid gap-4 sm:grid-cols-3" onSubmit={guardar}>
        <div>
          <label className="etiqueta" htmlFor="tipo">
            Tipo
          </label>
          <select
            id="tipo"
            className="campo"
            value={formulario.tipo}
            onChange={(evento) => cambiar('tipo', evento.target.value)}
          >
            {TIPOS.map((tipo) => (
              <option key={tipo.valor} value={tipo.valor}>
                {tipo.texto}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="etiqueta" htmlFor="numero">
            Número
          </label>
          <input
            id="numero"
            type="number"
            min="1"
            max="50"
            className="campo"
            required
            value={formulario.numero}
            onChange={(evento) => cambiar('numero', evento.target.value)}
          />
        </div>
        <div>
          <label className="etiqueta" htmlFor="nota">
            Nota (0 a 20)
          </label>
          <input
            id="nota"
            type="number"
            min="0"
            max="20"
            step="0.01"
            className="campo"
            required
            value={formulario.nota}
            onChange={(evento) => cambiar('nota', evento.target.value)}
          />
        </div>
        <div>
          <label className="etiqueta" htmlFor="fecha_registro">
            Fecha (opcional)
          </label>
          <input
            id="fecha_registro"
            type="date"
            className="campo"
            value={formulario.fecha_registro}
            onChange={(evento) => cambiar('fecha_registro', evento.target.value)}
          />
        </div>
        <div className="sm:col-span-2">
          <label className="etiqueta" htmlFor="observacion">
            Observación (opcional)
          </label>
          <input
            id="observacion"
            className="campo"
            value={formulario.observacion}
            onChange={(evento) => cambiar('observacion', evento.target.value)}
          />
        </div>
        <div className="flex items-end gap-2 sm:col-span-3">
          <button className="boton-primario" type="submit">
            {formulario.id ? 'Guardar nota' : 'Registrar nota'}
          </button>
          {formulario.id && (
            <button
              className="boton-secundario"
              type="button"
              onClick={() => setFormulario({ ...VACIO })}
            >
              Cancelar edición
            </button>
          )}
        </div>
      </form>

      <Avisos error={error} aviso={aviso} />

      <table className="tabla mt-4">
        <thead>
          <tr>
            <th>Tipo</th>
            <th>Número</th>
            <th>Nota</th>
            <th>Fecha</th>
            <th>Observación</th>
            <th className="text-right">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {notas.map((nota) => (
            <tr key={nota.id}>
              <td className="capitalize">{nota.tipo}</td>
              <td>{nota.numero}</td>
              <td className="font-medium text-slate-800">{nota.nota_texto}</td>
              <td>{nota.fecha_registro || '—'}</td>
              <td className="text-slate-500">{nota.observacion || '—'}</td>
              <td className="text-right">
                <div className="flex justify-end gap-2">
                  <button
                    className="boton-secundario px-3! py-1.5! text-xs!"
                    type="button"
                    onClick={() => editar(nota)}
                  >
                    Editar
                  </button>
                  <button
                    className="boton-peligro"
                    type="button"
                    onClick={() => setPorEliminar(nota)}
                  >
                    Eliminar
                  </button>
                </div>
              </td>
            </tr>
          ))}
          {!notas.length && (
            <tr>
              <td colSpan="6" className="py-6 text-center text-slate-500">
                {cargando ? 'Cargando…' : 'Esta matrícula todavía no tiene notas.'}
              </td>
            </tr>
          )}
        </tbody>
      </table>

      <Confirmacion
        abierto={Boolean(porEliminar)}
        titulo="Eliminar nota"
        mensaje={`¿Seguro que quieres eliminar la nota ${porEliminar?.tipo} ${porEliminar?.numero} (${porEliminar?.nota_texto})?`}
        textoConfirmar="Sí, eliminar"
        onConfirmar={eliminar}
        onCancelar={() => setPorEliminar(null)}
        cargando={eliminando}
        error=""
      />
    </Modal>
  )
}
