import { useEffect } from 'react'

// Diálogo propio de la aplicación (no se usan diálogos nativos).
export function Modal({ abierto, titulo, onCerrar, children, ancho = 'max-w-2xl' }) {
  useEffect(() => {
    if (!abierto) return undefined
    function alTeclear(evento) {
      if (evento.key === 'Escape') onCerrar()
    }
    document.addEventListener('keydown', alTeclear)
    return () => document.removeEventListener('keydown', alTeclear)
  }, [abierto, onCerrar])

  if (!abierto) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/40 p-4">
      <div
        className={`mx-auto mt-8 w-full ${ancho} rounded-xl border border-slate-200 bg-white shadow-lg`}
        role="dialog"
        aria-modal="true"
        aria-label={titulo}
      >
        <div className="flex items-center justify-between gap-4 border-b border-slate-200 px-5 py-3">
          <h2 className="text-sm font-semibold text-slate-900">{titulo}</h2>
          <button className="boton-secundario px-3! py-1.5! text-xs!" type="button" onClick={onCerrar}>
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
