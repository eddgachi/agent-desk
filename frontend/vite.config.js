import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],

  server: {
    // 0.0.0.0 is REQUIRED inside Docker so the server is reachable from outside
    host: '0.0.0.0',
    port: 5173,

    // Your browser will now hit http://localhost:8000/api directly
    // based on our changes in src/api/client.js, bypassing this proxy.
    // We'll keep the proxy here pointing to 'backend' (not 127.0.0.1) 
    // as a fallback if you ever want to use relative paths again.
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
    watch: {
      usePolling: true,
    },
  },
})