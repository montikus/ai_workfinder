import { expect, it, vi } from 'vitest';

it('routes auth requests through the shared client', async () => {
  const { klientHttp } = await import('../../../api/http.js');
  const { rejestracja, logowanie, pobierzProfil, aktualizujProfil } = await import('../../../api/auth.js');
  const postSpy = vi.spyOn(klientHttp, 'post').mockResolvedValue({ data: {} });
  const getSpy = vi.spyOn(klientHttp, 'get').mockResolvedValue({ data: {} });
  const putSpy = vi.spyOn(klientHttp, 'put').mockResolvedValue({ data: {} });

  await rejestracja({ email: 'user@example.com' });
  await logowanie({ email: 'user@example.com' });
  await pobierzProfil();
  await aktualizujProfil({ name: 'Roman' });

  expect(postSpy).toHaveBeenNthCalledWith(1, '/api/register', { email: 'user@example.com' });
  expect(postSpy).toHaveBeenNthCalledWith(2, '/api/login', { email: 'user@example.com' });
  expect(getSpy).toHaveBeenCalledWith('/api/profile');
  expect(putSpy).toHaveBeenCalledWith('/api/profile', { name: 'Roman' });
});

it('routes job, application, and gmail requests through the shared client', async () => {
  const { klientHttp } = await import('../../../api/http.js');
  const { rozpocznijWyszukiwanie, pobierzOferty, pobierzStatusWyszukiwania } = await import('../../../api/jobs.js');
  const { pobierzAplikacje } = await import('../../../api/applications.js');
  const { polaczGmail } = await import('../../../api/gmail.js');
  const postSpy = vi.spyOn(klientHttp, 'post').mockResolvedValue({ data: {} });
  const getSpy = vi.spyOn(klientHttp, 'get').mockResolvedValue({ data: {} });

  await rozpocznijWyszukiwanie({ specialization: 'python' });
  await pobierzOferty();
  await pobierzStatusWyszukiwania();
  await pobierzAplikacje();
  await polaczGmail();

  expect(postSpy).toHaveBeenCalledWith('/api/start_search', { specialization: 'python' });
  expect(getSpy).toHaveBeenCalledWith('/api/jobs');
  expect(getSpy).toHaveBeenCalledWith('/api/search_status');
  expect(getSpy).toHaveBeenCalledWith('/api/applications');
  expect(getSpy).toHaveBeenCalledWith('/api/gmail/connect');
});
