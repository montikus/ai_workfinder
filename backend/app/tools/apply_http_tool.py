from __future__ import annotations

import logging
import mimetypes
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests
from pydantic import BaseModel, EmailStr, Field, ValidationError

logger = logging.getLogger(__name__)

# -----------------------------
# Local hardcoded headers (ignored by git)
# -----------------------------
# try:
    # File you created:
    # backend/tools/_justjoin_headers_local.py (must be in .gitignore)
from ._justjoin_headers_local import (  # type: ignore
    JJ_X_IDENTITY,
    JJ_X_SNOWPLOW,
    JJ_X_GA,
    JJ_RECAPTCHA_TOKEN,
)
# except Exception:
#     JJ_X_IDENTITY = None
#     JJ_X_SNOWPLOW = None
#     JJ_X_GA = None
#     JJ_RECAPTCHA_TOKEN = None


# -----------------------------
# Schemas
# -----------------------------
class ApplyHttpInput(BaseModel):
    job_url: str = Field(..., min_length=10)
    full_name: str = Field(..., min_length=2)
    email: EmailStr = Field(...)
    resume_path: str = Field(..., min_length=1)

    message: Optional[str] = None
    marketing_consent_accepted: bool = False
    source: str = "apply_form"

    # Optional headers (copied from browser network)
    recaptcha_token: Optional[str] = None
    x_identity: Optional[str] = None
    x_snowplow: Optional[str] = None
    x_ga: Optional[str] = None

    timeout_sec: int = Field(default=30, ge=5, le=120)


class ApplyHttpResult(BaseModel):
    ok: bool
    applied: bool
    job_url: str
    api_url: str
    status_code: int
    application_id: Optional[str] = None
    error: Optional[str] = None
    response_json: Optional[Dict[str, Any]] = None
    response_text: Optional[str] = None


# -----------------------------
# Helpers
# -----------------------------
def _file_error(path_str: str) -> Optional[str]:
    p = Path(path_str).expanduser()
    if not p.exists():
        return f"Resume file not found: {p}"
    if not p.is_file():
        return f"Resume path is not a file: {p}"
    return None


def _offer_slug_from_job_url(job_url: str) -> str:
    u = urlparse(job_url)
    path = (u.path or "").strip("/")

    # If someone passes api url:
    # /v1/offers/<slug>/applications
    if "api.justjoin.it" in (u.netloc or "") and path.startswith("v1/offers/"):
        parts = path.split("/")
        if len(parts) >= 3:
            return parts[2]

    # Normal site url:
    # /job-offer/<slug>
    parts = path.split("/")
    if "job-offer" in parts:
        i = parts.index("job-offer")
        if i + 1 < len(parts):
            return parts[i + 1]

    if not parts or not parts[-1]:
        raise ValueError("Cannot parse offer slug from job_url")
    return parts[-1]


def _build_api_url(job_url: str) -> str:
    slug = _offer_slug_from_job_url(job_url)
    return f"https://api.justjoin.it/v1/offers/{slug}/applications"


