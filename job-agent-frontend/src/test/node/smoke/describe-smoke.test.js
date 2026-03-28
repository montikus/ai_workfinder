import { describe, expect, it, vi } from 'vitest';

describe('describe smoke', () => {
  it('works', async () => {
    const fn = vi.fn();
    fn();
    expect(fn).toHaveBeenCalledTimes(1);
  });
});
