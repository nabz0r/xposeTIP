import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // S232 — consent router lives at FastAPI root (matches Google's
      // Authorized redirect URI verbatim, so it cannot share /api/v1).
      '/consent': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
