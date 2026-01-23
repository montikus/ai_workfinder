from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends

from app.api.deps import pobierz_aktualnego_uzytkownika
from app.services.search_state import get_jobs, get_status_payload

router = APIRouter()


def _is_applied(job: Dict[str, Any]) -> bool:
    if job.get("applied") is True:
        return True
    status = job.get("application_status")
    return isinstance(status, str) and status.lower() == "applied"


def _normalize_status(job: Dict[str, Any]) -> str:
    status = job.get("application_status")
    if isinstance(status, str) and status.strip():
        return status
    if job.get("applied") is True:
        return "Applied"
    return "Not applied"


def _build_application(job: Dict[str, Any], sent_at: Optional[str]) -> Dict[str, Any]:
    title = job.get("title") or job.get("job_title") or job.get("position")
    company = job.get("company") or job.get("company_name") or job.get("employer")
    return {
        "job_title": title,
        "company": company,
        "sent_at": job.get("applied_at") or sent_at,
        "status": _normalize_status(job),
        "email_to": job.get("email_to"),
        "apply_url": job.get("apply_url") or job.get("url"),
        "source": job.get("source"),
    }


@router.get("/api/applications")
def list_applications(
    aktualny_uzytkownik: dict = Depends(pobierz_aktualnego_uzytkownika),
) -> List[Dict[str, Any]]:
    user_id = str(aktualny_uzytkownik["_id"])
    jobs = get_jobs(user_id)
    status_payload = get_status_payload(user_id)
    sent_at = status_payload.get("finished_at")

    applications: List[Dict[str, Any]] = []
    for job in jobs:
        if not _is_applied(job):
            continue
        applications.append(_build_application(job, sent_at))

    return applications
