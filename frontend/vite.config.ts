import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  const env = loadEnv(mode, process.cwd(), '')

  // Determinar si estamos en modo subpath (producción con dominio propio)
  const useSubpath = env.VITE_USE_SUBPATH === 'true'
  const basePath = useSubpath ? '/intranet/cipa/' : '/'

  return {
    // Base path para deployment con subpath
    base: basePath,

    plugins: [react()],

    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },

    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:5000',
          changeOrigin: true,
        },
      },
    },

    build: {
      outDir: 'dist',
      // Generar sourcemaps solo en desarrollo
      sourcemap: mode === 'development',
      // Optimizaciones para producción
      minify: 'terser',
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom', 'react-router-dom'],
            ui: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
          },
        },
      },
    },
  }
})
