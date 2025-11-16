from typing import Optional

from bson import ObjectId
from pymongo.collection import Collection


class RepozytoriumUzytkownikow:
    def __init__(self, kolekcja: Collection):
        self.kolekcja = kolekcja

    def znajdz_po_emailu(self, email: str) -> Optional[dict]:
        return self.kolekcja.find_one({"email": email})

    def znajdz_po_id(self, uzytkownik_id: str) -> Optional[dict]:
        try:
            oid = ObjectId(uzytkownik_id)
        except Exception:
            return None
        return self.kolekcja.find_one({"_id": oid})

    def utworz_pusty_profil(self, email: str, haslo_zahaszowane: str) -> dict:
        dokument = {
            "email": email,
            "password_hash": haslo_zahaszowane,
            "name": None,
            "phone": None,
            "location": None,
            "job_preferences_text": None,
            "gmail_connected": False,
            "resume_filename": None,
        }
        wynik = self.kolekcja.insert_one(dokument)
        dokument["_id"] = wynik.inserted_id
        return dokument

    def zaktualizuj(self, dokument: dict, aktualizacje: dict) -> dict:
        if not aktualizacje:
            return dokument
        self.kolekcja.update_one({"_id": dokument["_id"]}, {"$set": aktualizacje})
        dokument.update(aktualizacje)
        return dokument
