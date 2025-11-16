import React, { createContext, useContext, useEffect, useMemo, useState, useCallback } from 'react';
import { logowanie, rejestracja, pobierzProfil } from '../api/auth.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [uzytkownik, ustawUzytkownika] = useState(null);
  const [token, ustawToken] = useState(null);
  const [ladowanie, ustawLadowanie] = useState(true);

  const zalogowany = !!token;

  useEffect(() => {
    const zapisanyToken = localStorage.getItem('token');
    if (zapisanyToken) {
      ustawToken(zapisanyToken);
      pobierzProfil()
        .then((res) => {
          ustawUzytkownika(res.data);
        })
        .catch(() => {
          localStorage.removeItem('token');
          ustawToken(null);
          ustawUzytkownika(null);
        })
        .finally(() => {
          ustawLadowanie(false);
        });
    } else {
      ustawLadowanie(false);
    }
  }, []);

  const zaloguj = useCallback(async (daneLogowania) => {
    const res = await logowanie(daneLogowania);
    const nowyToken = res.data.token; // предполагаем, что бекенд возвращает { token, user }
    localStorage.setItem('token', nowyToken);
    ustawToken(nowyToken);
    ustawUzytkownika(res.data.user || null);
  }, []);

  const zarejestruj = useCallback(async (dane) => {
    await rejestracja(dane);
  }, []);

  const wyloguj = useCallback(() => {
    localStorage.removeItem('token');
    ustawToken(null);
    ustawUzytkownika(null);
  }, []);

  const wartosc = useMemo(
    () => ({
      uzytkownik,
      token,
      zalogowany,
      ladowanie,
      zaloguj,
      zarejestruj,
      wyloguj,
      ustawUzytkownika,
    }),
    [uzytkownik, token, zalogowany, ladowanie, zaloguj, zarejestruj, wyloguj]
  );

  return <AuthContext.Provider value={wartosc}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}

// ⚠️ Если твой бекенд возвращает другой формат ответа (например, только token), подправь строки с res.data.token и res.data.user.
