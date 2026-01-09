from __future__ import annotations

import json
import logging
import time
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.deps import pobierz_aktualnego_uzytkownika
from app.services.ai_runner import run_ai_from_config
from app.services.paths import project_root, resume_path
from app.services.search_state import (
    append_event,
    get_events_since,
    get_jobs,
    get_status_payload,
    mark_failed,
    mark_finished,
    mark_running,
)


router = APIRouter()
_current_search_user: ContextVar[str | None] = ContextVar("current_search_user", default=None)

class _SearchLogHandler(logging.Handler):
    def __init__(self, user_id: str) -> None:
        super().__init__()
        self.user_id = user_id

    def emit(self, record: logging.LogRecord) -> None:
        if _current_search_user.get() != self.user_id:
            return
        if not (record.name.startswith("ai") or record.name.startswith("backend.tools")):
            return
        try:
            message = self.format(record)
            append_event(self.user_id, message, record.levelname)
        except Exception:
            return


class SearchStartInput(BaseModel):
    specialization: str = Field(..., min_length=1)
    experience_level: Optional[str] = None
    location: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)
    max_apply: int = Field(default=3, ge=1, le=100)
    full_name: Optional[str] = None
    user_request: Optional[str] = None
    llm_model: Optional[str] = None
    headless: Optional[bool] = None
    timeout_sec: Optional[int] = Field(default=None, ge=5, le=120)
    captcha_wait_sec: Optional[int] = Field(default=None, ge=0, le=900)
    slow_mo_ms: Optional[int] = Field(default=None, ge=0, le=2000)


def _config_path() -> Path:
    return project_root() / "config.json"


def _merge_jobs(jobs: List[Dict[str, Any]], apply_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results_by_url = {
        (item or {}).get("job_url"): (item or {})
        for item in apply_results
        if (item or {}).get("job_url")
    }

    merged: List[Dict[str, Any]] = []
    for job in jobs:
        data = dict(job or {})
        job_url = data.get("url") or data.get("apply_url")
        if job_url and not data.get("apply_url"):
            data["apply_url"] = job_url

        result = results_by_url.get(job_url)
        if result:
            applied = bool(result.get("applied"))
            data["applied"] = applied
            if applied:
                data["application_status"] = "Applied"
            elif result.get("ok") is False:
                data["application_status"] = "Failed"
            else:
                data["application_status"] = "Not applied"
            if result.get("error"):
                data["apply_error"] = result.get("error")

        merged.append(data)

    return merged


def _run_search_task(user_id: str, config_path: Path) -> None:
    root_logger = logging.getLogger()
    handler = _SearchLogHandler(user_id)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))
    root_logger.addHandler(handler)
    append_event(user_id, "AI search started")

    token = _current_search_user.set(user_id)
    try:
        summary, final_state = run_ai_from_config(config_path)
        jobs = final_state.get("one_click_jobs") or final_state.get("jobs") or []
        merged = _merge_jobs(jobs, summary.get("apply_results", []) or [])
        mark_finished(user_id, summary, merged)
        append_event(user_id, "AI search finished")
    except Exception as exc:
        append_event(user_id, f"AI search failed: {exc}", "ERROR")
        mark_failed(user_id, str(exc))
    finally:
        _current_search_user.reset(token)
        root_logger.removeHandler(handler)


@router.post("/api/start_search")
def start_search(
    payload: SearchStartInput,
    background_tasks: BackgroundTasks,
    aktualny_uzytkownik: dict = Depends(pobierz_aktualnego_uzytkownika),
):
    user_id = str(aktualny_uzytkownik["_id"])
    email = aktualny_uzytkownik.get("email")
    full_name = (payload.full_name or aktualny_uzytkownik.get("name") or "").strip()
    resume_filename = aktualny_uzytkownik.get("resume_filename")

    current_status = get_status_payload(user_id)
    if current_status.get("status") == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Search is already running.",
        )

    if not full_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing full name. Update your profile or provide it in the request.",
        )

    if not resume_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume not uploaded. Please upload your resume first.",
        )

    resume_file_path = resume_path(user_id, resume_filename)
    if not resume_file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume file not found on server. Please upload again.",
        )

    config_path = _config_path()
    base_config: Dict[str, Any] = {}
    if config_path.exists():
        try:
            base_config = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            base_config = {}

    specialization = payload.specialization.strip()
    if not specialization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Specialization cannot be empty.",
        )

    config = dict(base_config)
    config.update(
        {
            "specialization": specialization,
            "experience_level": payload.experience_level,
            "location": payload.location,
            "limit": payload.limit,
            "full_name": full_name,
            "email": email,
            "resume_path": str(resume_file_path),
            "max_apply": payload.max_apply,
        }
    )

    if payload.user_request:
        config["user_request"] = payload.user_request
    if payload.llm_model:
        config["llm_model"] = payload.llm_model
    if payload.headless is not None:
        config["headless"] = payload.headless
    if payload.timeout_sec is not None:
        config["timeout_sec"] = payload.timeout_sec
    if payload.captcha_wait_sec is not None:
        config["captcha_wait_sec"] = payload.captcha_wait_sec
    if payload.slow_mo_ms is not None:
        config["slow_mo_ms"] = payload.slow_mo_ms

    config_path.write_text(
        json.dumps(config, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )

    mark_running(user_id)
    append_event(user_id, "Search queued")
    background_tasks.add_task(_run_search_task, user_id, config_path)

    return {"status": "running"}


@router.get("/api/search_status")
def search_status(
    aktualny_uzytkownik: dict = Depends(pobierz_aktualnego_uzytkownika),
):
    user_id = str(aktualny_uzytkownik["_id"])
    return get_status_payload(user_id)


@router.get("/api/jobs")
def list_jobs(
    aktualny_uzytkownik: dict = Depends(pobierz_aktualnego_uzytkownika),
):
    user_id = str(aktualny_uzytkownik["_id"])
    return get_jobs(user_id)


@router.get("/api/search_stream")
def search_stream(
    aktualny_uzytkownik: dict = Depends(pobierz_aktualnego_uzytkownika),
):
    user_id = str(aktualny_uzytkownik["_id"])

    def event_generator():
        last_idx = 0
        while True:
            events, last_idx = get_events_since(user_id, last_idx)
            for event in events:
                payload = json.dumps(event, ensure_ascii=True)
                yield f"event: log\ndata: {payload}\n\n"

            status_payload = get_status_payload(user_id)
            yield f"event: status\ndata: {json.dumps(status_payload, ensure_ascii=True)}\n\n"

            if status_payload.get("status") in ("finished", "failed"):
                yield "event: done\ndata: {}\n\n"
                break

            time.sleep(1)

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)
