import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { Insignia } from '../componentes/Avisos.jsx'
import { Confirmacion } from '../componentes/Modal.jsx'

describe('insignia de estado', () => {
  it('traduce los estados del API', () => {
    const { rerender } = render(<Insignia estado={true} />)
    expect(screen.getByText('Activo')).toBeInTheDocument()
    rerender(<Insignia estado={false} />)
    expect(screen.getByText('Inactivo')).toBeInTheDocument()
    rerender(<Insignia estado="activa" />)
    expect(screen.getByText('Activa')).toBeInTheDocument()
    rerender(<Insignia estado="retirado" />)
    expect(screen.getByText('Retirado')).toBeInTheDocument()
  })
})

describe('confirmación propia (sin diálogos nativos)', () => {
  it('los botones dicen qué hacen y el de confirmar avisa al componente', () => {
    const alConfirmar = vi.fn()
    const alCancelar = vi.fn()
    render(
      <Confirmacion
        abierto
        titulo="Eliminar estudiante"
        mensaje="¿Seguro que quieres eliminarlo?"
        textoConfirmar="Sí, eliminar"
        textoCancelar="No, volver"
        onConfirmar={alConfirmar}
        onCancelar={alCancelar}
      />,
    )
    expect(screen.getByRole('dialog', { name: 'Eliminar estudiante' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Sí, eliminar' }))
    expect(alConfirmar).toHaveBeenCalled()
    fireEvent.click(screen.getByRole('button', { name: 'No, volver' }))
    expect(alCancelar).toHaveBeenCalled()
  })
})
