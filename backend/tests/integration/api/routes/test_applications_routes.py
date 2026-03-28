from __future__ import annotations

from app.api.routes.applications import _build_application, _is_applied, _normalize_status, list_applications
from app.services import search_state
from app.services.search_state import mark_finished


def test_application_helpers_handle_status_variants():
    assert _is_applied({"applied": True}) is True
    assert _is_applied({"application_status": "Applied"}) is True
    assert _is_applied({"application_status": "failed"}) is False

    assert _normalize_status({"application_status": "Failed"}) == "Failed"
    assert _normalize_status({"applied": True}) == "Applied"
    assert _normalize_status({}) == "Not applied"


def test_build_application_uses_fallback_fields():
    built = _build_application(
        {
            "job_title": "Backend Developer",
            "company_name": "ACME",
            "url": "https://example.com/job",
            "source": "justjoin",
        },
        "2026-03-28T12:00:00Z",
    )

    assert built["job_title"] == "Backend Developer"
    assert built["company"] == "ACME"
    assert built["sent_at"] == "2026-03-28T12:00:00Z"
    assert built["apply_url"] == "https://example.com/job"


def test_list_applications_returns_only_applied_jobs(user_document, monkeypatch):
    user_id = str(user_document["_id"])
    monkeypatch.setattr(search_state, "_now_iso", lambda: "2026-03-28T09:00:00Z")
    mark_finished(
        user_id,
        {"finished_at": "2026-03-28T09:00:00Z"},
        [
            {
                "id": "1",
                "title": "Python Developer",
                "company": "ACME",
                "source": "justjoin",
                "apply_url": "https://example.com/1",
                "application_status": "Applied",
            },
            {
                "id": "2",
                "title": "Data Engineer",
                "company": "Beta",
                "source": "justjoin",
                "apply_url": "https://example.com/2",
                "application_status": "Failed",
            },
        ],
    )

    response = list_applications(user_document)

    assert response == [
        {
            "job_title": "Python Developer",
            "company": "ACME",
            "sent_at": "2026-03-28T09:00:00Z",
            "status": "Applied",
            "email_to": None,
            "apply_url": "https://example.com/1",
            "source": "justjoin",
        }
    ]
