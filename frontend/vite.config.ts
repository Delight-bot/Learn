import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ command }) => ({
  plugins: [react()],
  // GitHub Pages serves this project at /Learn/; keep local dev at root.
  base: command === 'build' ? '/Learn/' : '/',
}))
