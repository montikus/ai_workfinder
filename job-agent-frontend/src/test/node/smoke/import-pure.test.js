import { expect, it } from 'vitest';
import { pureValue } from '../../helpers/pure-module.js';

it('imports a pure local module', () => {
  expect(pureValue).toBe(42);
});
