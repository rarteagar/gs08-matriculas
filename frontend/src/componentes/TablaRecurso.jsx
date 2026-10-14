// Tabla de recurso reutilizable: buscador, filtros por props, tabla y paginación.
export function TablaRecurso({
  columnas,
  filas,
  cargando,
  q,
  onQ,
  onBuscar,
  children,
  page = 1,
  paginas = 0,
  total = 0,
  onPagina,
  mensajeVacio = 'No hay registros.',
  singular = 'registro',
}) {
  return (
    <div className="tarjeta mt-4 overflow-x-auto">
      <form
        className="mb-3 flex flex-wrap items-end gap-3"
        onSubmit={(evento) => {
          evento.preventDefault()
          onBuscar()
        }}
      >
        <div className="min-w-56 flex-1">
          <label className="etiqueta" htmlFor="buscar">
            Buscar
          </label>
          <input
            id="buscar"
            className="campo"
            value={q}
            onChange={(evento) => onQ(evento.target.value)}
            placeholder="Código, DNI, nombres o apellidos"
          />
        </div>
        {children}
        <button className="boton-secundario" type="submit">
          Buscar
        </button>
      </form>

      <table className="tabla">
        <thead>
          <tr>
            {columnas.map((columna) => (
              <th key={columna.clave || columna} className={columna.alineada ? 'text-right' : undefined}>
                {columna.titulo || columna}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filas.map((fila) => fila)}
          {!filas.length && (
            <tr>
              <td colSpan={columnas.length} className="py-6 text-center text-slate-500">
                {cargando ? 'Cargando…' : mensajeVacio}
              </td>
            </tr>
          )}
        </tbody>
      </table>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-slate-600">
          {total} {singular}
          {total === 1 ? '' : 's'}
          {paginas > 1 ? ` · página ${page} de ${paginas}` : ''}
        </p>
        {paginas > 1 && (
          <div className="flex gap-2">
            <button
              className="boton-secundario"
              type="button"
              onClick={() => onPagina(page - 1)}
              disabled={page <= 1 || cargando}
            >
              Anterior
            </button>
            <button
              className="boton-secundario"
              type="button"
              onClick={() => onPagina(page + 1)}
              disabled={page >= paginas || cargando}
            >
              Siguiente
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
