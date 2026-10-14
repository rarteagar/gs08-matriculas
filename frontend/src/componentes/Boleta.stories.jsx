import { Boleta } from './Boleta.jsx'

const boletaReal = {
  estudiante: { id: 12, codigo: 'E20260012', nombre_completo: 'Cárdenas Ruiz, Fiorella Milagros' },
  periodo: '2026-02',
  cursos: [
    { curso_id: 4, codigo_curso: 'C204', curso: 'Estadística Aplicada', creditos: 3, cantidad_notas: 3, nota: 16, nota_texto: '16.00', notas: [] },
    { curso_id: 1, codigo_curso: 'C101', curso: 'Matemática Básica', creditos: 4, cantidad_notas: 0, nota: null, nota_texto: null, notas: [] },
  ],
  creditos_con_notas: 3,
  promedio: 16,
  promedio_texto: '16.00',
  promedio_simple: 16,
}

const sinNotas = {
  estudiante: { id: 7, codigo: 'E20260007', nombre_completo: 'Castillo Neyra, Jorge Luis' },
  periodo: '2026-02',
  cursos: [{ curso_id: 2, codigo_curso: 'C202', curso: 'Base de Datos II', creditos: 3, cantidad_notas: 0, nota: null, nota_texto: null, notas: [] }],
  creditos_con_notas: 0,
  promedio: null,
  promedio_texto: null,
  promedio_simple: null,
}

// El componente consulta la boleta al abrirse: en el Storybook se responde con datos reales del seed.
const conApi = (cuerpo) => (Story) => {
  globalThis.fetch = async () => ({ ok: true, status: 200, text: async () => JSON.stringify(cuerpo) })
  return <Story />
}

export default {
  title: 'Pantallas/Boleta',
  component: Boleta,
  tags: ['autodocs'],
  parameters: {
    docs: {
      description: {
        component:
          'Boleta del estudiante: consume GET /estudiantes/{id}/boleta con el periodo elegido y muestra la nota de ' +
          'cada curso con su cantidad de notas, el promedio ponderado por créditos, el promedio simple y los créditos ' +
          'con notas. Un curso sin notas no cuenta como cero.',
      },
    },
  },
  decorators: [conApi(boletaReal)],
  args: { estudiante: boletaReal.estudiante, onCerrar: () => {} },
}

export const ConNotas = {}
export const SinNotas = { decorators: [conApi(sinNotas)] }
