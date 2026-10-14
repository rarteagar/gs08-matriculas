import { Confirmacion, Modal } from './Modal.jsx'

export default {
  title: 'Componentes/Diálogos',
  component: Modal,
  tags: ['autodocs'],
  parameters: {
    docs: {
      description: {
        component:
          'Diálogos propios de la aplicación: se usan para mostrar contenido (boleta, notas) y para confirmar ' +
          'operaciones destructivas. La confirmación nombra la acción en cada botón («No, volver» / «Sí, eliminar») ' +
          'y admite un aviso de error cuando el backend rechaza la operación.',
      },
    },
  },
}

export const ModalConContenido = {
  render: () => (
    <Modal abierto titulo="Notas · Cárdenas Ruiz, Fiorella Milagros en Estadística Aplicada" onCerrar={() => {}}>
      <p className="text-sm text-slate-700">El contenido de la ventana va aquí.</p>
    </Modal>
  ),
}

export const ConfirmacionDeBaja = {
  render: () => (
    <Confirmacion
      abierto
      titulo="Eliminar estudiante"
      mensaje="¿Seguro que quieres eliminar a Cárdenas Ruiz, Fiorella Milagros (E20260012)? Sus matrículas y notas se eliminan con él."
      onConfirmar={() => {}}
      onCancelar={() => {}}
    />
  ),
}

export const ConfirmacionConAvisoDelBackend = {
  render: () => (
    <Confirmacion
      abierto
      titulo="El estudiante tiene matrículas"
      mensaje="Tiene 2 matrícula(s) registrada(s). Si continúas se eliminan también sus matrículas y sus notas."
      textoConfirmar="Sí, eliminar todo"
      error="No se puede eliminar: la matrícula 24 tiene notas registradas."
      onConfirmar={() => {}}
      onCancelar={() => {}}
    />
  ),
}

export const ConfirmacionEnProceso = {
  render: () => (
    <Confirmacion
      abierto
      titulo="Eliminar curso"
      mensaje="¿Seguro que quieres eliminar el curso Base de Datos II (C202)?"
      cargando
      onConfirmar={() => {}}
      onCancelar={() => {}}
    />
  ),
}
