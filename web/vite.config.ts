import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';
export default defineConfig({
  plugins: [tailwindcss()],
  build: {
    outDir: '../assets/workbench',
    emptyOutDir: true,
    sourcemap: false,
    license: { fileName: 'THIRD_PARTY_NOTICES.md' },
  },
});
