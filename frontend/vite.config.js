import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],

  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
        ws: true,   // proxy WebSocket connections too
      },
    },
    watch: { usePolling: true },
  },

  define: {
    // Fallback so the app works without a .env file
    'import.meta.env.VITE_WS_URL': JSON.stringify(
      process.env.VITE_WS_URL ?? 'ws://localhost:8000'
    ),
    'import.meta.env.VITE_API_URL': JSON.stringify(
      process.env.VITE_API_URL ?? 'http://localhost:8000'
    ),
  },
})
