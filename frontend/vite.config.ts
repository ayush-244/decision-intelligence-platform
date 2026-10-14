import { fileURLToPath, URL } from 'node:url';

import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      // Mirror the "@/*" -> "src/*" alias declared in tsconfig.
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    // Split large, stable vendor libraries into their own long-cached chunks
    // so app-code changes don't invalidate the whole bundle.
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'data-vendor': ['@tanstack/react-query'],
          'motion-vendor': ['framer-motion'],
        },
      },
    },
  },
  server: {
    port: 5173,
    host: true, // listen on 0.0.0.0 so the dev server works inside Docker
  },
  preview: {
    port: 4173,
    host: true,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: true,
  },
});
