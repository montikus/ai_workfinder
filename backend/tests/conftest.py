from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.api.deps import pobierz_repo_uzytkownikow
from app.core.security import haszuj_haslo, utworz_token_dostepu
from app.main import app
from app.repositories.uzytkownik_repo import RepozytoriumUzytkownikow
from app.services import search_state


class FakeCollection:
    def __init__(self, documents: list[dict] | None = None):
        self.documents = list(documents or [])
        self.index_calls: list[tuple[tuple, dict]] = []

    def find_one(self, query: dict) -> dict | None:
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                return document
        return None

    def insert_one(self, document: dict):
        stored = dict(document)
        stored["_id"] = stored.get("_id", ObjectId())
        self.documents.append(stored)
        document["_id"] = stored["_id"]
        return SimpleNamespace(inserted_id=stored["_id"])

    def update_one(self, query: dict, update: dict):
        document = self.find_one(query)
        if not document:
            return SimpleNamespace(matched_count=0, modified_count=0)

        document.update(update.get("$set", {}))
        return SimpleNamespace(matched_count=1, modified_count=1)

    def create_index(self, *args, **kwargs):
        self.index_calls.append((args, kwargs))
        return "email_1"


@pytest.fixture(autouse=True)
def clear_search_state():
    search_state._states.clear()
    yield
    search_state._states.clear()


@pytest.fixture
def fake_collection():
    return FakeCollection()


@pytest.fixture
def repo(fake_collection):
    return RepozytoriumUzytkownikow(fake_collection)


@pytest.fixture
def create_user(repo):
    def _create_user(
        email: str = "user@example.com",
        password: str = "Secret123!",
        **updates,
    ) -> dict:
        document = repo.utworz_pusty_profil(email, haszuj_haslo(password))
        if updates:
            repo.zaktualizuj(document, updates)
        return document

    return _create_user


@pytest.fixture
def user_document(create_user):
    return create_user()


@pytest.fixture
def auth_headers_for():
    def _auth_headers_for(user_document: dict) -> dict[str, str]:
        token = utworz_token_dostepu(
            {
                "sub": str(user_document["_id"]),
                "email": user_document["email"],
            }
        )
        return {"Authorization": f"Bearer {token}"}

    return _auth_headers_for


@pytest.fixture
def client(repo):
    app.dependency_overrides[pobierz_repo_uzytkownikow] = lambda: repo
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
