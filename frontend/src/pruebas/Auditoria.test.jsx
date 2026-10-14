import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import Auditoria from '../vistas/Auditoria.jsx'

// La pantalla consume GET /api/v1/auditoria (bitácora en MongoDB) y la boleta
// archivada. Se prueba con `fetch` simulado, sin backend.
const BITACORA = {
  activa: true,
  total: 2,
  total_bitacora: 24,
  items: [
    {
      fecha: '2026-10-13T23:41:07.512000+00:00',
      accion: 'crear',
      entidad: 'estudiante',
      entidad_id: null,
      usuario: 'admin',
      resultado: 'ok',
      pedido_id: '9f2c1ab43d01',
      datos: { rol: 'admin', estado: 201, demora_ms: 30.7, cuerpo: { codigo: 'PZ1000' } },
    },
    {
      fecha: '2026-10-13T23:41:09.900000+00:00',
      accion: 'eliminar',
      entidad: 'nota',
      entidad_id: 41,
      usuario: 'asesora',
      resultado: 'error 403',
      pedido_id: '0f9e8d7c6b5a',
      datos: { rol: 'asistente', estado: 403, demora_ms: 3.9 },
    },
  ],
  detalle: null,
}

function respuesta(cuerpo, estado = 200) {
  return { ok: estado < 400, status: estado, text: async () => JSON.stringify(cuerpo) }
}

describe('pantalla de auditoría', () => {
  beforeEach(() => {
    localStorage.clear()
    localStorage.setItem('gs08.token', 'token-de-prueba')
    global.fetch = vi.fn()
  })

  it('muestra las operaciones de la bitácora con su usuario y resultado', async () => {
    global.fetch.mockResolvedValue(respuesta(BITACORA))
    render(<Auditoria />)

    expect(await screen.findByRole('table')).toBeInTheDocument()
    expect(screen.getByRole('cell', { name: 'estudiante' })).toBeInTheDocument()
    expect(screen.getByRole('cell', { name: 'error 403' })).toBeInTheDocument()
    expect(screen.getByText(/2 operación\(es\) con ese filtro · 24 en la bitácora/)).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Usuario' })).toBeInTheDocument()
    expect(global.fetch.mock.calls[0][0]).toContain('/auditoria?limite=25')
  })

  it('manda los filtros a la API y avisa cuando la bitácora está apagada', async () => {
    global.fetch.mockResolvedValue(respuesta({ ...BITACORA, activa: false, items: [], total: 0, total_bitacora: 0, detalle: 'La bitácora documental está apagada.' }))
    render(<Auditoria />)

    expect(await screen.findByText(/bitácora está apagada/i)).toBeInTheDocument()
    expect(screen.getByText('La bitácora documental está apagada.')).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Entidad'), { target: { value: 'nota' } })
    fireEvent.change(screen.getByLabelText('Acción'), { target: { value: 'eliminar' } })
    expect(global.fetch.mock.calls.at(-1)[0]).toContain('entidad=nota')
    expect(global.fetch.mock.calls.at(-1)[0]).toContain('accion=eliminar')
  })

  it('consulta la boleta archivada de un estudiante y periodo', async () => {
    global.fetch
      .mockResolvedValueOnce(respuesta(BITACORA))
      .mockResolvedValueOnce(
        respuesta({
          activa: true,
          estudiante_id: 7,
          periodo: '2026-02',
          archivada: true,
          generado_en: '2026-10-13T23:41:07+00:00',
          generado_por: 'admin',
          boleta: { promedio_texto: '16.00', cursos: [{}, {}, {}] },
        }),
      )
    render(<Auditoria />)
    await screen.findByRole('table')

    fireEvent.change(screen.getByLabelText('Estudiante (id)'), { target: { value: '7' } })
    fireEvent.submit(screen.getByRole('button', { name: 'Ver archivada' }).closest('form'))

    expect(await screen.findByText(/16.00/)).toBeInTheDocument()
    expect(screen.getByText('admin')).toBeInTheDocument()
    expect(global.fetch.mock.calls.at(-1)[0]).toContain('/estudiantes/7/boleta/archivada?periodo=2026-02')
  })

  it('avisa cuando no hay boleta archivada', async () => {
    global.fetch
      .mockResolvedValueOnce(respuesta(BITACORA))
      .mockResolvedValueOnce(respuesta({ activa: true, archivada: false, boleta: null }))
    render(<Auditoria />)
    await screen.findByRole('table')
    fireEvent.change(screen.getByLabelText('Estudiante (id)'), { target: { value: '99' } })
    fireEvent.submit(screen.getByRole('button', { name: 'Ver archivada' }).closest('form'))
    expect(await screen.findByText(/No hay una boleta archivada/i)).toBeInTheDocument()
  })

  it('si la consulta falla no afirma que la bitácora esté apagada', async () => {
    // Pasó en la verificación real: un 401 (sesión vencida) se contaba como
    // "la bitácora está apagada", que es una afirmación distinta y falsa.
    global.fetch.mockResolvedValue(respuesta({ detail: 'La sesión expiró. Vuelve a iniciar sesión.' }, 401))
    render(<Auditoria />)

    expect(await screen.findByText('La sesión expiró. Vuelve a iniciar sesión.')).toBeInTheDocument()
    expect(screen.getByText('No se pudo consultar la bitácora.')).toBeInTheDocument()
    expect(screen.queryByText(/bitácora está apagada/i)).not.toBeInTheDocument()
  })
})
