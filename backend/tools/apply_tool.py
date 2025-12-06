from __future__ import annotations

import time
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field, ValidationError

logger = logging.getLogger(__name__)


# -----------------------------
# Pydantic schemas
# -----------------------------


class ApplyInput(BaseModel):
    """
    Input schema for the JustJoin "Apply" automation tool (Playwright).

    Fields
    ------
    job_url:
        Absolute URL to a justjoin.it offer page, e.g. "https://justjoin.it/job-offer/...".
    full_name:
        Candidate first + last name (as expected by the form).
    email:
        Candidate email used for application.
    resume_path:
        Path to a local file (PDF/DOCX) that will be uploaded via the "Add document" control.
    attach_message:
        Optional message to the employer (only if the form exposes this option).
    headless:
        Run browser in headless mode. Use False for local debugging.
    timeout_sec:
        Max time for each major step.
    slow_mo_ms:
        Slow down Playwright actions (useful for debugging).
    """

    job_url: str = Field(..., min_length=10, description="JustJoin offer URL.")
    full_name: str = Field(..., min_length=2, description="First and last name.")
    email: EmailStr = Field(..., description="Applicant email.")
    resume_path: str = Field(..., min_length=1, description="Path to resume file.")
    attach_message: Optional[str] = Field(
        default=None,
        description="Optional message to employer (if supported by the form).",
    )
    headless: bool = Field(default=True, description="Run browser headless.")
    timeout_sec: int = Field(default=45, ge=10, le=300, description="Timeout per step.")
    captcha_wait_sec: int = Field(
        default=180,
        ge=0,
        le=900,
        description=(
            "If captcha appears in headed mode, wait up to N seconds for manual solve. "
            "0 disables waiting."
        ),
    )
    slow_mo_ms: int = Field(default=0, ge=0, le=2000, description="Slow motion ms.")


class ApplyResult(BaseModel):
    """JSON-serializable result returned by apply_to_job_tool."""

    ok: bool
    job_url: str
    applied: bool
    step: str
    error: Optional[str] = None
    debug: Optional[Dict[str, Any]] = None


# -----------------------------
# Internal helpers
# -----------------------------


def _file_error(path_str: str) -> Optional[str]:
    p = Path(path_str).expanduser()
    if not p.exists():
        return f"Resume file not found: {p}"
    if not p.is_file():
        return f"Resume path is not a file: {p}"
    return None


def _safe_filename(path_str: str) -> str:
    try:
        return Path(path_str).name
    except Exception:
        return "resume"


def _try_click(locator, *, timeout_ms: int = 2500) -> bool:
    try:
        locator.wait_for(state="visible", timeout=timeout_ms)
        locator.click(timeout=timeout_ms)
        return True
    except Exception:
        return False


def _dismiss_common_popups(page) -> None:
    # try a few times because banner can appear with delay
    for _ in range(25):  # ~7-8 seconds total
        for pat in [r"accept all", r"accept", r"agree", r"allow all", r"akceptuj", r"zgadzam", r"zaakceptuj"]:
            btn = page.get_by_role("button", name=re.compile(pat, re.I))
            if _try_click(btn, timeout_ms=400):
                return

        # common uppercase button text fallback
        btn2 = page.locator("button:has-text('ACCEPT ALL')")
        if _try_click(btn2, timeout_ms=400):
            return

        page.wait_for_timeout(300)


def _is_captcha_present(page) -> bool:
    """
    Best-effort captcha detection.
    We check VISIBILITY (not just existence) because recaptcha iframes
    often remain in DOM even after a successful solve.
    """
    # 1) Visible captcha text on the page
    try:
        txt = page.locator(
            ":text-matches('i am not a robot|captcha|verify you are human|are you human|"
            "nie jestem robotem|potwierdź, że nie jesteś robotem|weryfikacja', 'i')"
        )
        if txt.count() > 0 and txt.first.is_visible():
            return True
    except Exception:
        pass

    # 2) Visible reCAPTCHA frame
    try:
        fr = page.locator(
            "iframe[src*='recaptcha'][src*='bframe'], "         # реальный challenge iframe
            "iframe[src*='recaptcha'][src*='fallback'], "
            "iframe[src*='hcaptcha'][src*='checkbox'], "
            "iframe[src*='hcaptcha'][src*='challenge']"
        )
        if fr.count() > 0 and fr.first.is_visible():
            return True
    except Exception:
        pass

    # 3) Common captcha containers
    try:
        cont = page.locator(
            ".g-recaptcha, div[id*='captcha'], div[class*='captcha'], [data-sitekey]"
        )
        if cont.count() > 0 and cont.first.is_visible():
            return True
    except Exception:
        pass

    return False

