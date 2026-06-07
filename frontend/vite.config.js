import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  build: {
    target: 'es2020',
  },
  server: {
    hot: true,
    proxy: {
      '/api': {
        target: 'http://localhost:32200',
        changeOrigin: true
      }
    }
  }
})
