import { render, screen, fireEvent } from '@testing-library/react'
import axe from 'axe-core'
import { MemoryRouter } from 'react-router-dom'
import { useState } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../App.jsx'
import { Confirmacion, Modal } from '../componentes/Modal.jsx'
import { TablaRecurso } from '../componentes/TablaRecurso.jsx'
import Login from '../vistas/Login.jsx'
import Estudiantes from '../vistas/Estudiantes.jsx'

// Auditoría de accesibilidad (D-30) con axe-core, el mismo motor que usa el addon
// a11y de Storybook. En jsdom no se pueden medir colores ni geometría, así que se
// desactivan las reglas que dependen del navegador real (el contraste de la paleta se
// midió aparte y está en el manual técnico §2.6). Todo lo demás —nombres accesibles,
// roles, etiquetas, estructura de tabla, orden de encabezados— sí se comprueba.
const REGLAS_SIN_NAVEGADOR = {
  'color-contrast': { enabled: false }, // jsdom no calcula colores
  region: { enabled: false }, // fragmentos, no páginas completas
  'landmark-one-main': { enabled: false },
  'page-has-heading-one': { enabled: false },
  bypass: { enabled: false },
  'html-has-lang': { enabled: false },
  'document-title': { enabled: false },
  'meta-viewport': { enabled: false },
}

async function violaciones(contenedor) {
  const resultado = await axe.run(contenedor, { rules: REGLAS_SIN_NAVEGADOR })
  return resultado.violations.map((v) => `${v.id} (${v.help}) -> ${v.nodes.length} nodo(s)`)
}

function Aviso() {
  const [abierto, setAbierto] = useState(false)
  return (
    <>
      <button type="button" onClick={() => setAbierto(true)}>
        Abrir diálogo de prueba
      </button>
      <Modal abierto={abierto} titulo="Ficha del estudiante" onCerrar={() => setAbierto(false)}>
        <p>Contenido del diálogo.</p>
      </Modal>
    </>
  )
}

describe('accesibilidad (axe-core)', () => {
  beforeEach(() => {
    localStorage.clear()
    global.fetch = vi.fn()
  })

  it('el formulario de entrada no tiene violaciones', async () => {
    const { container } = render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    )
    expect(await violaciones(container)).toEqual([])
  })

  it('la tabla de listado no tiene violaciones', async () => {
    const { container } = render(
      <TablaRecurso
        titulo="Estudiantes"
        columnas={['Código', { clave: 'accion', titulo: 'Acciones', alineada: true }]}
        filas={[
          <tr key="1">
            <td>E20260001</td>
            <td className="text-right">
              <button type="button">Editar</button>
            </td>
          </tr>,
        ]}
        cargando={false}
        q=""
        onQ={() => {}}
        onBuscar={() => {}}
        page={1}
        paginas={3}
        total={50}
        onPagina={() => {}}
      />,
    )
    expect(await violaciones(container)).toEqual([])
  })

  it('el diálogo de confirmación no tiene violaciones', async () => {
    const { container } = render(
      <Confirmacion
        abierto
        titulo="Eliminar estudiante"
        mensaje="¿Seguro que quieres eliminarlo?"
        textoConfirmar="Sí, eliminar"
        textoCancelar="No, volver"
        onConfirmar={() => {}}
        onCancelar={() => {}}
      />,
    )
    expect(await violaciones(container)).toEqual([])
  })

  it('el panel con el diálogo abierto no tiene violaciones', async () => {
    const { container } = render(<Aviso />)
    fireEvent.click(screen.getByRole('button', { name: 'Abrir diálogo de prueba' }))
    expect(await violaciones(container)).toEqual([])
  })

  it('la lista de estudiantes con datos no tiene violaciones', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      status: 200,
      text: async () =>
        JSON.stringify({
          total: 1,
          page: 1,
          page_size: 25,
          paginas: 1,
          estudiantes: [
            {
              id: 7,
              codigo: 'E20260001',
              dni: '45123456',
              nombres: 'María',
              apellidos: 'Huamán',
              nombre_completo: 'Huamán, María',
              email: null,
              estado: true,
            },
          ],
        }),
    })
    const { container } = render(<Estudiantes />)
    expect(await screen.findByRole('button', { name: 'Editar a Huamán, María' })).toBeInTheDocument()
    expect(await violaciones(container)).toEqual([])
  })
})

