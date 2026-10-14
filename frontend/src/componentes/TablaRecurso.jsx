import { useId } from 'react'

// Tabla de recurso reutilizable: buscador, filtros por props, tabla y paginación.
// Accesibilidad (D-30): la tabla lleva título para lectores de pantalla, las cabeceras
// van con `scope="col"`, el resultado de la búsqueda se anuncia (`role="status"`), el
// estado de carga con `aria-busy` y la paginación es una `nav` con botones que dicen
// a dónde llevan.
export function TablaRecurso({
  titulo = 'Listado',
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
  const idBuscar = useId()
  return (
    <div className="tarjeta mt-4 overflow-x-auto">
      <form
        className="mb-3 flex flex-wrap items-end gap-3"
        role="search"
        aria-label={`Buscar en ${titulo}`}
        onSubmit={(evento) => {
          evento.preventDefault()
          onBuscar()
        }}
      >
        <div className="min-w-56 flex-1">
          <label className="etiqueta" htmlFor={idBuscar}>
            Buscar
          </label>
          <input
            id={idBuscar}
            type="search"
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

      <table className="tabla" aria-busy={cargando || undefined}>
        <caption className="solo-lectores">{titulo}</caption>
        <thead>
          <tr>
            {columnas.map((columna) => (
              <th
                key={columna.clave || columna}
                scope="col"
                className={columna.alineada ? 'text-right' : undefined}
              >
                {columna.titulo || columna}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filas.map((fila) => fila)}
          {!filas.length && (
            <tr>
              <td colSpan={columnas.length} className="py-6 text-center text-slate-500" role="status">
                {cargando ? 'Cargando…' : mensajeVacio}
              </td>
            </tr>
          )}
        </tbody>
      </table>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-slate-600" role="status">
          {total} {singular}
          {total === 1 ? '' : 's'}
          {paginas > 1 ? ` · página ${page} de ${paginas}` : ''}
        </p>
        {paginas > 1 && (
          <nav className="flex gap-2" aria-label="Paginación">
            <button
              className="boton-secundario"
              type="button"
              onClick={() => onPagina(page - 1)}
              disabled={page <= 1 || cargando}
              aria-label="Página anterior"
            >
              Anterior
            </button>
            <button
              className="boton-secundario"
              type="button"
              onClick={() => onPagina(page + 1)}
              disabled={page >= paginas || cargando}
              aria-label="Página siguiente"
            >
              Siguiente
            </button>
          </nav>
        )}
      </div>
    </div>
  )
}
