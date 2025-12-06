from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, EmailStr, Field


class RunInput(BaseModel):
    # pipeline params
    specialization: str = Field(..., min_length=1)
    experience_level: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)
    limit: int = Field(default=20, ge=1, le=100)

    # candidate params
    full_name: str = Field(..., min_length=2)
    email: EmailStr = Field(...)
    resume_path: str = Field(..., min_length=1)

    # apply params
    headless: bool = Field(default=True)
    timeout_sec: int = Field(default=45, ge=10, le=300)
    captcha_wait_sec: int = Field(default=180, ge=0, le=900)
    slow_mo_ms: int = Field(default=0, ge=0, le=2000)
    max_apply: int = Field(default=10, ge=1, le=100)

    # optional request
    user_request: str = Field(
        default="Find jobs on justjoin.it, keep only 1-click apply, and apply automatically."
    )


class WorkflowState(TypedDict, total=False):
    # input
    specialization: str
    experience_level: Optional[str]
    location: Optional[str]
    limit: int

    full_name: str
    email: str
    resume_path: str

    headless: bool
    timeout_sec: int
    captcha_wait_sec: int
    slow_mo_ms: int
    max_apply: int
    user_request: str

    # orchestration
    phase: str  # init/search/after_search/filter/after_filter/apply/after_apply/done/error
    status: str
    error: Optional[str]

    # data
    jobs: List[Dict[str, Any]]
    one_click_jobs: List[Dict[str, Any]]
    apply_results: List[Dict[str, Any]]

    # debug/trace
    llm_trace: List[Dict[str, Any]]


class RunSummary(BaseModel):
    ok: bool
    status: str
    error: Optional[str] = None

    total_found: int = 0
    total_one_click: int = 0

    attempted_apply: int = 0
    applied_ok: int = 0

    apply_results: List[Dict[str, Any]] = Field(default_factory=list)
    one_click_jobs: List[Dict[str, Any]] = Field(default_factory=list)
    llm_trace: List[Dict[str, Any]] = Field(default_factory=list)


def state_from_input(inp: RunInput) -> WorkflowState:
    return WorkflowState(
        specialization=inp.specialization,
        experience_level=inp.experience_level,
        location=inp.location,
        limit=inp.limit,
        full_name=inp.full_name,
        email=str(inp.email),
        resume_path=inp.resume_path,
        headless=inp.headless,
        timeout_sec=inp.timeout_sec,
        captcha_wait_sec=inp.captcha_wait_sec,
        slow_mo_ms=inp.slow_mo_ms,
        max_apply=inp.max_apply,
        user_request=inp.user_request,
        phase="init",
        status="running",
        error=None,
        jobs=[],
        one_click_jobs=[],
        apply_results=[],
        llm_trace=[],
    )


def summary_from_state(state: WorkflowState) -> RunSummary:
    jobs = state.get("jobs", []) or []
    one_click = state.get("one_click_jobs", []) or []
    results = state.get("apply_results", []) or []
    trace = state.get("llm_trace", []) or []

    applied_ok = 0
    for r in results:
        if isinstance(r, dict) and r.get("ok") and r.get("applied"):
            applied_ok += 1

    return RunSummary(
        ok=(state.get("phase") == "done" and state.get("status") in ("done", "partial_done")),
        status=state.get("status", "unknown"),
        error=state.get("error"),
        total_found=len(jobs),
        total_one_click=len(one_click),
        attempted_apply=len(results),
        applied_ok=applied_ok,
        apply_results=results,
        one_click_jobs=one_click,
        llm_trace=trace,
    )
