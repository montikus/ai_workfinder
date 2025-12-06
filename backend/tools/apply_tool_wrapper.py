from __future__ import annotations

import json
from typing import Optional, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel

# Import your existing Pydantic schema + tool implementation:
# - ApplyInput: pydantic args schema
# - apply_to_job_tool: returns Dict[str, Any] (ApplyResult.model_dump())
from your_module.justjoin_apply_impl import ApplyInput, apply_to_job_tool


class JustJoinApplyTool(BaseTool):
    """
    A LangChain-compatible Tool that submits a job application on justjoin.it
    via the in-platform "Apply" modal (Playwright automation).

    Why this wrapper exists
    -----------------------
    LangChain agents typically interact with tools through a standardized interface:
      - name:        the tool identifier exposed to the LLM
      - description: what the tool does (very important for correct tool selection)
      - args_schema: a Pydantic model describing the tool inputs (typed + validated)

    Inputs (validated by args_schema)
    ---------------------------------
    This tool uses your `ApplyInput` schema. The LLM will be asked to fill:
      - job_url       : URL of a justjoin.it job offer
      - full_name     : "First Last"
      - email         : candidate email
      - resume_path   : local path to PDF/DOCX (must exist on disk)
      - attach_message: optional message for the employer if the UI supports it
      - headless      : run browser without UI (True = faster, but captcha harder)
      - timeout_sec   : timeout per major step
      - captcha_wait_sec: how long to wait for manual captcha solve (headed mode)
      - slow_mo_ms    : slow down actions for debugging

    Output
    ------
    Returns a JSON string (ApplyResult.model_dump()) so it is:
      - safe to store in message history
      - easy for an agent to parse or summarize
      - fully serializable

    Notes / Constraints
    -------------------
    - Captchas cannot be solved automatically in a reliable/ethical way.
      If captcha appears, run with headless=False and solve it manually.
    - This tool assumes the site UI is compatible with the locators you coded.
      If justjoin.it changes UI labels, you may need minor selector updates.
    """

    name: str = "justjoin_apply"
    description: str = (
        "Submit a job application on justjoin.it using Playwright. "
        "Fills candidate name + email, uploads a resume file, checks required consent, "
        "and clicks the final Apply button. Returns a JSON result with status and debug info."
    )

    args_schema: Type[BaseModel] = ApplyInput

    def _run(
        self,
        job_url: str,
        full_name: str,
        email: str,
        resume_path: str,
        attach_message: Optional[str] = None,
        headless: bool = True,
        timeout_sec: int = 45,
        captcha_wait_sec: int = 180,
        slow_mo_ms: int = 0,
        **kwargs,
    ) -> str:
        """
        Synchronous execution (recommended because your Playwright code uses sync API).

        If you later want fully-async support, run this sync tool inside a threadpool
        from your async orchestration layer.
        """
        result = apply_to_job_tool(
            job_url=job_url,
            full_name=full_name,
            email=email,
            resume_path=resume_path,
            attach_message=attach_message,
            headless=headless,
            timeout_sec=timeout_sec,
            captcha_wait_sec=captcha_wait_sec,
            slow_mo_ms=slow_mo_ms,
        )
        return json.dumps(result, ensure_ascii=False)

    async def _arun(self, *args, **kwargs) -> str:
        """
        Async entrypoint required by BaseTool.
        We keep it simple: delegate to sync implementation.
        """
        return self._run(*args, **kwargs)
