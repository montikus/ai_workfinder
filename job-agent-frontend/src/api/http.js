import axios from 'axios';

const bazaURL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

export const klientHttp = axios.create({
  baseURL: bazaURL,
});

// добавляем токен к каждому запросу
klientHttp.interceptors.request.use((konfiguracja) => {
  const token = localStorage.getItem('token');
  if (token) {
    konfiguracja.headers.Authorization = `Bearer ${token}`;
  }
  return konfiguracja;
});
