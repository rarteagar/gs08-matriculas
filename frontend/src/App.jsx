import { NavLink, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { cerrarSesion, token, usuarioGuardado } from './api'
import Login from './vistas/Login.jsx'
import Panel from './vistas/Panel.jsx'
import Estudiantes from './vistas/Estudiantes.jsx'
import Cursos from './vistas/Cursos.jsx'
import Matriculas from './vistas/Matriculas.jsx'
import Usuarios from './vistas/Usuarios.jsx'

const ENLACES = [
  { a: '/', t: 'Panel', fin: true },
  { a: '/estudiantes', t: 'Estudiantes' },
  { a: '/cursos', t: 'Cursos' },
  { a: '/matriculas', t: 'Matrículas' },
  { a: '/usuarios', t: 'Usuarios', soloAdmin: true },
]

function RutaPrivada({ children }) {
  if (!token()) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  const navegar = useNavigate()
  // Se lee la ubicación para que la cabecera se vuelva a pintar al entrar o salir.
  useLocation()
  const usuario = usuarioGuardado()
  const haySesion = Boolean(token())
  const enlaces = ENLACES.filter((enlace) => !enlace.soloAdmin || usuario?.rol === 'admin')

  function salir() {
    cerrarSesion()
    navegar('/login')
  }

  return (
    <div className="min-h-screen">
      {haySesion && (
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-4 px-5 py-3">
            <div className="mr-2">
              <p className="text-sm font-semibold text-slate-900">GS08 · Matrículas y Notas</p>
              <p className="text-xs text-slate-500">Sistema administrativo · Instituto Privado Horizonte</p>
            </div>
            <nav className="flex flex-1 flex-wrap gap-1" aria-label="Secciones del sistema">
              {enlaces.map((enlace) => (
                <NavLink
                  key={enlace.a}
                  to={enlace.a}
                  end={enlace.fin}
                  className={({ isActive }) =>
                    `rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                      isActive ? 'bg-sky-50 text-sky-800' : 'text-slate-600 hover:bg-slate-100'
                    }`
                  }
                >
                  {enlace.t}
                </NavLink>
              ))}
            </nav>
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-500">
                {usuario ? `${usuario.nombre_completo} (${usuario.rol})` : ''}
              </span>
              <button className="boton-secundario" type="button" onClick={salir}>
                Cerrar sesión
              </button>
            </div>
          </div>
        </header>
      )}

      <main className="mx-auto max-w-6xl px-5 py-6">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <RutaPrivada>
                <Panel />
              </RutaPrivada>
            }
          />
          <Route
            path="/estudiantes"
            element={
              <RutaPrivada>
                <Estudiantes />
              </RutaPrivada>
            }
          />
          <Route
            path="/cursos"
            element={
              <RutaPrivada>
                <Cursos />
              </RutaPrivada>
            }
          />
          <Route
            path="/matriculas"
            element={
              <RutaPrivada>
                <Matriculas />
              </RutaPrivada>
            }
          />
          <Route
            path="/usuarios"
            element={
              <RutaPrivada>
                <Usuarios />
              </RutaPrivada>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
