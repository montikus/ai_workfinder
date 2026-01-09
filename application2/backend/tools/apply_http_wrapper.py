from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional, Type

import requests
from pydantic import BaseModel, EmailStr, Field, ValidationError

from langchain_core.tools import BaseTool

from backend.app.tools.apply_http_tool import apply_to_job_http_tool

logger = logging.getLogger(__name__)


# -----------------------------
# Pydantic input for wrapper
# -----------------------------
class ApplyHTTPWrapperInput(BaseModel):
    job_url: str = Field(..., min_length=10)
    full_name: str = Field(..., min_length=2)
    email: EmailStr
    resume_path: str = Field(..., min_length=1)

    message: Optional[str] = None
    marketing_consent_accepted: bool = False
    source: str = "apply_form"
    timeout_sec: int = Field(default=30, ge=5, le=120)


def apply_http_wrapper_tool(
    job_url: str,
    full_name: str,
    email: str,
    resume_path: str,
    message: Optional[str] = None,
    marketing_consent_accepted: bool = False,
    source: str = "apply_form",
    timeout_sec: int = 30,
    session: Optional[requests.Session] = None,  
) -> Dict[str, Any]:
    try:
        v = ApplyHTTPWrapperInput(
            job_url=job_url,
            full_name=full_name,
            email=email,
            resume_path=resume_path,
            message=message,
            marketing_consent_accepted=marketing_consent_accepted,
            source=source,
            timeout_sec=timeout_sec,
        )
    except ValidationError as exc:
        logger.warning("ApplyHTTPWrapperInput validation failed: %s", exc)
        return {
            "ok": False,
            "applied": False,
            "job_url": str(job_url),
            "api_url": "",
            "status_code": 0,
            "error": f"validation: {exc}",
        }

    try:
        return apply_to_job_http_tool(
            job_url=v.job_url,
            full_name=v.full_name,
            email=str(v.email),
            resume_path=v.resume_path,
            message=v.message,
            marketing_consent_accepted=v.marketing_consent_accepted,
            source=v.source,
            timeout_sec=v.timeout_sec,
            session=session,
        )
    except Exception as exc:
        logger.exception("apply_to_job_http_tool failed: %s", exc)
        return {
            "ok": False,
            "applied": False,
            "job_url": v.job_url,
            "api_url": "",
            "status_code": 0,
            "error": f"runtime: {exc}",
        }


# -----------------------------
# Optional: LangChain BaseTool class (если захотите регистрировать как Tool)
# -----------------------------
class ApplyHTTPArgs(BaseModel):
    job_url: str = Field(..., min_length=10)
    full_name: str = Field(..., min_length=2)
    email: EmailStr
    resume_path: str = Field(..., min_length=1)
    message: Optional[str] = None
    marketing_consent_accepted: bool = False
    source: str = "apply_form"
    timeout_sec: int = Field(default=30, ge=5, le=120)


class JustJoinApplyHttpTool(BaseTool):
    name: str = "justjoin_apply_http"
    description: str = "Apply to a justjoin.it offer via JustJoin API (HTTP multipart/form-data). Returns JSON."
    args_schema: Type[BaseModel] = ApplyHTTPArgs

    def _run(
        self,
        job_url: str,
        full_name: str,
        email: str,
        resume_path: str,
        message: Optional[str] = None,
        marketing_consent_accepted: bool = False,
        source: str = "apply_form",
        timeout_sec: int = 30,
        **kwargs,
    ) -> str:
        res = apply_http_wrapper_tool(
            job_url=job_url,
            full_name=full_name,
            email=email,
            resume_path=resume_path,
            message=message,
            marketing_consent_accepted=marketing_consent_accepted,
            source=source,
            timeout_sec=timeout_sec,
            session=None, 
        )
        return json.dumps(res, ensure_ascii=False)

    async def _arun(self, *args, **kwargs) -> str:
        return self._run(*args, **kwargs)
