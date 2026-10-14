import { TablaRecurso } from './TablaRecurso.jsx'
import { Insignia } from './Avisos.jsx'

const estudiantes = [
  { id: 7, codigo: 'E20260007', dni: '51789012', nombre_completo: 'Castillo Neyra, Jorge Luis', email: 'jcastillo@correo.pe', estado: true },
  { id: 12, codigo: 'E20260012', dni: '56234567', nombre_completo: 'Cárdenas Ruiz, Fiorella Milagros', email: 'fcardenas@correo.pe', estado: true },
  { id: 3, codigo: 'E20260003', dni: '45123456', nombre_completo: 'Huamán Quispe, Rosa Elena', email: null, estado: false },
]

export default {
  title: 'Componentes/Tabla de recurso',
  component: TablaRecurso,
  tags: ['autodocs'],
  parameters: {
    docs: {
      description: {
        component:
          'Tabla de listado que se reutiliza en todas las pantallas: buscador, filtros (por children), tabla y ' +
          'paginación con el total de registros. Se alimenta del hook usePaginado.',
      },
    },
  },
}

const columnas = [
  'Código',
  'DNI',
  'Apellidos y nombres',
  'Email',
  'Estado',
  { clave: 'accion', titulo: 'Acciones', alineada: true },
]

const filas = estudiantes.map((estudiante) => (
  <tr key={estudiante.id}>
    <td className="font-mono text-xs">{estudiante.codigo}</td>
    <td className="font-mono text-xs">{estudiante.dni}</td>
    <td className="font-medium text-slate-700">{estudiante.nombre_completo}</td>
    <td className="text-slate-500">{estudiante.email || '—'}</td>
    <td>
      <Insignia estado={estudiante.estado} />
    </td>
    <td className="text-right">
      <button className="boton-secundario px-3! py-1.5! text-xs!" type="button">
        Editar
      </button>
    </td>
  </tr>
))

export const ConDatos = {
  args: {
    columnas,
    filas,
    cargando: false,
    q: '',
    onQ: () => {},
    onBuscar: () => {},
    page: 1,
    paginas: 3,
    total: 62,
    onPagina: () => {},
    singular: 'estudiante',
  },
}

export const Vacia = {
  args: { ...ConDatos.args, filas: [], total: 0, paginas: 0, mensajeVacio: 'No hay estudiantes registrados.' },
}

export const Cargando = {
  args: { ...ConDatos.args, filas: [], total: 0, paginas: 0, cargando: true },
}
