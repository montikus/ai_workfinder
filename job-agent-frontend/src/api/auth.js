import { klientHttp } from './http.js';

export function rejestracja(dane) {
  return klientHttp.post('/api/register', dane);
}

export function logowanie(dane) {
  return klientHttp.post('/api/login', dane);
}

export function pobierzProfil() {
  return klientHttp.get('/api/profile');
}

export function aktualizujProfil(dane) {
  return klientHttp.put('/api/profile', dane);
}
