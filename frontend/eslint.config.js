import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'

// Configuración plana (eslint 9). Cubre el SPA en src/ y las pruebas de src/pruebas.
export default [
  { ignores: ['dist', 'node_modules', 'storybook-static'] },
  {
    files: ['**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 'latest',
      globals: { ...globals.browser, ...globals.node },
      parserOptions: {
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
      },
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...js.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      'no-unused-vars': ['error', { varsIgnorePattern: '^[A-Z_]' }],
      // La carga de datos al montar la pantalla es el patrón de este SPA:
      // el estado se llena en una función asíncrona, no en el cuerpo del efecto.
      'react-hooks/set-state-in-effect': 'off',
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
    },
  },
  {
    files: ['**/*.test.{js,jsx}', 'src/pruebas/**'],
    languageOptions: { globals: { ...globals.browser, ...globals.node, ...globals.vitest } },
  },
]
