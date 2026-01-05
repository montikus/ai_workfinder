from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.db.mongo import kolekcja_uzytkownicy
from app.repositories.uzytkownik_repo import RepozytoriumUzytkownikow
from app.core.security import zweryfikuj_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


def pobierz_repo_uzytkownikow() -> RepozytoriumUzytkownikow:
    return RepozytoriumUzytkownikow(kolekcja_uzytkownicy)


async def pobierz_aktualnego_uzytkownika(
    token: str = Depends(oauth2_scheme),
    repo: RepozytoriumUzytkownikow = Depends(pobierz_repo_uzytkownikow),
) -> dict:
    payload = zweryfikuj_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy token",
        )

    uzytkownik_id = payload.get("sub")
    if not uzytkownik_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy token (brak sub)",
        )

    dokument = repo.znajdz_po_id(uzytkownik_id)
    if not dokument:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Użytkownik nie istnieje",
        )

    return dokument
