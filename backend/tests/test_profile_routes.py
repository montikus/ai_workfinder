from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.api.routes import profile
from app.schemas.uzytkownik import SchematProfilAktualizacja


class FakeUploadFile:
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self._content = content

    async def read(self) -> bytes:
        return self._content


def test_get_profile_returns_current_user(create_user):
    user = create_user(
        name="Roman",
        phone="+48123456789",
        location="Warsaw",
        job_preferences_text="Python backend",
        resume_filename="cv.pdf",
    )

    response = asyncio.run(profile.pobierz_profil(user))

    assert response.email == "user@example.com"
    assert response.name == "Roman"


def test_put_profile_updates_only_sent_fields(create_user, repo):
    user = create_user(name="Before", phone="111", location="Krakow")

    response = asyncio.run(
        profile.aktualizuj_profil(
            SchematProfilAktualizacja(name="After", job_preferences_text="Remote only"),
            user,
            repo,
        )
    )

    assert response.name == "After"
    assert response.phone == "111"
    assert response.job_preferences_text == "Remote only"


def test_upload_resume_saves_file_and_updates_profile(
    create_user,
    repo,
    monkeypatch,
    tmp_path,
):
    user = create_user()

    monkeypatch.setattr(
        profile,
        "resume_path",
        lambda user_id, filename: tmp_path / user_id / filename,
    )

    response = asyncio.run(
        profile.upload_resume(
            FakeUploadFile("resume.pdf", b"%PDF-1.4 fake"),
            user,
            repo,
        )
    )

    saved_path = tmp_path / str(user["_id"]) / "resume.pdf"

    assert response == {"resume_filename": "resume.pdf"}
    assert saved_path.read_bytes() == b"%PDF-1.4 fake"
    assert user["resume_filename"] == "resume.pdf"


def test_upload_resume_rejects_missing_filename(user_document, repo):
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            profile.upload_resume(
                FakeUploadFile("", b"content"),
                user_document,
                repo,
            )
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Missing resume filename."


def test_upload_resume_rejects_unsupported_file_type(user_document, repo):
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            profile.upload_resume(
                FakeUploadFile("resume.txt", b"content"),
                user_document,
                repo,
            )
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Unsupported file type. Upload PDF, DOC, or DOCX."


def test_upload_resume_rejects_empty_file(
    create_user,
    repo,
    monkeypatch,
    tmp_path,
):
    user = create_user()
    monkeypatch.setattr(
        profile,
        "resume_path",
        lambda user_id, filename: Path(tmp_path / user_id / filename),
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            profile.upload_resume(
                FakeUploadFile("resume.pdf", b""),
                user,
                repo,
            )
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Uploaded file is empty."
