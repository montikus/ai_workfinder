from __future__ import annotations

from functools import lru_cache

from pymongo import MongoClient
from pymongo.collection import Collection

from app.core.config import ustawienia


@lru_cache(maxsize=1)
def pobierz_kolekcje_uzytkownicy() -> Collection:
    klient_mongo = MongoClient(ustawienia.mongodb_uri)
    baza_danych = klient_mongo[ustawienia.mongodb_nazwa_bazy]
    kolekcja_uzytkownicy = baza_danych["users"]
    kolekcja_uzytkownicy.create_index("email", unique=True)
    return kolekcja_uzytkownicy
