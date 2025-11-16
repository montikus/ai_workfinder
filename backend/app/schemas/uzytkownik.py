from pydantic import BaseModel, EmailStr


class SchematRejestracji(BaseModel):
    email: EmailStr
    password: str


class SchematLogowania(BaseModel):
    email: EmailStr
    password: str


class SchematUzytkownik(BaseModel):
    id: str
    email: EmailStr
    name: str | None = None
    phone: str | None = None
    location: str | None = None
    job_preferences_text: str | None = None
    gmail_connected: bool = False
    resume_filename: str | None = None


class SchematProfilAktualizacja(BaseModel):
    name: str | None = None
    phone: str | None = None
    location: str | None = None
    job_preferences_text: str | None = None
