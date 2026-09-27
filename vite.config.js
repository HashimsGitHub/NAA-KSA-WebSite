import { defineConfig } from 'vite';
import { resolve } from 'node:path';
import { readdirSync } from 'node:fs';

const pages = readdirSync(resolve('frontend/pages'))
  .filter((name) => name.endsWith('.html'))
  .map((name) => resolve('frontend/pages', name));

export default defineConfig({
  root: 'frontend',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
    rollupOptions: {
      input: [resolve('frontend/index.html'), ...pages],
    },
  },
});
