from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.deps import pobierz_aktualnego_uzytkownika, pobierz_repo_uzytkownikow
from app.repositories.uzytkownik_repo import RepozytoriumUzytkownikow
from app.schemas.uzytkownik import SchematUzytkownik, SchematProfilAktualizacja
from app.api.routes.auth import zamien_uzytkownika_na_schemat
from app.services.paths import resume_path

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


@router.post("/api/upload_resume")
async def upload_resume(
    resume: UploadFile = File(...),
    aktualny_uzytkownik: dict = Depends(pobierz_aktualnego_uzytkownika),
    repo: RepozytoriumUzytkownikow = Depends(pobierz_repo_uzytkownikow),
):
    if not resume.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing resume filename.",
        )

    filename = Path(resume.filename).name
    if not filename.lower().endswith((".pdf", ".doc", ".docx")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Upload PDF, DOC, or DOCX.",
        )

    user_id = str(aktualny_uzytkownik["_id"])
    dest_path = resume_path(user_id, filename)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    content = await resume.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    dest_path.write_bytes(content)

    zaktualizowany = repo.zaktualizuj(aktualny_uzytkownik, {"resume_filename": filename})
    return {
        "resume_filename": zaktualizowany.get("resume_filename"),
    }
