const bazaURL = globalThis.__APP_API_URL__ || 'http://localhost:8001';

async function wykonajZadanie(metoda, url, dane, konfiguracja = {}) {
  let finalnaKonfiguracja = {
    headers: {},
    ...konfiguracja,
  };

  for (const handler of klientHttp.interceptors.request.handlers) {
    if (handler?.fulfilled) {
      finalnaKonfiguracja = (await handler.fulfilled(finalnaKonfiguracja)) || finalnaKonfiguracja;
    }
  }

  const headers = new Headers(finalnaKonfiguracja.headers || {});
  let body;

  if (dane instanceof FormData) {
    body = dane;
    headers.delete('Content-Type');
  } else if (dane !== undefined) {
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }
    body = JSON.stringify(dane);
  }

  const response = await fetch(`${bazaURL}${url}`, {
    method: metoda,
    headers,
    body,
  });

  const text = await response.text();
  let parsed = null;

  if (text) {
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = text;
    }
  }

  if (!response.ok) {
    const error = new Error(`HTTP ${response.status}`);
    error.response = {
      status: response.status,
      data: parsed,
    };
    throw error;
  }

  return {
    data: parsed,
    status: response.status,
    headers: response.headers,
  };
}

export const klientHttp = {
  baseURL: bazaURL,
  interceptors: {
    request: {
      handlers: [],
      use(fulfilled) {
        this.handlers.push({ fulfilled });
        return this.handlers.length - 1;
      },
    },
  },
  get(url, konfiguracja) {
    return wykonajZadanie('GET', url, undefined, konfiguracja);
  },
  post(url, dane, konfiguracja) {
    return wykonajZadanie('POST', url, dane, konfiguracja);
  },
  put(url, dane, konfiguracja) {
    return wykonajZadanie('PUT', url, dane, konfiguracja);
  },
};

klientHttp.interceptors.request.use((konfiguracja) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return konfiguracja;
  }

  return {
    ...konfiguracja,
    headers: {
      ...(konfiguracja.headers || {}),
      Authorization: `Bearer ${token}`,
    },
  };
});
