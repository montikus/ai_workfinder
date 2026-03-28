import { expect, it } from 'vitest';

it('dynamically imports http module', async () => {
  const module = await import('../api/http.js');
  expect(Boolean(module.klientHttp)).toBe(true);
});
