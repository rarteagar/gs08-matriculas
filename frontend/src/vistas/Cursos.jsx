import { useState } from 'react'
import { api } from '../api'
import { usePaginado } from '../hooks/usePaginado'
import { Avisos, Insignia } from '../componentes/Avisos.jsx'
import { Confirmacion } from '../componentes/Modal.jsx'
import { TablaRecurso } from '../componentes/TablaRecurso.jsx'

const VACIO = {
  id: null,
  codigo: '',
  nombre: '',
  descripcion: '',
  creditos: 3,
  horas: 48,
  estado: true,
}

export default function Cursos() {
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

  const listado = usePaginado(api.cursos, 'cursos', busqueda)

  function cambiar(campo, valor) {
    setFormulario((actual) => ({ ...actual, [campo]: valor }))
  }

  function limpiar() {
    setFormulario({ ...VACIO })
  }

  function editar(curso) {
    setFormulario({
      id: curso.id,
      codigo: curso.codigo,
      nombre: curso.nombre,
      descripcion: curso.descripcion || '',
      creditos: curso.creditos,
      horas: curso.horas,
      estado: curso.estado,
    })
    setAviso('')
    setError('')
    window.scrollTo({ top: 0 })
  }

  function cuerpo() {
    return {
      codigo: formulario.codigo.trim(),
      nombre: formulario.nombre.trim(),
      descripcion: formulario.descripcion.trim() || null,
      creditos: Number(formulario.creditos),
      horas: Number(formulario.horas),
      estado: formulario.estado,
    }
  }

  async function guardar(evento) {
    evento.preventDefault()
    setError('')
    setAviso('')
    try {
      if (formulario.id) {
        await api.editarCurso(formulario.id, cuerpo())
        setAviso(`Curso ${formulario.codigo} actualizado.`)
      } else {
        await api.crearCurso(cuerpo())
        setAviso(`Curso ${formulario.codigo} registrado.`)
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
      await api.eliminarCurso(porEliminar.id, matriculasHijas ? true : undefined)
      setAviso(
        `Curso ${porEliminar.codigo} eliminado${matriculasHijas ? ` con sus ${matriculasHijas} matrícula(s)` : ''}.`,
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

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-900">Cursos</h1>
      <p className="text-sm text-slate-500">
        Catálogo de cursos con créditos y horas, y su estado en el sistema.
      </p>

      <div className="tarjeta mt-4">
        <h2 className="text-sm font-semibold text-slate-900">
          {formulario.id ? `Editar ${formulario.codigo}` : 'Nuevo curso'}
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
          <div className="lg:col-span-2">
            <label className="etiqueta" htmlFor="nombre">
              Nombre del curso
            </label>
            <input
              id="nombre"
              className="campo"
              required
              maxLength="100"
              value={formulario.nombre}
              onChange={(evento) => cambiar('nombre', evento.target.value)}
            />
          </div>
          <div className="sm:col-span-2 lg:col-span-3">
            <label className="etiqueta" htmlFor="descripcion">
              Descripción (opcional)
            </label>
            <input
              id="descripcion"
              className="campo"
              value={formulario.descripcion}
              onChange={(evento) => cambiar('descripcion', evento.target.value)}
            />
          </div>
          <div>
            <label className="etiqueta" htmlFor="creditos">
              Créditos
            </label>
            <input
              id="creditos"
              type="number"
              min="1"
              max="20"
              className="campo"
              required
              value={formulario.creditos}
              onChange={(evento) => cambiar('creditos', evento.target.value)}
            />
          </div>
          <div>
            <label className="etiqueta" htmlFor="horas">
              Horas
            </label>
            <input
              id="horas"
              type="number"
              min="1"
              max="500"
              className="campo"
              required
              value={formulario.horas}
              onChange={(evento) => cambiar('horas', evento.target.value)}
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
          'Curso',
          'Créditos',
          'Horas',
          'Estado',
          { clave: 'accion', titulo: 'Acciones', alineada: true },
        ]}
        filas={listado.items.map((curso) => (
          <tr key={curso.id}>
            <td className="font-mono text-xs">{curso.codigo}</td>
            <td className="font-medium text-slate-700">{curso.nombre}</td>
            <td>{curso.creditos}</td>
            <td>{curso.horas}</td>
            <td>
              <Insignia estado={curso.estado} />
            </td>
            <td className="text-right">
              <div className="flex justify-end gap-2">
                <button
                  className="boton-secundario px-3! py-1.5! text-xs!"
                  type="button"
                  onClick={() => editar(curso)}
                >
                  Editar
                </button>
                <button
                  className="boton-peligro"
                  type="button"
                  onClick={() => {
                    setPorEliminar(curso)
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
        onBuscar={() => setBusqueda({ q, estado })}
        page={listado.page}
        paginas={listado.paginas}
        total={listado.total}
        onPagina={(pagina) => listado.cargar(pagina)}
        mensajeVacio="No hay cursos registrados."
        singular="curso"
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
        titulo={matriculasHijas ? 'El curso tiene matrículas' : 'Eliminar curso'}
        mensaje={
          matriculasHijas
            ? `El curso ${porEliminar?.nombre} tiene ${matriculasHijas} matrícula(s). Si continúas se eliminan también esas matrículas y sus notas.`
            : `¿Seguro que quieres eliminar el curso ${porEliminar?.nombre} (${porEliminar?.codigo})?`
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
    </div>
  )
}
