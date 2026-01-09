import { klientHttp } from './http.js';

export function rozpocznijWyszukiwanie(dane) {
  return klientHttp.post('/api/start_search', dane);
}

export function pobierzOferty() {
  return klientHttp.get('/api/jobs');
}

export function pobierzStatusWyszukiwania() {
  return klientHttp.get('/api/search_status');
}
