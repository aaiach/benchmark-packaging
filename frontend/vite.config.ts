import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  
  // Build configuration
  build: {
    // Output directory (default: dist)
    outDir: 'dist',
    // Generate source maps for debugging in production (optional)
    sourcemap: false,
    // Minification
    minify: 'esbuild',
    // Chunk size warning limit (kB)
    chunkSizeWarningLimit: 1000,
  },
  
  // Server configuration (development)
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
  },
  
  // Preview configuration (production preview)
  preview: {
    host: '0.0.0.0',
    port: 4173,
  },
})
