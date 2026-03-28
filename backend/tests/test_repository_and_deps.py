from __future__ import annotations

import asyncio

import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.api import deps
from app.db import mongo
from app.repositories.uzytkownik_repo import RepozytoriumUzytkownikow


def test_repozytorium_uzytkownikow_crud(fake_collection):
    repo = RepozytoriumUzytkownikow(fake_collection)

    document = repo.utworz_pusty_profil("user@example.com", "hashed-password")

    assert repo.znajdz_po_emailu("user@example.com") == document
    assert repo.znajdz_po_id(str(document["_id"])) == document

    updated = repo.zaktualizuj(document, {"name": "Roman", "location": "Warsaw"})

    assert updated["name"] == "Roman"
    assert updated["location"] == "Warsaw"


def test_repozytorium_uzytkownikow_returns_none_for_invalid_id(repo):
    assert repo.znajdz_po_id("not-an-object-id") is None


def test_repozytorium_uzytkownikow_skips_empty_update(user_document, repo):
    updated = repo.zaktualizuj(user_document, {})

    assert updated is user_document


def test_pobierz_repo_uzytkownikow_uses_lazy_collection_provider(monkeypatch, fake_collection):
    monkeypatch.setattr(deps, "pobierz_kolekcje_uzytkownicy", lambda: fake_collection)

    repo = deps.pobierz_repo_uzytkownikow()

    assert isinstance(repo, RepozytoriumUzytkownikow)
    assert repo.kolekcja is fake_collection


def test_pobierz_aktualnego_uzytkownika_returns_document(user_document, repo, auth_headers_for):
    token = auth_headers_for(user_document)["Authorization"].removeprefix("Bearer ")

    document = asyncio.run(
        deps.pobierz_aktualnego_uzytkownika(token=token, repo=repo)
    )

    assert document == user_document


def test_pobierz_aktualnego_uzytkownika_rejects_invalid_token(repo):
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(deps.pobierz_aktualnego_uzytkownika(token="bad-token", repo=repo))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Nieprawidłowy token"


def test_pobierz_aktualnego_uzytkownika_requires_sub(monkeypatch, repo):
    monkeypatch.setattr(deps, "zweryfikuj_token", lambda token: {"email": "user@example.com"})

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(deps.pobierz_aktualnego_uzytkownika(token="token", repo=repo))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Nieprawidłowy token (brak sub)"


def test_pobierz_aktualnego_uzytkownika_requires_existing_user(monkeypatch, repo):
    monkeypatch.setattr(deps, "zweryfikuj_token", lambda token: {"sub": str(ObjectId())})

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(deps.pobierz_aktualnego_uzytkownika(token="token", repo=repo))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Użytkownik nie istnieje"


def test_pobierz_kolekcje_uzytkownicy_creates_index(monkeypatch):
    class FakeDatabase:
        def __init__(self, collection):
            self.collection = collection

        def __getitem__(self, key):
            assert key == "users"
            return self.collection

    class FakeClient:
        def __init__(self, uri):
            self.uri = uri

        def __getitem__(self, key):
            assert key == "job_agent_db"
            return fake_database

    class Collection:
        def __init__(self):
            self.index_calls = []

        def create_index(self, *args, **kwargs):
            self.index_calls.append((args, kwargs))
            return "email_1"

    collection = Collection()
    fake_database = FakeDatabase(collection)

    monkeypatch.setattr(mongo, "MongoClient", FakeClient)
    monkeypatch.setattr(mongo.ustawienia, "mongodb_uri", "mongodb://fake")
    monkeypatch.setattr(mongo.ustawienia, "mongodb_nazwa_bazy", "job_agent_db")
    mongo.pobierz_kolekcje_uzytkownicy.cache_clear()

    result = mongo.pobierz_kolekcje_uzytkownicy()

    assert result is collection
    assert collection.index_calls == [(("email",), {"unique": True})]

    mongo.pobierz_kolekcje_uzytkownicy.cache_clear()
