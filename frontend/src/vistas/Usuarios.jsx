import { useEffect, useState } from 'react'
import { api } from '../api'
import { Avisos } from '../componentes/Avisos.jsx'
import { Confirmacion } from '../componentes/Modal.jsx'

const VACIO = {
  id: null,
  nombre_usuario: '',
  email: '',
  password: '',
  nombre_completo: '',
  rol: 'asistente',
  estado: true,
}

export default function Usuarios() {
  const [lista, setLista] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [aviso, setAviso] = useState('')
  const [formulario, setFormulario] = useState(VACIO)
  const [porEliminar, setPorEliminar] = useState(null)
  const [eliminando, setEliminando] = useState(false)
  const [errorEliminar, setErrorEliminar] = useState('')

  async function cargar() {
    setCargando(true)
    setError('')
    try {
      setLista(await api.usuarios())
    } catch (fallo) {
      setError(fallo.message)
    } finally {
      setCargando(false)
    }
  }

  useEffect(() => {
    cargar()
  }, [])

  function cambiar(campo, valor) {
    setFormulario((actual) => ({ ...actual, [campo]: valor }))
  }

  function limpiar() {
    setFormulario({ ...VACIO })
  }

  function editar(usuario) {
    setFormulario({
      id: usuario.id,
      nombre_usuario: usuario.nombre_usuario,
      email: usuario.email,
      password: '',
      nombre_completo: usuario.nombre_completo,
      rol: usuario.rol,
      estado: usuario.estado,
    })
    setAviso('')
    setError('')
    window.scrollTo({ top: 0 })
  }

  async function guardar(evento) {
    evento.preventDefault()
    setError('')
    setAviso('')
    try {
      if (formulario.id) {
        const cuerpo = {
          email: formulario.email.trim(),
          nombre_completo: formulario.nombre_completo.trim(),
          rol: formulario.rol,
          estado: formulario.estado,
        }
        if (formulario.password.trim()) cuerpo.password = formulario.password
        await api.editarUsuario(formulario.id, cuerpo)
        setAviso(`Usuario ${formulario.nombre_usuario} actualizado.`)
      } else {
        await api.crearUsuario({
          nombre_usuario: formulario.nombre_usuario.trim(),
          email: formulario.email.trim(),
          password: formulario.password,
          nombre_completo: formulario.nombre_completo.trim(),
          rol: formulario.rol,
          estado: formulario.estado,
        })
        setAviso(`Usuario ${formulario.nombre_usuario} creado.`)
      }
      limpiar()
      await cargar()
    } catch (fallo) {
      setError(fallo.message)
    }
  }

  async function eliminar() {
    setErrorEliminar('')
    setEliminando(true)
    try {
      await api.eliminarUsuario(porEliminar.id)
      setAviso(`Usuario ${porEliminar.nombre_usuario} eliminado.`)
      setPorEliminar(null)
      await cargar()
    } catch (fallo) {
      setErrorEliminar(fallo.message)
    } finally {
      setEliminando(false)
    }
  }

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-900">Usuarios</h1>
      <p className="text-sm text-slate-500">
        Cuentas del sistema y su rol. Solo el administrador puede administrarlas.
      </p>

      <div className="tarjeta mt-4">
        <h2 className="text-sm font-semibold text-slate-900">
          {formulario.id ? `Editar ${formulario.nombre_usuario}` : 'Nuevo usuario'}
        </h2>
        <form className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3" onSubmit={guardar}>
          <div>
            <label className="etiqueta" htmlFor="nombre_usuario">
              Nombre de usuario
            </label>
            <input
              id="nombre_usuario"
              className="campo"
              required
              disabled={Boolean(formulario.id)}
              value={formulario.nombre_usuario}
              onChange={(evento) => cambiar('nombre_usuario', evento.target.value)}
            />
          </div>
          <div>
            <label className="etiqueta" htmlFor="nombre_completo">
              Nombre completo
            </label>
            <input
              id="nombre_completo"
              className="campo"
              required
              maxLength="100"
              value={formulario.nombre_completo}
              onChange={(evento) => cambiar('nombre_completo', evento.target.value)}
            />
          </div>
          <div>
            <label className="etiqueta" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              className="campo"
              required
              value={formulario.email}
              onChange={(evento) => cambiar('email', evento.target.value)}
            />
          </div>
          <div>
            <label className="etiqueta" htmlFor="password">
              Contraseña {formulario.id ? '(dejar vacía para no cambiarla)' : ''}
            </label>
            <input
              id="password"
              type="password"
              className="campo"
              required={!formulario.id}
              minLength="8"
              autoComplete="new-password"
              value={formulario.password}
              onChange={(evento) => cambiar('password', evento.target.value)}
            />
          </div>
          <div>
            <label className="etiqueta" htmlFor="rol">
              Rol
            </label>
            <select
              id="rol"
              className="campo"
              value={formulario.rol}
              onChange={(evento) => cambiar('rol', evento.target.value)}
            >
              <option value="asistente">Asistente</option>
              <option value="admin">Administrador</option>
            </select>
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
              {formulario.id ? 'Guardar cambios' : 'Crear usuario'}
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

      <div className="tarjeta mt-4 overflow-x-auto">
        <table className="tabla">
          <thead>
            <tr>
              <th>Usuario</th>
              <th>Nombre completo</th>
              <th>Email</th>
              <th>Rol</th>
              <th>Estado</th>
              <th className="text-right">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {lista.map((usuario) => (
              <tr key={usuario.id}>
                <td className="font-mono text-xs">{usuario.nombre_usuario}</td>
                <td className="font-medium text-slate-700">{usuario.nombre_completo}</td>
                <td className="text-slate-500">{usuario.email}</td>
                <td>{usuario.rol === 'admin' ? 'Administrador' : 'Asistente'}</td>
                <td className="text-slate-500">{usuario.estado ? 'Activo' : 'Inactivo'}</td>
                <td className="text-right">
                  <div className="flex justify-end gap-2">
                    <button
                      className="boton-secundario px-3! py-1.5! text-xs!"
                      type="button"
                      onClick={() => editar(usuario)}
                    >
                      Editar
                    </button>
                    <button
                      className="boton-peligro"
                      type="button"
                      onClick={() => {
                        setPorEliminar(usuario)
                        setErrorEliminar('')
                      }}
                    >
                      Eliminar
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {!lista.length && (
              <tr>
                <td colSpan="6" className="py-6 text-center text-slate-500">
                  {cargando ? 'Cargando…' : 'No hay usuarios registrados.'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
        <p className="mt-3 text-sm text-slate-600">{lista.length} usuario(s)</p>
      </div>

      <Confirmacion
        abierto={Boolean(porEliminar)}
        titulo="Eliminar usuario"
        mensaje={`¿Seguro que quieres eliminar al usuario ${porEliminar?.nombre_usuario} (${porEliminar?.nombre_completo})?`}
        textoConfirmar="Sí, eliminar"
        onConfirmar={eliminar}
        onCancelar={() => setPorEliminar(null)}
        cargando={eliminando}
        error={errorEliminar}
      />
    </div>
  )
}
