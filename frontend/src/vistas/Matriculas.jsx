import { useEffect, useState } from 'react'
import { api } from '../api'
import { usePaginado } from '../hooks/usePaginado'
import { Avisos, Insignia } from '../componentes/Avisos.jsx'
import { Confirmacion } from '../componentes/Modal.jsx'
import { TablaRecurso } from '../componentes/TablaRecurso.jsx'
import { Notas } from '../componentes/Notas.jsx'

const VACIO = {
  id: null,
  estudiante_id: '',
  curso_id: '',
  periodo: '2026-02',
  fecha_matricula: '',
  estado: 'activa',
}

export default function Matriculas() {
  const [formulario, setFormulario] = useState(VACIO)
  const [estudiantes, setEstudiantes] = useState([])
  const [cursos, setCursos] = useState([])
  const [error, setError] = useState('')
  const [aviso, setAviso] = useState('')
  const [q, setQ] = useState('')
  const [periodo, setPeriodo] = useState('')
  const [estado, setEstado] = useState('')
  const [busqueda, setBusqueda] = useState({})
  const [porEliminar, setPorEliminar] = useState(null)
  const [eliminando, setEliminando] = useState(false)
  const [errorEliminar, setErrorEliminar] = useState('')
  const [notasDe, setNotasDe] = useState(null)

  const listado = usePaginado(api.matriculas, 'matriculas', busqueda)

  useEffect(() => {
    async function cargarSelectores() {
      try {
        const [alumnos, catalogo] = await Promise.all([
          api.estudiantes({ page_size: 100 }),
          api.cursos({ page_size: 100 }),
        ])
        setEstudiantes(alumnos.estudiantes)
        setCursos(catalogo.cursos)
      } catch (fallo) {
        setError(fallo.message)
      }
    }
    cargarSelectores()
  }, [])

  function cambiar(campo, valor) {
    setFormulario((actual) => ({ ...actual, [campo]: valor }))
  }

  function limpiar() {
    setFormulario({ ...VACIO })
  }

  function editar(matricula) {
    setFormulario({
      id: matricula.id,
      estudiante_id: matricula.estudiante_id,
      curso_id: matricula.curso_id,
      periodo: matricula.periodo,
      fecha_matricula: matricula.fecha_matricula,
      estado: matricula.estado,
    })
    setAviso('')
    setError('')
    window.scrollTo({ top: 0 })
  }

  async function guardar(evento) {
    evento.preventDefault()
    setError('')
    setAviso('')
    const cuerpo = {
      estudiante_id: Number(formulario.estudiante_id),
      curso_id: Number(formulario.curso_id),
      periodo: formulario.periodo.trim(),
      fecha_matricula: formulario.fecha_matricula,
      estado: formulario.estado,
    }
    try {
      if (formulario.id) {
        const actualizada = await api.editarMatricula(formulario.id, cuerpo)
        setAviso(`Matrícula ${actualizada.id} actualizada.`)
      } else {
        const creada = await api.crearMatricula(cuerpo)
        setAviso(
          `Matrícula ${creada.id} registrada: ${creada.estudiante} en ${creada.curso} (${creada.periodo}).`,
        )
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
      await api.eliminarMatricula(porEliminar.id)
      setAviso(`Matrícula ${porEliminar.id} eliminada.`)
      setPorEliminar(null)
      await listado.cargar(1)
    } catch (fallo) {
      setErrorEliminar(fallo.message)
    } finally {
      setEliminando(false)
    }
  }

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-900">Matrículas</h1>
      <p className="text-sm text-slate-500">
        Un estudiante en un curso, en un periodo. Los selectores salen de las listas de estudiantes y
        cursos, y desde cada fila se ven y registran sus notas.
      </p>

      <div className="tarjeta mt-4">
        <h2 className="text-sm font-semibold text-slate-900">
          {formulario.id ? `Editar matrícula ${formulario.id}` : 'Nueva matrícula'}
        </h2>
        <form className="mt-4 grid gap-4 md:grid-cols-4" onSubmit={guardar}>
          <div className="md:col-span-2">
            <label className="etiqueta" htmlFor="estudiante">
              Estudiante
            </label>
            <select
              id="estudiante"
              className="campo"
              required
              value={formulario.estudiante_id}
              onChange={(evento) => cambiar('estudiante_id', evento.target.value)}
            >
              <option value="" disabled>
                Selecciona un estudiante
              </option>
              {estudiantes.map((estudiante) => (
                <option key={estudiante.id} value={estudiante.id}>
                  {estudiante.codigo} · {estudiante.nombre_completo}
                </option>
              ))}
            </select>
          </div>
          <div className="md:col-span-2">
            <label className="etiqueta" htmlFor="curso">
              Curso
            </label>
            <select
              id="curso"
              className="campo"
              required
              value={formulario.curso_id}
              onChange={(evento) => cambiar('curso_id', evento.target.value)}
            >
              <option value="" disabled>
                Selecciona un curso
              </option>
              {cursos.map((curso) => (
                <option key={curso.id} value={curso.id}>
                  {curso.codigo} · {curso.nombre} ({curso.creditos} cr.)
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="etiqueta" htmlFor="periodo">
              Periodo (AAAA-MM)
            </label>
            <input
              id="periodo"
              className="campo"
              placeholder="2026-02"
              required
              value={formulario.periodo}
              onChange={(evento) => cambiar('periodo', evento.target.value)}
            />
          </div>
          <div>
            <label className="etiqueta" htmlFor="fecha">
              Fecha de matrícula
            </label>
            <input
              id="fecha"
              type="date"
              className="campo"
              required
              value={formulario.fecha_matricula}
              onChange={(evento) => cambiar('fecha_matricula', evento.target.value)}
            />
          </div>
          <div>
            <label className="etiqueta" htmlFor="estado">
              Estado
            </label>
            <select
              id="estado"
              className="campo"
              value={formulario.estado}
              onChange={(evento) => cambiar('estado', evento.target.value)}
            >
              <option value="activa">Activa</option>
              <option value="retirado">Retirado</option>
            </select>
          </div>
          <div className="flex items-end gap-2">
            <button className="boton-primario" type="submit">
              {formulario.id ? 'Guardar cambios' : 'Matricular'}
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
          '#',
          'Estudiante',
          'Curso',
          'Periodo',
          'Fecha',
          'Estado',
          { clave: 'accion', titulo: 'Acciones', alineada: true },
        ]}
        filas={listado.items.map((matricula) => (
          <tr key={matricula.id}>
            <td className="text-slate-500">{matricula.id}</td>
            <td>
              <span className="font-medium text-slate-700">{matricula.estudiante}</span>
              <span className="block font-mono text-xs text-slate-400">
                {matricula.codigo_estudiante}
              </span>
            </td>
            <td>
              {matricula.curso}
              <span className="block text-xs text-slate-400">
                {matricula.codigo_curso} · {matricula.creditos} cr.
              </span>
            </td>
            <td>{matricula.periodo}</td>
            <td>{matricula.fecha_matricula}</td>
            <td>
              <Insignia estado={matricula.estado} />
            </td>
            <td className="text-right">
              <div className="flex justify-end gap-2">
                <button
                  className="boton-secundario px-3! py-1.5! text-xs!"
                  type="button"
                  onClick={() => editar(matricula)}
                >
                  Editar
                </button>
                <button
                  className="boton-secundario px-3! py-1.5! text-xs!"
                  type="button"
                  onClick={() => setNotasDe(matricula)}
                >
                  Notas
                </button>
                <button
                  className="boton-peligro"
                  type="button"
                  onClick={() => {
                    setPorEliminar(matricula)
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
        onBuscar={() => setBusqueda({ q, periodo, estado })}
        page={listado.page}
        paginas={listado.paginas}
        total={listado.total}
        onPagina={(pagina) => listado.cargar(pagina)}
        mensajeVacio="No hay matrículas registradas."
        singular="matrícula"
      >
        <div className="w-36">
          <label className="etiqueta" htmlFor="filtro-periodo">
            Periodo
          </label>
          <input
            id="filtro-periodo"
            className="campo"
            placeholder="2026-02"
            value={periodo}
            onChange={(evento) => setPeriodo(evento.target.value)}
          />
        </div>
        <div className="w-36">
          <label className="etiqueta" htmlFor="filtro-estado-matricula">
            Estado
          </label>
          <select
            id="filtro-estado-matricula"
            className="campo"
            value={estado}
            onChange={(evento) => setEstado(evento.target.value)}
          >
            <option value="">Todos</option>
            <option value="activa">Activas</option>
            <option value="retirado">Retiradas</option>
          </select>
        </div>
      </TablaRecurso>

      <Avisos error={listado.error} aviso="" />

      <Confirmacion
        abierto={Boolean(porEliminar)}
        titulo="Eliminar matrícula"
        mensaje={`¿Seguro que quieres eliminar la matrícula ${porEliminar?.id} de ${porEliminar?.estudiante} en ${porEliminar?.curso}? Se eliminan también sus notas.`}
        textoConfirmar="Sí, eliminar"
        onConfirmar={eliminar}
        onCancelar={() => setPorEliminar(null)}
        cargando={eliminando}
        error={errorEliminar}
      />

      {notasDe && (
        <Notas
          matricula={notasDe}
          onCerrar={() => setNotasDe(null)}
          onCambio={() => listado.cargar(listado.page)}
        />
      )}
    </div>
  )
}
