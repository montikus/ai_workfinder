from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.api.routes.auth import logowanie_uzytkownika, rejestracja_uzytkownika
from app.schemas.uzytkownik import SchematLogowania, SchematRejestracji


def test_register_creates_user_profile(repo):
    response = rejestracja_uzytkownika(
        SchematRejestracji(email="User@Example.com", password="Secret123!"),
        repo,
    )

    assert response == {"message": "Rejestracja udana"}

    stored = repo.znajdz_po_emailu("user@example.com")
    assert stored is not None
    assert stored["email"] == "user@example.com"
    assert stored["password_hash"] != "Secret123!"


def test_register_rejects_duplicate_email(create_user, repo):
    create_user(email="user@example.com")

    with pytest.raises(HTTPException) as exc_info:
        rejestracja_uzytkownika(
            SchematRejestracji(email="USER@example.com", password="Secret123!"),
            repo,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Użytkownik z takim emailem już istnieje"


def test_login_returns_token_and_user(create_user, repo):
    create_user(email="user@example.com", password="Secret123!", name="Roman")

    response = logowanie_uzytkownika(
        SchematLogowania(email="USER@example.com", password="Secret123!"),
        repo,
    )

    assert isinstance(response["token"], str)
    assert response["user"].email == "user@example.com"
    assert response["user"].name == "Roman"


def test_login_rejects_invalid_credentials(create_user, repo):
    create_user(email="user@example.com", password="Secret123!")

    with pytest.raises(HTTPException) as exc_info:
        logowanie_uzytkownika(
            SchematLogowania(email="user@example.com", password="wrong"),
            repo,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Nieprawidłowy email lub hasło"
