from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import EmailStr

from app.api.deps import pobierz_repo_uzytkownikow
from app.core.security import haszuj_haslo, sprawdz_haslo, utworz_token_dostepu
from app.repositories.uzytkownik_repo import RepozytoriumUzytkownikow
from app.schemas.uzytkownik import (
    SchematRejestracji,
    SchematLogowania,
    SchematUzytkownik,
)

router = APIRouter()


def zamien_uzytkownika_na_schemat(dokument: dict) -> SchematUzytkownik:
    return SchematUzytkownik(
        id=str(dokument["_id"]),
        email=dokument["email"],
        name=dokument.get("name"),
        phone=dokument.get("phone"),
        location=dokument.get("location"),
        job_preferences_text=dokument.get("job_preferences_text"),
        gmail_connected=dokument.get("gmail_connected", False),
        resume_filename=dokument.get("resume_filename"),
    )


@router.post("/api/register")
def rejestracja_uzytkownika(
    dane: SchematRejestracji,
    repo: RepozytoriumUzytkownikow = Depends(pobierz_repo_uzytkownikow),
):
    email_normalizowany: EmailStr = dane.email.lower()

    istnieje = repo.znajdz_po_emailu(email_normalizowany)
    if istnieje:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Użytkownik z takim emailem już istnieje",
        )

    haslo_zahaszowane = haszuj_haslo(dane.password)
    repo.utworz_pusty_profil(email_normalizowany, haslo_zahaszowane)

    return {"message": "Rejestracja udana"}


@router.post("/api/login")
def logowanie_uzytkownika(
    dane: SchematLogowania,
    repo: RepozytoriumUzytkownikow = Depends(pobierz_repo_uzytkownikow),
):
    email_normalizowany: EmailStr = dane.email.lower()

    uzytkownik = repo.znajdz_po_emailu(email_normalizowany)
    if not uzytkownik or not sprawdz_haslo(dane.password, uzytkownik["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nieprawidłowy email lub hasło",
        )

    dane_tokena = {"sub": str(uzytkownik["_id"]), "email": uzytkownik["email"]}
    token = utworz_token_dostepu(dane_tokena, expires_delta=timedelta(minutes=60))

    schemat = zamien_uzytkownika_na_schemat(uzytkownik)

    return {
      "token": token,
      "user": schemat,
    }
