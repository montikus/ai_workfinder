import { klientHttp } from './http.js';

export function rozpocznijWyszukiwanie() {
  return klientHttp.post('/api/start_search');
}

export function pobierzOferty() {
  return klientHttp.get('/api/jobs');
}

export function pobierzStatusWyszukiwania() {
  return klientHttp.get('/api/search_status');
}
