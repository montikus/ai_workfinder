import { klientHttp } from './http.js';

export function polaczGmail() {
  // предполагаем, что бекенд вернёт { url: 'https://accounts.google.com/...' }
  return klientHttp.get('/api/gmail/connect');
}
