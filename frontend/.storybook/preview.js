// Estilos de la aplicación dentro del Storybook: sin esto los componentes
// no se verían con las clases propias (tarjeta, campo, etiqueta, botones…).
import '../src/estilos.css'

/** @type { import('@storybook/react-vite').Preview } */
const preview = {
  parameters: {
    layout: 'padded',
    controls: { matchers: { color: /(background|color)$/i, date: /Date$/i } },
  },
}

export default preview
