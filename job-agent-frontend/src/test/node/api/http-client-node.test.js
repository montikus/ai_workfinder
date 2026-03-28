import { beforeEach, expect, it, vi } from 'vitest';

function createStorage(token = null) {
  return {
    getItem: vi.fn((key) => (key === 'token' ? token : null)),
    clear: vi.fn(),
  };
}

function mockResponse({ ok = true, status = 200, text = '', headers = new Headers() } = {}) {
  return {
    ok,
    status,
    headers,
    text: () => Promise.resolve(text),
  };
}

async function importHttpModule({ token = null, apiUrl, fetchMock } = {}) {
  vi.resetModules();

  if (apiUrl !== undefined) {
    vi.stubGlobal('__APP_API_URL__', apiUrl);
  }

  vi.stubGlobal('localStorage', createStorage(token));

  if (fetchMock) {
    vi.stubGlobal('fetch', fetchMock);
  }

  return import('../../../api/http.js');
}

beforeEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.resetModules();
});

it('adds an authorization header when a token exists', async () => {
  const { klientHttp } = await importHttpModule({ token: 'token-123' });
  const handler = klientHttp.interceptors.request.handlers.at(-1).fulfilled;
  const config = await handler({ headers: {} });

  expect(config.headers.Authorization).toBe('Bearer token-123');
});

it('keeps the original request config when there is no token', async () => {
  const { klientHttp } = await importHttpModule();
  const handler = klientHttp.interceptors.request.handlers.at(-1).fulfilled;
  const config = { headers: { 'X-Test': '1' } };

  const result = await handler(config);

  expect(result).toBe(config);
  expect(result.headers['X-Test']).toBe('1');
});

it('uses a custom API base URL when provided at runtime', async () => {
  const fetchMock = vi.fn().mockResolvedValue(mockResponse({ text: '{"ok":true}' }));
  const { klientHttp } = await importHttpModule({
    apiUrl: 'https://api.example.test',
    fetchMock,
  });

  await klientHttp.get('/api/profile');

  expect(klientHttp.baseURL).toBe('https://api.example.test');
  expect(fetchMock).toHaveBeenCalledWith(
    'https://api.example.test/api/profile',
    expect.objectContaining({ method: 'GET' })
  );
});

it('sends GET, POST, and PUT requests through fetch and serializes JSON payloads', async () => {
  const fetchMock = vi.fn().mockResolvedValue(mockResponse({ text: '{"ok":true}' }));
  const { klientHttp } = await importHttpModule({ fetchMock });

  await klientHttp.get('/api/profile');
  await klientHttp.post('/api/login', { email: 'user@example.com' });
  await klientHttp.put('/api/profile', { name: 'Roman' });

  expect(fetchMock).toHaveBeenNthCalledWith(
    1,
    'http://localhost:8001/api/profile',
    expect.objectContaining({ method: 'GET', body: undefined })
  );
  expect(fetchMock).toHaveBeenNthCalledWith(
    2,
    'http://localhost:8001/api/login',
    expect.objectContaining({
      method: 'POST',
      body: '{"email":"user@example.com"}',
    })
  );
  expect(fetchMock.mock.calls[1][1].headers.get('Content-Type')).toBe('application/json');
  expect(fetchMock).toHaveBeenNthCalledWith(
    3,
    'http://localhost:8001/api/profile',
    expect.objectContaining({
      method: 'PUT',
      body: '{"name":"Roman"}',
    })
  );
});

it('preserves an explicit JSON content type and survives interceptors without handlers or return values', async () => {
  const fetchMock = vi.fn().mockResolvedValue(mockResponse({ text: '' }));
  const { klientHttp } = await importHttpModule({ fetchMock });
  klientHttp.interceptors.request.handlers.push({});
  klientHttp.interceptors.request.use(() => undefined);

  const response = await klientHttp.post(
    '/api/profile',
    { name: 'Roman' },
    { headers: { 'Content-Type': 'application/merge-patch+json' } }
  );

  expect(fetchMock.mock.calls[0][1].headers.get('Content-Type')).toBe('application/merge-patch+json');
  expect(response.data).toBeNull();
});

it('sends FormData without forcing a JSON content type and returns plain text responses', async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    mockResponse({
      text: 'plain text',
      headers: new Headers({ 'X-Test': '1' }),
    })
  );
  const { klientHttp } = await importHttpModule({ fetchMock });
  const formData = new FormData();
  formData.append('resume', 'file-content');

  const response = await klientHttp.post('/api/upload_resume', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  const headers = fetchMock.mock.calls[0][1].headers;

  expect(headers.get('Content-Type')).toBeNull();
  expect(fetchMock.mock.calls[0][1].body).toBe(formData);
  expect(response.data).toBe('plain text');
  expect(response.headers.get('X-Test')).toBe('1');
});

it('throws an error with parsed JSON details for non-OK responses', async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    mockResponse({
      ok: false,
      status: 400,
      text: '{"detail":"bad request"}',
    })
  );
  const { klientHttp } = await importHttpModule({ fetchMock });

  await expect(klientHttp.get('/api/profile')).rejects.toMatchObject({
    message: 'HTTP 400',
    response: {
      status: 400,
      data: { detail: 'bad request' },
    },
  });
});

it('throws an error with plain-text details when the error payload is not JSON', async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    mockResponse({
      ok: false,
      status: 503,
      text: 'service unavailable',
    })
  );
  const { klientHttp } = await importHttpModule({ fetchMock });

  await expect(klientHttp.get('/api/profile')).rejects.toMatchObject({
    message: 'HTTP 503',
    response: {
      status: 503,
      data: 'service unavailable',
    },
  });
});
