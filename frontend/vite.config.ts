import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:9500',
        changeOrigin: true
      },
      '/socket.io': {
        target: 'http://localhost:9500',
        ws: true,
        changeOrigin: true
      }
    }
  }
})
