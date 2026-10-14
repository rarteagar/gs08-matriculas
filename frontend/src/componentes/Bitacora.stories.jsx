import { TablaBitacora } from './Bitacora.jsx'

const ITEMS = [
  {
    fecha: '2026-10-13T23:41:07.512000+00:00',
    accion: 'crear',
    entidad: 'estudiante',
    entidad_id: null,
    usuario: 'admin',
    resultado: 'ok',
    pedido_id: '9f2c1ab43d01',
    datos: { rol: 'admin', ruta: '/api/v1/estudiantes', estado: 201, demora_ms: 30.7, cuerpo: { codigo: 'PZ1000' } },
  },
  {
    fecha: '2026-10-13T23:41:08.101000+00:00',
    accion: 'editar',
    entidad: 'matricula',
    entidad_id: 12,
    usuario: 'admin',
    resultado: 'ok',
    pedido_id: '1a2b3c4d5e6f',
    datos: { rol: 'admin', ruta: '/api/v1/matriculas/12', estado: 200, demora_ms: 12.4 },
  },
  {
    fecha: '2026-10-13T23:41:09.900000+00:00',
    accion: 'eliminar',
    entidad: 'nota',
    entidad_id: 41,
    usuario: 'asesora',
    resultado: 'error 403',
    pedido_id: '0f9e8d7c6b5a',
    datos: { rol: 'asistente', ruta: '/api/v1/notas/41', estado: 403, demora_ms: 3.9 },
  },
]

export default {
  title: 'Componentes/Bitácora',
  component: TablaBitacora,
  tags: ['autodocs'],
  parameters: {
    docs: {
      description: {
        component:
          'Tabla de la bitácora documental (MongoDB): quién hizo qué, desde qué petición, con qué resultado y en cuánto tiempo. La alimenta la vista Auditoría.',
      },
    },
  },
}

export const ConRegistros = { args: { items: ITEMS } }

export const Vacia = {
  args: { items: [] },
  parameters: { docs: { description: { story: 'Sin operaciones con ese filtro: la tabla lo dice.' } } },
}

export const Cargando = { args: { items: [], cargando: true } }
