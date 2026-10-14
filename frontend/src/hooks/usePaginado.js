import { useCallback, useEffect, useState } from 'react'

// Listado paginado contra el API: recibe la función que pide la página y la clave
// de la colección en la respuesta (estudiantes, cursos, matriculas…).
// Devuelve los items, el total, la página actual, las páginas y cómo recargar.
export function usePaginado(pedir, clave, filtros = {}, tamano = 25) {
  const [items, setItems] = useState([])
  const [meta, setMeta] = useState({ total: 0, page: 1, paginas: 0 })
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const consulta = JSON.stringify(filtros)

  const cargar = useCallback(
    async (page = 1) => {
      setCargando(true)
      setError('')
      try {
        const datos = await pedir({ ...JSON.parse(consulta), page, page_size: tamano })
        setItems(datos[clave] || [])
        setMeta({ total: datos.total, page: datos.page, paginas: datos.paginas })
      } catch (fallo) {
        setError(fallo.message)
      } finally {
        setCargando(false)
      }
    },
    [pedir, clave, consulta, tamano],
  )

  useEffect(() => {
    cargar(1)
  }, [cargar])

  return { items, ...meta, cargando, error, setError, cargar }
}
