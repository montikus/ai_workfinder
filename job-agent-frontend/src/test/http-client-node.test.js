import { expect, it, vi } from 'vitest';

it('adds an authorization header when a token exists', async () => {
  vi.stubGlobal('localStorage', {
    getItem: vi.fn(() => 'token-123'),
  });

  const { klientHttp } = await import('../api/http.js');
  const handler = klientHttp.interceptors.request.handlers.at(-1).fulfilled;
  const config = await handler({ headers: {} });

  expect(config.headers.Authorization).toBe('Bearer token-123');
});

it('sends GET, POST, and PUT requests through fetch', async () => {
  vi.stubGlobal('localStorage', {
    getItem: vi.fn(() => null),
  });
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    headers: new Headers(),
    text: () => Promise.resolve('{"ok":true}'),
  });
  vi.stubGlobal('fetch', fetchMock);

  const { klientHttp } = await import('../api/http.js');

  await klientHttp.get('/api/profile');
  await klientHttp.post('/api/login', { email: 'user@example.com' });
  await klientHttp.put('/api/profile', { name: 'Roman' });

  expect(fetchMock).toHaveBeenNthCalledWith(
    1,
    'http://localhost:8001/api/profile',
    expect.objectContaining({ method: 'GET' })
  );
  expect(fetchMock).toHaveBeenNthCalledWith(
    2,
    'http://localhost:8001/api/login',
    expect.objectContaining({ method: 'POST' })
  );
  expect(fetchMock).toHaveBeenNthCalledWith(
    3,
    'http://localhost:8001/api/profile',
    expect.objectContaining({ method: 'PUT' })
  );
});

it('sends FormData without forcing a JSON content type', async () => {
  vi.stubGlobal('localStorage', {
    getItem: vi.fn(() => null),
  });
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    headers: new Headers(),
    text: () => Promise.resolve('plain text'),
  });
  vi.stubGlobal('fetch', fetchMock);

  const { klientHttp } = await import('../api/http.js');
  const formData = new FormData();
  formData.append('resume', 'file-content');

  const response = await klientHttp.post('/api/upload_resume', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  const headers = fetchMock.mock.calls[0][1].headers;

  expect(headers.get('Content-Type')).toBeNull();
  expect(response.data).toBe('plain text');
});

it('throws an error with response details for non-OK responses', async () => {
  vi.stubGlobal('localStorage', {
    getItem: vi.fn(() => null),
  });
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      headers: new Headers(),
      text: () => Promise.resolve('{"detail":"bad request"}'),
    })
  );

  const { klientHttp } = await import('../api/http.js');

  await expect(klientHttp.get('/api/profile')).rejects.toMatchObject({
    message: 'HTTP 400',
    response: {
      status: 400,
      data: { detail: 'bad request' },
    },
  });
});
