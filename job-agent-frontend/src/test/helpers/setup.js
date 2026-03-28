import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

afterEach(() => {
  cleanup();
  if (typeof globalThis.localStorage?.clear === 'function') {
    globalThis.localStorage.clear();
  }
  if (typeof globalThis.sessionStorage?.clear === 'function') {
    globalThis.sessionStorage.clear();
  }
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});
