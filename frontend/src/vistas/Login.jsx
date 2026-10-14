import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { api, guardarSesion, token } from '../api'

export default function Login() {
  const navegar = useNavigate()
  const [usuario, setUsuario] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  if (token()) return <Navigate to="/" replace />

  async function entrar(evento) {
    evento.preventDefault()
    setError('')
    setCargando(true)
    try {
      const datos = await api.login(usuario, password)
      guardarSesion(datos)
      navegar('/', { replace: true })
    } catch (fallo) {
      setError(fallo.message)
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="mx-auto mt-10 max-w-md">
      <div className="tarjeta">
        <h1 className="text-lg font-semibold text-slate-900">Iniciar sesión</h1>
        <p className="mt-1 text-sm text-slate-500">
          Entra con tu nombre de usuario o tu email institucional.
        </p>

        <form className="mt-5 space-y-4" onSubmit={entrar}>
          <div>
            <label className="etiqueta" htmlFor="usuario">
              Usuario o email
            </label>
            <input
              id="usuario"
              className="campo"
              autoComplete="username"
              required
              value={usuario}
              onChange={(evento) => setUsuario(evento.target.value)}
            />
          </div>
          <div>
            <label className="etiqueta" htmlFor="password">
              Contraseña
            </label>
            <input
              id="password"
              type="password"
              className="campo"
              autoComplete="current-password"
              required
              value={password}
              onChange={(evento) => setPassword(evento.target.value)}
            />
          </div>

          {error && (
            <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700" role="alert">
              {error}
            </p>
          )}

          <button className="boton-primario w-full" type="submit" disabled={cargando}>
            {cargando ? 'Entrando…' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  )
}
