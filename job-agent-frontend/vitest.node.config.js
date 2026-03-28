import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    include: ['src/test/node/**/*.test.js'],
    environment: 'node',
    pool: 'threads',
    maxWorkers: 1,
    fileParallelism: false,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json-summary'],
      include: ['src/api/**/*.js'],
    },
  },
});