def _wait_for_captcha_clear(page, timeout_sec: int) -> bool:
    try:
        page.locator("iframe[src*='recaptcha'][src*='bframe']").wait_for(
            state="hidden", timeout=timeout_sec * 1000
        )
        return True
    except Exception:
        return not _is_captcha_present(page)





def _open_apply_modal(page, timeout_ms: int) -> None:
    """Click the visible Apply button and wait for the application modal."""
    try:
        page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
    except Exception:
        pass

    _dismiss_common_popups(page)

    # IMPORTANT: only visible candidates (avoid hidden duplicates)
    apply_visible = page.locator(
        ":is(button,a,[role='button']):has-text('Apply'):visible, "
        ":is(button,a,[role='button']):has-text('Aplikuj'):visible"
    )

    # Wait until we have at least one visible Apply button
    apply_visible.first.wait_for(state="visible", timeout=timeout_ms)

    # Click the most “likely CTA” (often last one in view)
    btn = apply_visible.last
    btn.scroll_into_view_if_needed(timeout=timeout_ms)

    try:
        btn.click(timeout=timeout_ms)
    except Exception:
        btn.click(timeout=timeout_ms, force=True)

    # Modal header
    page.get_by_text(re.compile(r"You apply for", re.I)).wait_for(state="visible", timeout=timeout_ms)





def _get_modal_root(page):
    """Return a locator that represents the opened application modal."""
    dialog = page.locator("[role=dialog],[aria-modal=true]").filter(
        has_text=re.compile(r"You apply for", re.I)
    )
    if dialog.count() > 0:
        return dialog.first

    # Fallback: container that includes the header + at least one input
    root = page.locator("div:has-text('You apply for')").filter(
        has=page.locator("input")
    )
    if root.count() > 0:
        return root.first

    # Worst-case: use the whole page (still works, just less strict)
    return page.locator("body")


def _fill_text_field(modal, *, label: str, value: str, placeholder_hint: Optional[str] = None) -> None:
    try:
        modal.get_by_label(label, exact=False).fill(value)
        return
    except Exception:
        pass

    if placeholder_hint:
        loc = modal.locator(f"input[placeholder*='{placeholder_hint}']")
        if loc.count() > 0:
            loc.first.fill(value)
            return

    label_loc = modal.get_by_text(label, exact=False)
    if label_loc.count() > 0:
        near = label_loc.first.locator("xpath=following::input[1]")
        near.fill(value)
        return

    raise RuntimeError(f"Could not locate field: {label}")


def _upload_resume(page, modal, resume_path: str, timeout_ms: int) -> None:
    """Upload resume - supports hidden <input type=file> or FileChooser flow."""
    p = str(Path(resume_path).expanduser())

    file_inputs = modal.locator("input[type='file']")
    if file_inputs.count() > 0:
        file_inputs.first.set_input_files(p, timeout=timeout_ms)
        return

    add_doc = modal.get_by_text("Add document", exact=False)
    try:
        with page.expect_file_chooser(timeout=timeout_ms) as fc_info:
            add_doc.click(timeout=timeout_ms)
        fc_info.value.set_files(p)
        return
    except Exception:
        pass

    # Last attempt: click upload area then re-scan for input
    upload_area = modal.locator(":has-text('Add document')")
    _try_click(upload_area.first, timeout_ms=timeout_ms)
    file_inputs = modal.locator("input[type='file']")
    if file_inputs.count() > 0:
        file_inputs.first.set_input_files(p, timeout=timeout_ms)
        return

    raise RuntimeError("Could not upload resume (no file input / file chooser found).")