# -----------------------------
# Public tool
# -----------------------------
def apply_to_job_http_tool(
    job_url: str,
    full_name: str,
    email: str,
    resume_path: str,
    message: Optional[str] = None,
    marketing_consent_accepted: bool = False,
    source: str = "apply_form",
    recaptcha_token: Optional[str] = None,
    x_identity: Optional[str] = None,
    x_snowplow: Optional[str] = None,
    x_ga: Optional[str] = None,
    timeout_sec: int = 30,
    session: Optional[requests.Session] = None,
) -> Dict[str, Any]:
    """
    POST multipart/form-data to JustJoin API:
      https://api.justjoin.it/v1/offers/<slug>/applications

    Required (in practice):
      - x-identity header (otherwise 403 IDENTITY_INVALID)

    This tool will automatically use defaults from:
      backend/tools/_justjoin_headers_local.py
    if you didn't pass headers as function arguments.
    """

    # Use local hardcoded defaults (ignored by git) if not explicitly passed
    if not x_identity and JJ_X_IDENTITY:
        x_identity = JJ_X_IDENTITY
    if not x_snowplow and JJ_X_SNOWPLOW:
        x_snowplow = JJ_X_SNOWPLOW
    if not x_ga and JJ_X_GA:
        x_ga = JJ_X_GA
    if recaptcha_token is None and JJ_RECAPTCHA_TOKEN is not None:
        # allow explicit None to mean "don't send it"
        recaptcha_token = JJ_RECAPTCHA_TOKEN

    try:
        v = ApplyHttpInput(
            job_url=job_url,
            full_name=full_name,
            email=email,
            resume_path=resume_path,
            message=message,
            marketing_consent_accepted=marketing_consent_accepted,
            source=source,
            recaptcha_token=recaptcha_token,
            x_identity=x_identity,
            x_snowplow=x_snowplow,
            x_ga=x_ga,
            timeout_sec=timeout_sec,
        )
    except ValidationError as exc:
        return ApplyHttpResult(
            ok=False,
            applied=False,
            job_url=str(job_url),
            api_url="",
            status_code=0,
            error=f"validation: {exc}",
        ).model_dump()

    fe = _file_error(v.resume_path)
    if fe:
        return ApplyHttpResult(
            ok=False,
            applied=False,
            job_url=v.job_url,
            api_url="",
            status_code=0,
            error=f"validation: {fe}",
        ).model_dump()

    api_url = _build_api_url(v.job_url)
    s = session or requests.Session()

    headers: Dict[str, str] = {
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://justjoin.it",
        "Referer": "https://justjoin.it/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JobAgentBot/0.2",
    }

    # Identity headers
    if v.x_identity:
        headers["x-identity"] = v.x_identity
    if v.x_snowplow:
        headers["x-snowplow"] = v.x_snowplow
    if v.x_ga:
        headers["x-ga"] = v.x_ga
    if v.recaptcha_token:
        headers["recaptcha-token"] = v.recaptcha_token

    data = {
        "name": v.full_name,
        "email": str(v.email),
        "message": v.message or "",
        "source": v.source,
        "marketing_consent_accepted": "true" if v.marketing_consent_accepted else "false",
    }

    p = Path(v.resume_path).expanduser()
    mime, _ = mimetypes.guess_type(str(p))
    mime = mime or "application/pdf"

    try:
        with open(p, "rb") as f:
            files = {"attachment": (p.name, f, mime)}
            resp = s.post(
                api_url,
                headers=headers,
                data=data,
                files=files,
                timeout=v.timeout_sec,
            )
            logging.info("%r", resp.text)

        # Read response
        resp_text = None
        try:
            resp_text = resp.text
        except Exception:
            pass

        resp_json = None
        try:
            resp_json = resp.json()
        except Exception:
            resp_json = None

        if resp.status_code in (200, 201):
            app_id = resp_json.get("id") if isinstance(resp_json, dict) else None
            return ApplyHttpResult(
                ok=True,
                applied=True,
                job_url=v.job_url,
                api_url=api_url,
                status_code=resp.status_code,
                application_id=app_id,
                response_json=resp_json,
                response_text=resp_text,
            ).model_dump()

        return ApplyHttpResult(
            ok=False,
            applied=False,
            job_url=v.job_url,
            api_url=api_url,
            status_code=resp.status_code,
            error=f"http_error: {resp.status_code}",
            response_json=resp_json,
            response_text=resp_text,
        ).model_dump()

    except requests.RequestException as exc:
        logger.exception("HTTP apply failed: %s", exc)
        return ApplyHttpResult(
            ok=False,
            applied=False,
            job_url=v.job_url,
            api_url=api_url,
            status_code=0,
            error=f"request_exception: {exc}",
        ).model_dump()