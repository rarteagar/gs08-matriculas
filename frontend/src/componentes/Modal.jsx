import { useEffect, useId, useRef } from 'react'

// Diálogo propio de la aplicación (no se usan diálogos nativos).
// Accesibilidad (D-30): además de `role="dialog"` y `aria-modal`, el foco entra al
// diálogo al abrirlo, queda atrapado dentro (Tab / Shift+Tab), Escape lo cierra y al
// cerrarse el foco vuelve al elemento que lo abrió. Nada de esto se ve: es para quien
// navega con teclado o con lector de pantalla.
const FOCALIZABLES =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

export function Modal({ abierto, titulo, onCerrar, children, ancho = 'max-w-2xl' }) {
  const caja = useRef(null)
  const idTitulo = useId()

  useEffect(() => {
    if (!abierto) return undefined
    const anterior = document.activeElement
    const nodo = caja.current
    const primeros = nodo?.querySelectorAll(FOCALIZABLES)
    const primero = primeros?.length ? primeros[0] : nodo
    primero?.focus()

    function alTeclear(evento) {
      if (evento.key === 'Escape') {
        onCerrar()
        return
      }
      if (evento.key !== 'Tab' || !nodo) return
      const elementos = [...nodo.querySelectorAll(FOCALIZABLES)]
      if (!elementos.length) {
        evento.preventDefault()
        nodo.focus()
        return
      }
      const inicio = elementos[0]
      const fin = elementos[elementos.length - 1]
      if (evento.shiftKey && document.activeElement === inicio) {
        evento.preventDefault()
        fin.focus()
      } else if (!evento.shiftKey && document.activeElement === fin) {
        evento.preventDefault()
        inicio.focus()
      }
    }

    document.addEventListener('keydown', alTeclear)
    return () => {
      document.removeEventListener('keydown', alTeclear)
      // El foco vuelve a donde estaba: quien abrió el diálogo no se pierde.
      if (anterior instanceof HTMLElement && document.contains(anterior)) anterior.focus()
    }
  }, [abierto, onCerrar])

  if (!abierto) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/40 p-4">
      <div
        ref={caja}
        tabIndex={-1}
        className={`mx-auto mt-8 w-full ${ancho} rounded-xl border border-slate-200 bg-white shadow-lg`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={idTitulo}
      >
        <div className="flex items-center justify-between gap-4 border-b border-slate-200 px-5 py-3">
          <h2 id={idTitulo} className="text-sm font-semibold text-slate-900">
            {titulo}
          </h2>
          <button
            className="boton-secundario px-3! py-1.5! text-xs!"
            type="button"
            onClick={onCerrar}
            aria-label={`Cerrar: ${titulo}`}
          >
            Cerrar
          </button>
        </div>
        <div className="px-5 py-4">{children}</div>
      </div>
    </div>
  )
}

// Confirmación para operaciones destructivas: los botones dicen qué hacen.
export function Confirmacion({
  abierto,
  titulo = 'Confirmar operación',
  mensaje,
  textoConfirmar = 'Sí, eliminar',
  textoCancelar = 'No, volver',
  onConfirmar,
  onCancelar,
  cargando = false,
  error = '',
}) {
  return (
    <Modal abierto={abierto} titulo={titulo} onCerrar={onCancelar} ancho="max-w-lg">
      <p className="text-sm text-slate-700">{mensaje}</p>
      {error && (
        <p className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700" role="alert">
          {error}
        </p>
      )}
      <div className="mt-5 flex flex-wrap justify-end gap-2">
        <button className="boton-secundario" type="button" onClick={onCancelar} disabled={cargando}>
          {textoCancelar}
        </button>
        <button className="boton-primario" type="button" onClick={onConfirmar} disabled={cargando}>
          {cargando ? 'Eliminando…' : textoConfirmar}
        </button>
      </div>
    </Modal>
  )
}