def _check_required_consent(modal, timeout_ms: int) -> None:
    """
    Tick the required consent checkbox (Polish/English fallbacks).
    """
    phrases = [
        re.compile(r"Wyrażam zgodę na przetwarzanie moich danych", re.I),
        re.compile(r"I\s*agree.*processing.*data", re.I),
        re.compile(r"consent.*processing.*data", re.I),
    ]

    # Label-based first (most reliable for checkboxes)
    for ph in phrases:
        try:
            modal.get_by_label(ph).check(timeout=timeout_ms)
            return
        except Exception:
            pass

    # Text-click fallback
    for ph in phrases:
        txt = modal.get_by_text(ph)
        if txt.count() > 0:
            txt.first.click(timeout=timeout_ms)
            return

    # "Nearby input" fallback
    for ph in phrases:
        txt = modal.get_by_text(ph)
        if txt.count() > 0:
            container = txt.first.locator("xpath=ancestor::*[self::label or self::div][1]")
            cb = container.locator("input[type='checkbox']")
            if cb.count() > 0:
                cb.first.check(timeout=timeout_ms)
                return

    raise RuntimeError("Could not find the required consent checkbox.")


def _is_enabled(locator) -> bool:
    """Best-effort enabled check for buttons."""
    try:
        if locator.is_disabled():
            return False
    except Exception:
        pass
    try:
        aria = locator.get_attribute("aria-disabled")
        if aria and aria.lower() == "true":
            return False
    except Exception:
        pass
    try:
        disabled = locator.get_attribute("disabled")
        if disabled is not None:
            return False
    except Exception:
        pass
    return True


def _submit_application(modal, timeout_ms: int) -> None:
    deadline = time.time() + (timeout_ms / 1000.0)

    # 1) самый надёжный вариант - submit-кнопка внутри формы
    def pick_button():
        btn = modal.locator("button[type='submit']:visible").filter(
            has_text=re.compile(r"Apply|Aplikuj", re.I)
        )
        if btn.count() > 0:
            return btn.last

        # 2) fallback
        btn = modal.locator(
            "button:visible:has-text('Apply'), "
            "button:visible:has-text('Aplikuj'), "
            ":is(button,[role='button']):visible:has-text('Apply'), "
            ":is(button,[role='button']):visible:has-text('Aplikuj')"
        )
        if btn.count() == 0:
            raise RuntimeError("Final Apply button not found in modal (visible).")
        return btn.last

    last_err = None
    while time.time() < deadline:
        try:
            btn = pick_button()
            btn.scroll_into_view_if_needed(timeout=timeout_ms)

            if not _is_enabled(btn):
                modal.page.wait_for_timeout(250)
                continue

            # Важно: сначала пробный клик - если перекрыто оверлеем, получишь исключение
            btn.click(timeout=1500, trial=True)
            btn.click(timeout=timeout_ms)
            return
        except Exception as e:
            last_err = e
            try:
                modal.page.wait_for_timeout(250)
            except Exception:
                time.sleep(0.25)

    raise RuntimeError(f"Could not click final Apply (still disabled/covered). Last error: {last_err}")





