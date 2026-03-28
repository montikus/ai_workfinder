from __future__ import annotations

from datetime import timedelta

from app.core.security import (
    haszuj_haslo,
    sprawdz_haslo,
    utworz_token_dostepu,
    zweryfikuj_token,
)


def test_haszuj_haslo_and_sprawdz_haslo_roundtrip():
    hashed = haszuj_haslo("Secret123!")

    assert hashed != "Secret123!"
    assert sprawdz_haslo("Secret123!", hashed) is True
    assert sprawdz_haslo("wrong-password", hashed) is False


def test_utworz_token_dostepu_and_zweryfikuj_token():
    token = utworz_token_dostepu({"sub": "abc123", "email": "user@example.com"})
    payload = zweryfikuj_token(token)

    assert payload is not None
    assert payload["sub"] == "abc123"
    assert payload["email"] == "user@example.com"
    assert "exp" in payload


def test_zweryfikuj_token_returns_none_for_invalid_token():
    assert zweryfikuj_token("definitely-not-a-jwt") is None


def test_zweryfikuj_token_returns_none_for_expired_token():
    token = utworz_token_dostepu(
        {"sub": "expired-user"},
        expires_delta=timedelta(seconds=-1),
    )

    assert zweryfikuj_token(token) is None
