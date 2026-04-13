import react from '@vitejs/plugin-react';
import { configDefaults, defineConfig } from 'vitest/config';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'happy-dom',
    include: ['src/test/dom/**/*.test.{js,jsx}'],
    setupFiles: './src/test/helpers/setup.js',
    css: true,
    pool: 'threads',
    maxWorkers: 2,
    exclude: [...configDefaults.exclude, 'src/test/node/**'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json-summary'],
      include: ['src/**/*.{js,jsx}'],
      exclude: ['src/**/*.css', 'src/assets/**', 'src/main.jsx', 'src/test/**'],
      thresholds: {
        lines: 90,
        statements: 90,
        functions: 90,
        branches: 80,
      },
    },
  },
});
