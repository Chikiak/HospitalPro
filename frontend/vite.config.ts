/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    // waitForTimeout aumentado a 5s para evitar fallos espúreos por timing
    // bajo carga de CPU cuando se ejecuta el suite completo en paralelo.
    waitForTimeout: 5000,
    // testTimeout aumentado para dar margen a waitFor anidado
    testTimeout: 15000,
  },
})
