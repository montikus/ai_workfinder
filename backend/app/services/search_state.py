from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, Dict, List


@dataclass
class SearchState:
    status: str = "idle"
    jobs_found: int = 0
    applications_sent: int = 0
    attempted_apply: int = 0
    applied_ok: int = 0
    total_one_click: int = 0
    error: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    jobs: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)


_lock = Lock()
_states: Dict[str, SearchState] = {}


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _get_or_create(user_id: str) -> SearchState:
    state = _states.get(user_id)
    if not state:
        state = SearchState()
        _states[user_id] = state
    return state


def mark_running(user_id: str) -> None:
    with _lock:
        state = _get_or_create(user_id)
        state.status = "running"
        state.jobs_found = 0
        state.applications_sent = 0
        state.attempted_apply = 0
        state.applied_ok = 0
        state.total_one_click = 0
        state.error = None
        state.started_at = _now_iso()
        state.finished_at = None
        state.jobs = []
        state.summary = {}
        state.events = []


def mark_finished(user_id: str, summary: Dict[str, Any], jobs: List[Dict[str, Any]]) -> None:
    with _lock:
        state = _get_or_create(user_id)
        state.status = "finished"
        state.summary = summary
        state.jobs = jobs
        state.jobs_found = int(summary.get("total_found", len(jobs) or 0))
        state.total_one_click = int(summary.get("total_one_click", 0))
        state.attempted_apply = int(summary.get("attempted_apply", 0))
        state.applied_ok = int(summary.get("applied_ok", 0))
        state.applications_sent = state.applied_ok
        state.error = summary.get("error")
        state.finished_at = _now_iso()


def mark_failed(user_id: str, error: str) -> None:
    with _lock:
        state = _get_or_create(user_id)
        state.status = "failed"
        state.error = error
        state.finished_at = _now_iso()


def get_status_payload(user_id: str) -> Dict[str, Any]:
    with _lock:
        state = _get_or_create(user_id)
        return {
            "status": state.status,
            "jobs_found": state.jobs_found,
            "applications_sent": state.applications_sent,
            "attempted_apply": state.attempted_apply,
            "applied_ok": state.applied_ok,
            "total_one_click": state.total_one_click,
            "error": state.error,
            "started_at": state.started_at,
            "finished_at": state.finished_at,
        }


def get_jobs(user_id: str) -> List[Dict[str, Any]]:
    with _lock:
        state = _get_or_create(user_id)
        return list(state.jobs)


def append_event(user_id: str, message: str, level: str = "INFO") -> None:
    with _lock:
        state = _get_or_create(user_id)
        state.events.append(
            {
                "ts": _now_iso(),
                "level": level,
                "message": message,
            }
        )
        if len(state.events) > 500:
            state.events = state.events[-500:]


def get_events_since(user_id: str, offset: int) -> tuple[List[Dict[str, Any]], int]:
    with _lock:
        state = _get_or_create(user_id)
        events = state.events[offset:]
        return list(events), len(state.events)
