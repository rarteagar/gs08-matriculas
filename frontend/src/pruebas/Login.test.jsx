import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const login = vi.fn()
vi.mock('../api', () => ({
  api: { login: (...args) => login(...args) },
  guardarSesion: vi.fn(),
  token: () => null,
}))

const { default: Login } = await import('../vistas/Login.jsx')

describe('pantalla de inicio de sesión', () => {
  beforeEach(() => {
    login.mockReset()
    localStorage.clear()
  })

  function pintar() {
    return render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    )
  }

  it('pide usuario y contraseña y llama al API', async () => {
    login.mockResolvedValue({ access_token: 'x', usuario: { nombre_completo: 'Admin', rol: 'admin' } })
    pintar()
    fireEvent.change(screen.getByLabelText(/usuario o email/i), { target: { value: 'admin' } })
    fireEvent.change(screen.getByLabelText(/contraseña/i), { target: { value: 'clave-de-prueba' } })
    fireEvent.click(screen.getByRole('button', { name: /entrar/i }))
    await waitFor(() => expect(login).toHaveBeenCalledWith('admin', 'clave-de-prueba'))
  })

  it('muestra el mensaje de error del backend dentro de la pantalla', async () => {
    login.mockRejectedValue(new Error('Usuario o contraseña incorrectos.'))
    pintar()
    fireEvent.change(screen.getByLabelText(/usuario o email/i), { target: { value: 'admin' } })
    fireEvent.change(screen.getByLabelText(/contraseña/i), { target: { value: 'mala' } })
    fireEvent.click(screen.getByRole('button', { name: /entrar/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Usuario o contraseña incorrectos.')
  })
})
