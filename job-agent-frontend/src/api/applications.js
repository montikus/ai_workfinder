import { klientHttp } from './http.js';

export function pobierzAplikacje() {
  return klientHttp.get('/api/applications');
}