describe('accesibilidad: teclado y foco', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('el foco entra al diálogo, Tab no se escapa y Escape lo cierra devolviendo el foco', () => {
    function ConDosBotones() {
      const [abierto, setAbierto] = useState(false)
      return (
        <>
          <button type="button" onClick={() => setAbierto(true)}>
            Abrir
          </button>
          <Modal abierto={abierto} titulo="Editar curso" onCerrar={() => setAbierto(false)}>
            <button type="button">Guardar</button>
          </Modal>
        </>
      )
    }
    render(<ConDosBotones />)
    const abrir = screen.getByRole('button', { name: 'Abrir' })
    abrir.focus()
    fireEvent.click(abrir)

    // 1) el foco entra al diálogo (primer elemento focalizable: el botón Cerrar)
    const cerrar = screen.getByRole('button', { name: 'Cerrar: Editar curso' })
    expect(document.activeElement).toBe(cerrar)

    // 2) Tab desde el último vuelve al primero (no se sale del diálogo)
    const guardar = screen.getByRole('button', { name: 'Guardar' })
    guardar.focus()
    fireEvent.keyDown(document, { key: 'Tab' })
    expect(document.activeElement).toBe(cerrar)

    // 3) Shift+Tab desde el primero va al último
    fireEvent.keyDown(document, { key: 'Tab', shiftKey: true })
    expect(document.activeElement).toBe(guardar)

    // 4) Escape cierra y el foco vuelve al botón que abrió el diálogo
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(document.activeElement).toBe(abrir)
  })

  it('la app ofrece «Saltar al contenido» y el contenido puede recibir el foco', async () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByRole('link', { name: 'Saltar al contenido' })).toHaveAttribute('href', '#contenido')
    expect(screen.getByRole('main')).toHaveAttribute('id', 'contenido')
  })

  it('la sección actual se marca con aria-current y el menú respeta el rol', async () => {
    localStorage.setItem('gs08.token', 'token-de-prueba')
    localStorage.setItem(
      'gs08.usuario',
      JSON.stringify({ nombre_completo: 'Admin de Prueba', rol: 'admin', nombre_usuario: 'admin' }),
    )
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ total: 0, page: 1, page_size: 25, paginas: 0, cursos: [] }),
    })
    render(
      <MemoryRouter initialEntries={['/cursos']}>
        <App />
      </MemoryRouter>,
    )
    const cursos = await screen.findByRole('link', { name: 'Cursos' })
    expect(cursos).toHaveAttribute('aria-current', 'page')
    expect(screen.getByRole('link', { name: 'Auditoría' })).toBeInTheDocument()
    expect(screen.getByText('Sección Cursos')).toBeInTheDocument()
  })

  it('con rol asistente no se muestran las secciones de administrador', async () => {
    localStorage.setItem('gs08.token', 'token-de-prueba')
    localStorage.setItem(
      'gs08.usuario',
      JSON.stringify({ nombre_completo: 'Asistente de Prueba', rol: 'asistente', nombre_usuario: 'asesora' }),
    )
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ total: 0, page: 1, page_size: 25, paginas: 0, cursos: [] }),
    })
    render(
      <MemoryRouter initialEntries={['/cursos']}>
        <App />
      </MemoryRouter>,
    )
    await screen.findByRole('link', { name: 'Cursos' })
    expect(screen.queryByRole('link', { name: 'Auditoría' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Usuarios' })).not.toBeInTheDocument()
  })
})
