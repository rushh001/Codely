import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  // Tauri expects a fixed port and disables host checking
  server: {
    port: 5173,
    host: true,
    strictPort: true,   // Tauri needs a predictable port
  },

  // Prevent Vite from obscuring Rust errors in dev
  clearScreen: false,

  // Tauri uses env vars to tell Vite which features to enable
  envPrefix: ['VITE_', 'TAURI_'],

  build: {
    // Tauri supports ES modules & this keeps compatibility
    target: ['es2021', 'chrome105', 'safari15'],
    minify: !process.env.TAURI_DEBUG ? 'esbuild' : false,
    sourcemap: !!process.env.TAURI_DEBUG,
  },
});
