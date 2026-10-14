import { Notas } from './Notas.jsx'

const notas = [
  { id: 1, matricula_id: 24, tipo: 'practica', numero: 1, nota: 14, nota_texto: '14.00', fecha_registro: '2026-08-20', observacion: null },
  { id: 2, matricula_id: 24, tipo: 'parcial', numero: 1, nota: 16, nota_texto: '16.00', fecha_registro: '2026-09-15', observacion: null },
  { id: 3, matricula_id: 24, tipo: 'final', numero: 1, nota: 18, nota_texto: '18.00', fecha_registro: '2026-10-01', observacion: 'Examen de recuperación de la práctica' },
]

const conApi = (cuerpo) => (Story) => {
  globalThis.fetch = async () => ({ ok: true, status: 200, text: async () => JSON.stringify(cuerpo) })
  return <Story />
}

export default {
  title: 'Pantallas/Notas de una matrícula',
  component: Notas,
  tags: ['autodocs'],
  parameters: {
    docs: {
      description: {
        component:
          'Notas de una matrícula: lista, registra, edita y elimina notas (practica | parcial | final, número ≥ 1 y ' +
          'nota de 0 a 20). Los rechazos del backend (nota fuera de rango, duplicado, matrícula retirada) se muestran ' +
          'en el diálogo con el mensaje del servidor.',
      },
    },
  },
  decorators: [conApi(notas)],
  args: {
    matricula: { id: 24, estudiante: 'Cárdenas Ruiz, Fiorella Milagros', curso: 'Estadística Aplicada' },
    onCerrar: () => {},
    onCambio: () => {},
  },
}

export const ConNotas = {}
export const SinNotas = { decorators: [conApi([])] }
