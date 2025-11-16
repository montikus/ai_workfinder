from fastapi import APIRouter, Depends

from app.api.deps import pobierz_aktualnego_uzytkownika, pobierz_repo_uzytkownikow
from app.repositories.uzytkownik_repo import RepozytoriumUzytkownikow
from app.schemas.uzytkownik import SchematUzytkownik, SchematProfilAktualizacja
from app.api.routes.auth import zamien_uzytkownika_na_schemat

router = APIRouter()


@router.get("/api/profile", response_model=SchematUzytkownik)
async def pobierz_profil(
    aktualny_uzytkownik: dict = Depends(pobierz_aktualnego_uzytkownika),
):
    return zamien_uzytkownika_na_schemat(aktualny_uzytkownik)


@router.put("/api/profile", response_model=SchematUzytkownik)
async def aktualizuj_profil(
    dane: SchematProfilAktualizacja,
    aktualny_uzytkownik: dict = Depends(pobierz_aktualnego_uzytkownika),
    repo: RepozytoriumUzytkownikow = Depends(pobierz_repo_uzytkownikow),
):
    aktualizacje: dict = {}
    if dane.name is not None:
        aktualizacje["name"] = dane.name
    if dane.phone is not None:
        aktualizacje["phone"] = dane.phone
    if dane.location is not None:
        aktualizacje["location"] = dane.location
    if dane.job_preferences_text is not None:
        aktualizacje["job_preferences_text"] = dane.job_preferences_text

    zaktualizowany = repo.zaktualizuj(aktualny_uzytkownik, aktualizacje)
    return zamien_uzytkownika_na_schemat(zaktualizowany)
