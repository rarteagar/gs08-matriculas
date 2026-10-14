import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// El SPA se sirve detrás de nginx, en el mismo origen que el API (/api/v1 → proxy).
// En desarrollo, `npm run dev` manda /api al API local para no depender de nginx.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/pruebas/configuracion.js',
    css: false,
  },
})
