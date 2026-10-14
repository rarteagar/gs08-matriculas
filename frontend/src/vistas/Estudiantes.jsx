import { useState } from 'react'
import { api } from '../api'
import { usePaginado } from '../hooks/usePaginado'
import { Avisos, Insignia } from '../componentes/Avisos.jsx'
import { Confirmacion } from '../componentes/Modal.jsx'
import { TablaRecurso } from '../componentes/TablaRecurso.jsx'
import { Boleta } from '../componentes/Boleta.jsx'

const VACIO = {
  id: null,
  codigo: '',
  dni: '',
  nombres: '',
  apellidos: '',
  email: '',
  telefono: '',
  fecha_nacimiento: '',
  direccion: '',
  estado: true,
}

export default function Estudiantes() {
  const [formulario, setFormulario] = useState(VACIO)
  const [error, setError] = useState('')
  const [aviso, setAviso] = useState('')
  const [q, setQ] = useState('')
  const [estado, setEstado] = useState('')
  const [busqueda, setBusqueda] = useState({})
  const [porEliminar, setPorEliminar] = useState(null)
  const [matriculasHijas, setMatriculasHijas] = useState(null)
  const [eliminando, setEliminando] = useState(false)
  const [errorEliminar, setErrorEliminar] = useState('')
  const [boletaDe, setBoletaDe] = useState(null)

  const listado = usePaginado(api.estudiantes, 'estudiantes', busqueda)

  function cambiar(campo, valor) {
    setFormulario((actual) => ({ ...actual, [campo]: valor }))
  }

  function limpiar() {
    setFormulario({ ...VACIO })
  }

  function editar(estudiante) {
    setFormulario({
      id: estudiante.id,
      codigo: estudiante.codigo,
      dni: estudiante.dni,
      nombres: estudiante.nombres,
      apellidos: estudiante.apellidos,
      email: estudiante.email || '',
      telefono: estudiante.telefono || '',
      fecha_nacimiento: estudiante.fecha_nacimiento || '',
      direccion: estudiante.direccion || '',
      estado: estudiante.estado,
    })
    setAviso('')
    setError('')
    window.scrollTo({ top: 0 })
  }

  function cuerpo() {
    return {
      codigo: formulario.codigo.trim(),
      dni: formulario.dni.trim(),
      nombres: formulario.nombres.trim(),
      apellidos: formulario.apellidos.trim(),
      email: formulario.email.trim() || null,
      telefono: formulario.telefono.trim() || null,
      fecha_nacimiento: formulario.fecha_nacimiento || null,
      direccion: formulario.direccion.trim() || null,
      estado: formulario.estado,
    }
  }

  async function guardar(evento) {
    evento.preventDefault()
    setError('')
    setAviso('')
    try {
      if (formulario.id) {
        await api.editarEstudiante(formulario.id, cuerpo())
        setAviso(`Estudiante ${formulario.codigo} actualizado.`)
      } else {
        await api.crearEstudiante(cuerpo())
        setAviso(`Estudiante ${formulario.codigo} registrado.`)
      }
      limpiar()
      await listado.cargar(listado.page)
    } catch (fallo) {
      setError(fallo.message)
    }
  }

  async function eliminar() {
    setErrorEliminar('')
    setEliminando(true)
    try {
      await api.eliminarEstudiante(porEliminar.id, matriculasHijas ? true : undefined)
      setAviso(
        `Estudiante ${porEliminar.codigo} eliminado${matriculasHijas ? ` con sus ${matriculasHijas} matrícula(s)` : ''}.`,
      )
      setPorEliminar(null)
      setMatriculasHijas(null)
      await listado.cargar(1)
    } catch (fallo) {
      if (fallo.estado === 409 && fallo.datos?.matriculas) {
        setMatriculasHijas(fallo.datos.matriculas)
      } else {
        setErrorEliminar(fallo.message)
      }
    } finally {
      setEliminando(false)
    }
  }

  function buscar() {
    setBusqueda({ q, estado })
  }

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-900">Estudiantes</h1>
      <p className="text-sm text-slate-500">
        Lista del sistema, búsqueda y formulario de alta y edición.
      </p>

      <div className="tarjeta mt-4">
        <h2 className="text-sm font-semibold text-slate-900">
          {formulario.id ? `Editar ${formulario.codigo}` : 'Nuevo estudiante'}
        </h2>
        <form className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3" onSubmit={guardar}>
          <div>
            <label className="etiqueta" htmlFor="codigo">
              Código
            </label>
            <input
              id="codigo"
              className="campo"
              required
              maxLength="20"
              value={formulario.codigo}
              onChange={(evento) => cambiar('codigo', evento.target.value)}
            />
          </div>
          <div>
            <label className="etiqueta" htmlFor="dni">
              DNI (8 dígitos)
            </label>
            <input
              id="dni"
              className="campo"
              required
              maxLength="8"
              value={formulario.dni}
              onChange={(evento) => cambiar('dni', evento.target.value)}
            />
          </div>
          <div>
            <label className="etiqueta" htmlFor="nombres">
              Nombres
            </label>
            <input
              id="nombres"
              className="campo"
              required
              value={formulario.nombres}
              onChange={(evento) => cambiar('nombres', evento.target.value)}
            />
          </div>
          <div>
            <label className="etiqueta" htmlFor="apellidos">
              Apellidos
            </label>
            <input
              id="apellidos"
              className="campo"
              required
              value={formulario.apellidos}
              onChange={(evento) => cambiar('apellidos', evento.target.value)}
            />
          </div>
          <div>
            <label className="etiqueta" htmlFor="email">
              Email (opcional)
            </label>
            <input
              id="email"
              className="campo"
              value={formulario.email}
              onChange={(evento) => cambiar('email', evento.target.value)}
            />
          </div>
          <div>
            <label className="etiqueta" htmlFor="telefono">
              Teléfono (opcional)
            </label>
            <input
              id="telefono"
              className="campo"
              value={formulario.telefono}
              onChange={(evento) => cambiar('telefono', evento.target.value)}
            />
          </div>
          <div>
            <label className="etiqueta" htmlFor="nacimiento">
              Fecha de nacimiento (opcional)
            </label>
            <input
              id="nacimiento"
              type="date"
              className="campo"
              value={formulario.fecha_nacimiento}
              onChange={(evento) => cambiar('fecha_nacimiento', evento.target.value)}
            />
          </div>
          <div>
            <label className="etiqueta" htmlFor="direccion">
              Dirección (opcional)
            </label>
            <input
              id="direccion"
              className="campo"
              value={formulario.direccion}
              onChange={(evento) => cambiar('direccion', evento.target.value)}
            />
          </div>
          <div className="flex items-end gap-4">
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                className="h-4 w-4"
                checked={formulario.estado}
                onChange={(evento) => cambiar('estado', evento.target.checked)}
              />
              Activo
            </label>
          </div>
          <div className="flex items-end gap-2 sm:col-span-2 lg:col-span-3">
            <button className="boton-primario" type="submit">
              {formulario.id ? 'Guardar cambios' : 'Registrar'}
            </button>
            {formulario.id && (
              <button className="boton-secundario" type="button" onClick={limpiar}>
                Cancelar edición
              </button>
            )}
          </div>
        </form>
      </div>

      <Avisos error={error} aviso={aviso} />

      <TablaRecurso
        columnas={[
          'Código',
          'DNI',
          'Apellidos y nombres',
          'Email',
          'Estado',
          { clave: 'accion', titulo: 'Acciones', alineada: true },
        ]}
        filas={listado.items.map((estudiante) => (
          <tr key={estudiante.id}>
            <td className="font-mono text-xs">{estudiante.codigo}</td>
            <td className="font-mono text-xs">{estudiante.dni}</td>
            <td className="font-medium text-slate-700">{estudiante.nombre_completo}</td>
            <td className="text-slate-500">{estudiante.email || '—'}</td>
            <td>
              <Insignia estado={estudiante.estado} />
            </td>
            <td className="text-right">
              <div className="flex justify-end gap-2">
                <button
                  className="boton-secundario px-3! py-1.5! text-xs!"
                  type="button"
                  onClick={() => editar(estudiante)}
                >
                  Editar
                </button>
                <button
                  className="boton-secundario px-3! py-1.5! text-xs!"
                  type="button"
                  onClick={() => setBoletaDe(estudiante)}
                >
                  Boleta
                </button>
                <button
                  className="boton-peligro"
                  type="button"
                  onClick={() => {
                    setPorEliminar(estudiante)
                    setMatriculasHijas(null)
                    setErrorEliminar('')
                  }}
                >
                  Eliminar
                </button>
              </div>
            </td>
          </tr>
        ))}
        cargando={listado.cargando}
        q={q}
        onQ={setQ}
        onBuscar={buscar}
        page={listado.page}
        paginas={listado.paginas}
        total={listado.total}
        onPagina={(pagina) => listado.cargar(pagina)}
        mensajeVacio="No hay estudiantes registrados."
        singular="estudiante"
      >
        <div className="w-40">
          <label className="etiqueta" htmlFor="filtro-estado">
            Estado
          </label>
          <select
            id="filtro-estado"
            className="campo"
            value={estado}
            onChange={(evento) => setEstado(evento.target.value)}
          >
            <option value="">Todos</option>
            <option value="activo">Activos</option>
            <option value="inactivo">Inactivos</option>
          </select>
        </div>
      </TablaRecurso>

      <Avisos error={listado.error} aviso="" />

      <Confirmacion
        abierto={Boolean(porEliminar)}
        titulo={matriculasHijas ? 'El estudiante tiene matrículas' : 'Eliminar estudiante'}
        mensaje={
          matriculasHijas
            ? `${porEliminar?.nombre_completo} tiene ${matriculasHijas} matrícula(s) registrada(s). Si continúas se eliminan también sus matrículas y sus notas.`
            : `¿Seguro que quieres eliminar a ${porEliminar?.nombre_completo} (${porEliminar?.codigo})? Sus matrículas y notas se eliminan con él.`
        }
        textoConfirmar={matriculasHijas ? 'Sí, eliminar todo' : 'Sí, eliminar'}
        onConfirmar={eliminar}
        onCancelar={() => {
          setPorEliminar(null)
          setMatriculasHijas(null)
        }}
        cargando={eliminando}
        error={errorEliminar}
      />

      {boletaDe && <Boleta estudiante={boletaDe} onCerrar={() => setBoletaDe(null)} />}
    </div>
  )
}
