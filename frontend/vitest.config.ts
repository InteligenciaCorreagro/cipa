import { defineConfig } from 'vitest/config'
import path from 'path'

export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    testDir: './tests/unit',
    environment: 'jsdom',
    setupFiles: './tests/setupTests.ts',
    css: true,
  },
})
