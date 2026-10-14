// Avisos en línea: los mensajes del API se muestran dentro de la interfaz,
// nunca con diálogos nativos del navegador.
export function Avisos({ error, aviso }) {
  return (
    <>
      {error && (
        <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700" role="alert">
          {error}
        </p>
      )}
      {aviso && (
        <p className="mt-4 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-800" role="status">
          {aviso}
        </p>
      )}
    </>
  )
}

// Insignia de estado. Acepta los estados del API («activa», «retirado») y los
// booleanos de estado (activo / inactivo).
export function Insignia({ estado }) {
  let clase = 'insignia-inactivo'
  let texto = 'Inactivo'
  if (estado === true || estado === 'activo' || estado === 'activa') {
    clase = 'insignia-activa'
    texto = estado === 'activa' ? 'Activa' : 'Activo'
  } else if (estado === 'retirado') {
    clase = 'insignia-retirado'
    texto = 'Retirado'
  }
  return <span className={clase}>{texto}</span>
}
