from pymongo import MongoClient
from app.core.config import ustawienia

klient_mongo = MongoClient(ustawienia.mongodb_uri)
baza_danych = klient_mongo[ustawienia.mongodb_nazwa_bazy]

kolekcja_uzytkownicy = baza_danych["users"]

# уникальный индекс по email
kolekcja_uzytkownicy.create_index("email", unique=True)
