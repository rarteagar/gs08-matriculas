// Tabla de la bitácora documental (la que vive en MongoDB). Es presentacional: la
// pantalla de Auditoría le pasa los items y el Storybook también puede usarla.
// Accesibilidad (D-30): título para lectores de pantalla y cabeceras con scope="col".
function momento(iso) {
  if (!iso) return '—'
  const fecha = new Date(iso)
  return Number.isNaN(fecha.getTime()) ? iso : fecha.toLocaleString('es-PE')
}

export function TablaBitacora({ items, cargando = false }) {
  if (cargando) {
    return (
      <p className="mt-4 text-sm text-slate-600" role="status">
        Cargando la bitácora…
      </p>
    )
  }

  return (
    <div className="tarjeta mt-4 overflow-x-auto">
      <table className="tabla">
        <caption className="solo-lectores">Bitácora de operaciones (últimas primero)</caption>
        <thead>
          <tr>
            <th scope="col">Fecha</th>
            <th scope="col">Usuario</th>
            <th scope="col">Acción</th>
            <th scope="col">Entidad</th>
            <th scope="col">Id</th>
            <th scope="col">Resultado</th>
            <th scope="col">Estado</th>
            <th scope="col" className="text-right">
              Duración
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, indice) => (
            <tr key={`${item.pedido_id || 'pedido'}-${indice}`}>
              <td className="text-xs whitespace-nowrap text-slate-500">{momento(item.fecha)}</td>
              <td className="text-sm text-slate-700">
                {item.usuario}
                {item.datos?.rol && item.datos.rol !== '-' ? ` (${item.datos.rol})` : ''}
              </td>
              <td className="text-sm font-medium text-slate-700">{item.accion}</td>
              <td className="text-sm">{item.entidad}</td>
              <td className="font-mono text-xs">{item.entidad_id ?? '—'}</td>
              <td className="text-sm">{item.resultado}</td>
              <td className="font-mono text-xs">{item.datos?.estado ?? '—'}</td>
              <td className="text-right font-mono text-xs">
                {item.datos?.demora_ms != null ? `${item.datos.demora_ms} ms` : '—'}
              </td>
            </tr>
          ))}
          {!items.length && (
            <tr>
              <td colSpan={8} className="py-6 text-center text-slate-500" role="status">
                No hay operaciones registradas con ese filtro.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
