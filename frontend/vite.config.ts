import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Obtener base path de variable de entorno
const BASE_PATH = process.env.VITE_BASE_PATH || '';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: BASE_PATH || '/',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu', '@radix-ui/react-label'],
        },
      },
    },
  },
})
