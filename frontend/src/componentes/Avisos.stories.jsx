import { Avisos, Insignia } from './Avisos.jsx'

export default {
  title: 'Componentes/Avisos',
  component: Avisos,
  tags: ['autodocs'],
  parameters: {
    docs: {
      description: {
        component:
          'Mensajes en línea de la interfaz. Los errores del API se muestran aquí con el texto que devuelve el ' +
          'backend, nunca con diálogos nativos del navegador.',
      },
    },
  },
  argTypes: {
    error: { control: 'text', description: 'Mensaje de error (fondo rojo, role="alert")' },
    aviso: { control: 'text', description: 'Confirmación de una operación correcta (fondo verde, role="status")' },
  },
}

export const SoloError = { args: { error: 'Ya existe una matrícula para ese estudiante y curso en el periodo.' } }
export const SoloAviso = { args: { aviso: 'Estudiante E20260007 registrado.' } }
export const Ambos = { args: { error: 'El DNI debe tener 8 dígitos.', aviso: 'Curso C204 actualizado.' } }
export const SinMensajes = { args: {} }

export const Insignias = {
  render: () => (
    <div className="flex flex-wrap items-center gap-3">
      <Insignia estado={true} />
      <Insignia estado="activa" />
      <Insignia estado="retirado" />
      <Insignia estado={false} />
    </div>
  ),
}