def _wait_for_confirmation(page, modal, timeout_ms: int) -> bool:
    # 1) Modal disappears
    try:
        modal.wait_for(state="hidden", timeout=timeout_ms)
        return True
    except Exception:
        pass

    # 2) Success-ish text appears
    success = page.get_by_text(
        re.compile(r"thank you|application sent|sent|success|wysłano|dziękuj", re.I)
    )
    try:
        success.wait_for(state="visible", timeout=timeout_ms // 2)
        return True
    except Exception:
        return False


def _collect_visible_errors(modal) -> Optional[str]:
    candidates = modal.locator(
        ":text-matches('error|required|invalid|błąd|wymagane|nieprawidł', 'i')"
    )
    try:
        texts = []
        for i in range(min(candidates.count(), 10)):
            t = candidates.nth(i).inner_text().strip()
            if t and t not in texts:
                texts.append(t)
        if texts:
            return " | ".join(texts)[:1000]
    except Exception:
        pass
    return None


# -----------------------------
# Public tool
# -----------------------------


def apply_to_job_tool(
    job_url: str,
    full_name: str,
    email: str,
    resume_path: str,
    attach_message: Optional[str] = None,
    headless: bool = True,
    timeout_sec: int = 45,
    captcha_wait_sec: int = 180,
    slow_mo_ms: int = 0,
) -> Dict[str, Any]:
    """
    Tool: open a justjoin.it job offer and apply via the in-platform "Apply" modal.

    Steps:
    1) Open the offer page (job_url)
    2) Click "Apply"
    3) Fill required fields (name, email)
    4) Upload resume (resume_path)
    5) Tick required consent checkbox
    6) Click final "Apply" and wait for success/error

    Returns JSON-serializable dict and never raises exceptions outward.
    """
    try:
        validated = ApplyInput(
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
    except ValidationError as exc:
        logger.warning("ApplyInput validation failed: %s", exc)
        return ApplyResult(
            ok=False,
            job_url=str(job_url),
            applied=False,
            step="validation",
            error=str(exc),
        ).model_dump()

    file_err = _file_error(validated.resume_path)
    if file_err:
        logger.warning(file_err)
        return ApplyResult(
            ok=False,
            job_url=validated.job_url,
            applied=False,
            step="validation",
            error=file_err,
        ).model_dump()

    timeout_ms = int(validated.timeout_sec * 1000)

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        logger.exception("Playwright import failed: %s", exc)
        return ApplyResult(
            ok=False,
            job_url=validated.job_url,
            applied=False,
            step="dependencies",
            error="Playwright is not installed. Run: poetry add playwright && poetry run playwright install chromium",
        ).model_dump()

    debug: Dict[str, Any] = {"resume_filename": _safe_filename(validated.resume_path)}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=validated.headless, slow_mo=validated.slow_mo_ms)
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()
            page.set_default_timeout(timeout_ms)
            page.set_default_navigation_timeout(timeout_ms)


            step = "open_offer"
            page.goto(validated.job_url, wait_until="domcontentloaded", timeout=timeout_ms)
            _dismiss_common_popups(page)

            step = "open_apply_modal"
            try:
                _open_apply_modal(page, timeout_ms=timeout_ms)
            except Exception as e:
                try:
                    page.screenshot(path="apply_open_modal_fail.png", full_page=True)
                    debug["screenshot"] = "apply_open_modal_fail.png"
                except Exception:
                    pass
                raise
            modal = _get_modal_root(page)

            step = "fill_form"
            _fill_text_field(modal, label="First and last name", value=validated.full_name, placeholder_hint="first")
            _fill_text_field(modal, label="Email", value=str(validated.email), placeholder_hint="email")

            # Optional message (best-effort)
            if validated.attach_message:
                try:
                    toggle = modal.get_by_text("Attach a message for the employer", exact=False)
                    _try_click(toggle, timeout_ms=1200)
                    ta = modal.locator("textarea")
                    if ta.count() > 0:
                        ta.first.fill(validated.attach_message)
                except Exception:
                    logger.info("Attach-message flow not available; continuing.")

            step = "upload_resume"
            _upload_resume(page, modal, validated.resume_path, timeout_ms=timeout_ms)

            step = "consent_checkbox"
            _check_required_consent(modal, timeout_ms=timeout_ms)

            step = "submit"
            _submit_application(modal, timeout_ms=timeout_ms)

            if _wait_for_confirmation(page, modal, timeout_ms=8000):
                return success

            if _is_captcha_present(page):
                debug["captcha_detected"] = True
                try:
                    page.screenshot(path="apply_captcha.png", full_page=True)
                    debug["screenshot"] = "apply_captcha.png"
                except Exception:
                    pass

                if (not validated.headless) and validated.captcha_wait_sec > 0:
                    ok = _wait_for_captcha_clear(page, validated.captcha_wait_sec)
                    if not ok:
                        return ApplyResult(
                            ok=False,
                            job_url=validated.job_url,
                            applied=False,
                            step="captcha",
                            error="Captcha detected and not solved in time.",
                            debug=debug,
                        ).model_dump()

                    # Give UI a moment to re-enable button / re-render after captcha
                    page.wait_for_timeout(700)

                    # Re-locate modal (DOM often changes after captcha)
                    try:
                        modal = _get_modal_root(page)
                    except Exception:
                        modal = page

                    # Sometimes submit already went through after captcha
                    try:
                        if _wait_for_confirmation(page, modal, timeout_ms=8000):
                            browser.close()
                            return ApplyResult(
                                ok=True,
                                job_url=validated.job_url,
                                applied=True,
                                step="done",
                                debug=debug,
                            ).model_dump()
                    except Exception:
                        pass

                    # Try clicking final Apply again (often required)
                    try:
                        modal = _get_modal_root(page)  # заново после капчи
                        _submit_application(modal, timeout_ms=timeout_ms)
                    except Exception:
                        try:
                            page.screenshot(path="apply_after_captcha_fail.png", full_page=True)
                            debug["screenshot"] = "apply_after_captcha_fail.png"
                        except Exception:
                            pass


                else:
                    return ApplyResult(
                        ok=False,
                        job_url=validated.job_url,
                        applied=False,
                        step="captcha",
                        error="Captcha detected. Run headed and solve it manually or increase captcha_wait_sec.",
                        debug=debug,
                    ).model_dump()


            step = "confirm"
            try:
                page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
            except Exception:
                pass
            page.wait_for_timeout(800) 
            try:
                modal = _get_modal_root(page)
            except Exception:
                pass
            success = _wait_for_confirmation(page, modal, timeout_ms=20000)


            if success:
                browser.close()
                return ApplyResult(
                    ok=True,
                    job_url=validated.job_url,
                    applied=True,
                    step="done",
                    debug=debug,
                ).model_dump()

            err_text = _collect_visible_errors(modal)
            debug["modal_errors"] = err_text

            screenshot_path = Path("apply_failure.png")
            try:
                page.screenshot(path=str(screenshot_path), full_page=True)
                debug["screenshot"] = str(screenshot_path)
            except Exception:
                pass

            browser.close()
            return ApplyResult(
                ok=False,
                job_url=validated.job_url,
                applied=False,
                step="confirm",
                error=err_text or "No success confirmation detected (modal still open).",
                debug=debug,
            ).model_dump()

    except Exception as exc:
        logger.exception("Unhandled error in apply_to_job_tool: %s", exc)
        return ApplyResult(
            ok=False,
            job_url=validated.job_url,
            applied=False,
            step="runtime",
            error=str(exc),
            debug=debug,
        ).model_dump()


if __name__ == "__main__":
    # Minimal manual test runner (adjust params to your needs)
    import json
    import argparse

    parser = argparse.ArgumentParser(description="Apply to a justjoin.it job offer via Playwright.")
    parser.add_argument("--url", required=True, help="Job offer URL on justjoin.it")
    parser.add_argument("--name", required=True, help="First and last name")
    parser.add_argument("--email", required=True, help="Email")
    parser.add_argument("--resume", required=True, help="Path to resume file")
    parser.add_argument("--message", default=None, help="Optional message to employer")
    parser.add_argument("--headed", action="store_true", help="Run with visible browser window (not headless)")
    parser.add_argument("--slow", type=int, default=0, help="Slow motion ms (debug)")
    parser.add_argument("--timeout", type=int, default=45, help="Timeout per step in seconds")
    parser.add_argument(
        "--captcha-wait",
        dest="captcha_wait_sec",
        type=int,
        default=180,
        help="Seconds to wait for manual captcha solve in headed mode (0 disables).",
    )


    args = parser.parse_args()

    result = apply_to_job_tool(
        job_url=args.url,
        full_name=args.name,
        email=args.email,
        resume_path=args.resume,
        attach_message=args.message,
        headless=not args.headed,
        slow_mo_ms=args.slow,
        timeout_sec=args.timeout,
        captcha_wait_sec=args.captcha_wait_sec,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
