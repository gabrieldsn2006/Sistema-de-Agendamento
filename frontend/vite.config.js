// vite.config.js
import { defineConfig } from 'vite'
import { resolve } from 'path'
 
export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        main:       resolve(__dirname, 'index.html'),
        medicos:    resolve(__dirname, 'medicos.html'),
        consultas:  resolve(__dirname, 'consultas.html'),
        relatorios: resolve(__dirname, 'relatorios.html'),
      },
    },
  },
})
 