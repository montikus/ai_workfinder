
from __future__ import annotations

import time
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field, ValidationError

from backend.tools.captcha_solver import (
    CaptchaSolver,
    extract_sitekey_from_page,
    inject_captcha_solution
)

logger = logging.getLogger(__name__)


# -----------------------------
# Pydantic schemas
# -----------------------------


class ApplyInput(BaseModel):
    """Input schema для JustJoin Apply automation tool."""

    job_url: str = Field(..., min_length=10, description="JustJoin offer URL.")
    full_name: str = Field(..., min_length=2, description="First and last name.")
    email: EmailStr = Field(..., description="Applicant email.")
    resume_path: str = Field(..., min_length=1, description="Path to resume file.")
    attach_message: Optional[str] = Field(
        default=None,
        description="Optional message to employer.",
    )
    headless: bool = Field(default=True, description="Run browser headless.")
    timeout_sec: int = Field(default=45, ge=10, le=300, description="Timeout per step.")
    captcha_wait_sec: int = Field(
        default=180,
        ge=0,
        le=900,
        description="Max wait for manual captcha solve if auto fails.",
    )
    slow_mo_ms: int = Field(default=0, ge=0, le=2000, description="Slow motion ms.")
    use_captcha_solver: bool = Field(
        default=True,
        description="Use 2Captcha API for automatic captcha solving."
    )


class ApplyResult(BaseModel):
    """JSON-serializable result."""

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
        locator.click(timeout=timeout_ms, no_wait_after=True)
        return True
    except Exception:
        return False




def _dismiss_popups_fast(page) -> None:

    for _ in range(4):
        selectors = [
            "button:has-text('Accept all'):visible",
            "button:has-text('ACCEPT ALL'):visible",
            "button:has-text('Accept'):visible",
            "button:has-text('Akceptuj'):visible",
            "[id*='cookie'] button:visible",
            ".cookie-banner button:visible",
            "#cookiescript_accept"
        ]

        for sel in selectors:
            btn = page.locator(sel).first
            if btn.count() > 0:
                try:
                    btn.click(timeout=500, no_wait_after=True)
                    logger.info("✅ Cookie баннер закрыт через кнопку")
                    page.wait_for_timeout(500)
                    return
                except Exception:
                    continue

        page.wait_for_timeout(200)


    try:
        page.evaluate("""
            () => {
            
                const cookieWrapper = document.getElementById('cookiescript_injected_wrapper');
                if (cookieWrapper) {
                    cookieWrapper.remove();
                }

             
                const cookieBanners = document.querySelectorAll(
                    '[id*="cookie"], [class*="cookie"], [id*="consent"], [class*="consent"]'
                );
                cookieBanners.forEach(el => {
                    if (el.offsetHeight > 50) {  // только большие элементы
                        el.remove();
                    }
                });

        
                document.body.style.overflow = 'auto';
            }
        """)
        logger.info("✅ Cookie баннеры удалены через JavaScript")
    except Exception as e:
        logger.warning(f"Не удалось удалить баннеры через JS: {e}")


def _is_captcha_present(page) -> bool:
    try:
        txt = page.locator(
            ":text-matches('i am not a robot|captcha|verify you are human|"
            "nie jestem robotem|potwierdź', 'i')"
        )
        if txt.count() > 0 and txt.first.is_visible():
            return True
    except Exception:
        pass


    try:
        fr = page.locator(
            "iframe[src*='recaptcha'][src*='bframe'], "
            "iframe[src*='recaptcha'][src*='fallback'], "
            "iframe[src*='hcaptcha'][src*='checkbox'], "
            "iframe[src*='hcaptcha'][src*='challenge']"
        )
        if fr.count() > 0 and fr.first.is_visible():
            return True
    except Exception:
        pass


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


def _handle_captcha_with_solver(page, modal, captcha_wait_sec: int, use_solver: bool = True) -> bool:

    if not _is_captcha_present(page):
        logger.info("Капча не обнаружена")
        return True

    logger.warning("⚠️ Капча обнаружена!")


    try:
        page.screenshot(path="captcha_detected.png", full_page=True)
    except Exception:
        pass


    if use_solver:
        try:
            solver = CaptchaSolver()
            logger.info("🤖 Запускаем автоматическое решение капчи через 2Captcha...")


            captcha_type = "recaptcha"
            if page.locator("iframe[src*='hcaptcha']").count() > 0:
                captcha_type = "hcaptcha"
                logger.info("Обнаружена hCaptcha")
            else:
                logger.info("Обнаружена reCAPTCHA")


            site_key = extract_sitekey_from_page(page)
            if not site_key:
                logger.error("❌ Не удалось найти sitekey капчи")
                raise Exception("sitekey not found")

            logger.info(f"Найден sitekey: {site_key[:20]}...")


            if captcha_type == "recaptcha":
                token = solver.solve_recaptcha_v2(page.url, site_key)
            else:
                token = solver.solve_hcaptcha(page.url, site_key)

            if not token:
                logger.error("❌ 2Captcha не вернула токен")
                raise Exception("No token from solver")

            logger.info("✅ Получен токен от 2Captcha")


            success = inject_captcha_solution(page, token, captcha_type)
            if success:
                logger.info("✅ Капча решена автоматически!")
                page.wait_for_timeout(1500)
                return True
            else:
                raise Exception("Failed to inject token")

        except Exception as e:
            logger.error(f"❌ Ошибка автоматического решения капчи: {e}")
            logger.warning("Падаем на ручное решение...")


    if captcha_wait_sec > 0:
        logger.warning(f"⏳ Ожидаем ручного решения капчи ({captcha_wait_sec}с)...")
        return _wait_for_captcha_clear(page, captcha_wait_sec)

    return False


def _open_apply_modal_fast(page, timeout_ms: int) -> None:

    try:
        page.wait_for_load_state("domcontentloaded", timeout=timeout_ms // 2)
    except Exception:
        pass

    _dismiss_popups_fast(page)


    apply_btn = page.locator(
        "button[data-test-id*='apply']:visible, "
        "button.MuiButton-containedPrimary:has-text('Apply'):visible, "
        "a[href*='apply']:visible, "
        ":is(button, [role='button']):has-text('Apply'):visible, "
        ":is(button, [role='button']):has-text('Aplikuj'):visible"
    )

    try:
        apply_btn.first.wait_for(state="visible", timeout=timeout_ms // 2)
    except Exception:
        logger.warning("Apply кнопка не найдена быстро, пробуем fallback...")
        apply_btn = page.locator(":is(button,a):has-text('Apply'):visible")
        apply_btn.first.wait_for(state="visible", timeout=timeout_ms)


    btn = apply_btn.first
    btn.scroll_into_view_if_needed(timeout=timeout_ms // 4)

    try:
        btn.click(timeout=2000, no_wait_after=True)
    except Exception:
        btn.click(timeout=timeout_ms, force=True, no_wait_after=True)


    modal_locator = page.locator(
        "[role='dialog']:visible, "
        ".MuiDialog-root:visible, "
        "div[class*='modal']:visible"
    ).filter(has_text=re.compile(r"apply", re.I))

    try:
        modal_locator.first.wait_for(state="visible", timeout=3000)
        logger.info("✅ Apply модалка открыта")
    except Exception:
        page.get_by_text(re.compile(r"You apply for", re.I)).wait_for(
            state="visible", timeout=timeout_ms
        )


def _get_modal_root(page):

    dialog = page.locator("[role=dialog],[aria-modal=true]").filter(
        has_text=re.compile(r"You apply for|Apply", re.I)
    )
    if dialog.count() > 0:
        return dialog.first

    root = page.locator("div:has-text('You apply for')").filter(
        has=page.locator("input")
    )
    if root.count() > 0:
        return root.first

    return page.locator("body")


def _fill_text_field_fast(modal, *, label: str, value: str, placeholder_hint: Optional[str] = None) -> None:

    try:
        modal.get_by_label(label, exact=False).fill(value)
        logger.info(f"✅ Поле '{label}' заполнено по label")
        return
    except Exception:
        pass


    if placeholder_hint:
        loc = modal.locator(f"input[placeholder*='{placeholder_hint}' i]")
        if loc.count() > 0:
            loc.first.fill(value)
            logger.info(f"✅ Поле '{label}' заполнено по placeholder")
            return


    label_loc = modal.get_by_text(label, exact=False)
    if label_loc.count() > 0:
        near = label_loc.first.locator("xpath=following::input[1]")
        near.fill(value)
        logger.info(f"✅ Поле '{label}' заполнено рядом с текстом")
        return

    raise RuntimeError(f"Could not locate field: {label}")


def _upload_resume_fast(page, modal, resume_path: str, timeout_ms: int) -> None:

    p = str(Path(resume_path).expanduser())


    file_inputs = modal.locator("input[type='file']")
    if file_inputs.count() > 0:
        file_inputs.first.set_input_files(p, timeout=timeout_ms // 2)
        logger.info("✅ Резюме загружено напрямую")
        return


    add_doc = modal.get_by_text("Add document", exact=False)
    try:
        with page.expect_file_chooser(timeout=timeout_ms // 2) as fc_info:
            add_doc.click(timeout=timeout_ms // 2, no_wait_after=True)
        fc_info.value.set_files(p)
        logger.info("✅ Резюме загружено через file chooser")
        return
    except Exception:
        pass

    # Клик на область загрузки
    upload_area = modal.locator(":has-text('Add document')")
    _try_click(upload_area.first, timeout_ms=timeout_ms // 2)
    file_inputs = modal.locator("input[type='file']")
    if file_inputs.count() > 0:
        file_inputs.first.set_input_files(p, timeout=timeout_ms // 2)
        logger.info("✅ Резюме загружено после клика на область")
        return

    raise RuntimeError("Could not upload resume")


def _check_consent_fast(modal, timeout_ms: int) -> None:

    phrases = [
        re.compile(r"Wyrażam zgodę na przetwarzanie", re.I),
        re.compile(r"I\s*agree.*processing.*data", re.I),
        re.compile(r"consent.*processing", re.I),
    ]

    # По label
    for ph in phrases:
        try:
            checkbox = modal.get_by_label(ph)

            if checkbox.count() > 0:

                parent_text = checkbox.first.locator("xpath=ancestor::label[1]").inner_text().lower()
                if "marketing" in parent_text or "newsletter" in parent_text:
                    logger.info("⏭️ Пропускаем маркетинговый чекбокс")
                    continue

                checkbox.check(timeout=timeout_ms // 2)
                logger.info("✅ Согласие проставлено по label")
                return
        except Exception:
            pass


    for ph in phrases:
        txt = modal.get_by_text(ph)
        if txt.count() > 0:
            try:
                text_content = txt.first.inner_text().lower()
                if "marketing" in text_content or "newsletter" in text_content:
                    continue

                txt.first.click(timeout=timeout_ms // 2)
                logger.info("✅ Согласие проставлено кликом по тексту")
                return
            except Exception:
                pass

    for ph in phrases:
        txt = modal.get_by_text(ph)
        if txt.count() > 0:
            container = txt.first.locator("xpath=ancestor::*[self::label or self::div][1]")
            cb = container.locator("input[type='checkbox']")
            if cb.count() > 0:
                try:

                    is_required = cb.first.get_attribute("required") is not None
                    parent_text = container.inner_text().lower()

                    if is_required or ("marketing" not in parent_text and "newsletter" not in parent_text):
                        cb.first.check(timeout=timeout_ms // 2)
                        logger.info("✅ Согласие проставлено через чекбокс")
                        return
                except Exception:
                    pass

    raise RuntimeError("Could not find required consent checkbox")


def _is_enabled(locator) -> bool:
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


def _submit_fast(modal, timeout_ms: int) -> None:

    page = modal.page


    try:
        page.evaluate("""
            () => {
        
                const overlays = document.querySelectorAll(
                    '#cookiescript_injected_wrapper, ' +
                    '[id*="cookie"], [class*="cookie"], ' +
                    '[id*="overlay"], [class*="overlay"], ' +
                    '[id*="backdrop"], [class*="backdrop"]'
                );
                overlays.forEach(el => {
                    const style = window.getComputedStyle(el);
                    const zIndex = parseInt(style.zIndex) || 0;
             
                    if (zIndex > 100 || el.id.includes('cookie')) {
                        el.remove();
                    }
                });

                document.body.style.pointerEvents = 'auto';
            }
        """)
        logger.info("✅ Оверлеи удалены перед submit")
    except Exception as e:
        logger.warning(f"Не удалось удалить оверлеи: {e}")

    def pick_button():
        btn = modal.locator("button[type='submit']:visible").filter(
            has_text=re.compile(r"Apply|Aplikuj", re.I)
        )
        if btn.count() > 0:
            return btn.last


        btn = modal.locator(
            "button:visible:has-text('Apply'), "
            "button:visible:has-text('Aplikuj'), "
            ":is(button,[role='button']):visible:has-text('Apply')"
        )
        if btn.count() == 0:
            raise RuntimeError("Submit button not found")
        return btn.last

    deadline = time.time() + (timeout_ms / 1000.0)
    last_err = None

    while time.time() < deadline:
        try:
            btn = pick_button()
            btn.scroll_into_view_if_needed(timeout=timeout_ms // 4)

            if not _is_enabled(btn):
                page.wait_for_timeout(250)
                continue


            try:
                btn.click(timeout=2000, no_wait_after=True)
                logger.info("✅ Submit нажат (обычный клик)")
                return
            except Exception:

                btn.click(timeout=timeout_ms, force=True, no_wait_after=True)
                logger.info("✅ Submit нажат (force клик)")
                return

        except Exception as e:
            last_err = e
            try:
                page.wait_for_timeout(250)
            except Exception:
                time.sleep(0.25)

    raise RuntimeError(f"Could not click submit. Last error: {last_err}")


def _wait_for_confirmation(page, modal, timeout_ms: int) -> bool:

    try:
        modal.wait_for(state="hidden", timeout=timeout_ms)
        return True
    except Exception:
        pass


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
        ":text-matches('error|required|invalid|błąd|wymagane', 'i')"
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
        use_captcha_solver: bool = True,  # НОВЫЙ ПАРАМЕТР
) -> Dict[str, Any]:

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
            use_captcha_solver=use_captcha_solver,
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
            error="Playwright not installed. Run: poetry add playwright && poetry run playwright install chromium",
        ).model_dump()

    debug: Dict[str, Any] = {"resume_filename": _safe_filename(validated.resume_path)}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=validated.headless,
                slow_mo=validated.slow_mo_ms
            )
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()
            page.set_default_timeout(timeout_ms)
            page.set_default_navigation_timeout(timeout_ms)


            step = "open_offer"
            page.goto(validated.job_url, wait_until="domcontentloaded", timeout=timeout_ms)
            _dismiss_popups_fast(page)


            step = "open_apply_modal"
            try:
                _open_apply_modal_fast(page, timeout_ms=timeout_ms)
            except Exception as e:
                try:
                    page.screenshot(path="apply_open_modal_fail.png", full_page=True)
                    debug["screenshot"] = "apply_open_modal_fail.png"
                except Exception:
                    pass
                raise

            modal = _get_modal_root(page)


            _dismiss_popups_fast(page)


            step = "fill_form"
            _fill_text_field_fast(modal, label="First and last name", value=validated.full_name,
                                  placeholder_hint="first")
            _fill_text_field_fast(modal, label="Email", value=str(validated.email), placeholder_hint="email")


            if validated.attach_message:
                try:
                    toggle = modal.get_by_text("Attach a message", exact=False)
                    _try_click(toggle, timeout_ms=1200)
                    ta = modal.locator("textarea")
                    if ta.count() > 0:
                        ta.first.fill(validated.attach_message)
                except Exception:
                    logger.info("Attach-message не доступен")


            step = "upload_resume"
            _upload_resume_fast(page, modal, validated.resume_path, timeout_ms=timeout_ms)


            step = "consent_checkbox"
            _check_consent_fast(modal, timeout_ms=timeout_ms)


            page.wait_for_timeout(500)
            _dismiss_popups_fast(page)


            step = "submit"
            _submit_fast(modal, timeout_ms=timeout_ms)


            if _wait_for_confirmation(page, modal, timeout_ms=8000):
                browser.close()
                return ApplyResult(
                    ok=True,
                    job_url=validated.job_url,
                    applied=True,
                    step="done",
                    debug=debug,
                ).model_dump()


            if _is_captcha_present(page):
                debug["captcha_detected"] = True
                logger.warning("⚠️ Обнаружена капча после submit")

                captcha_solved = _handle_captcha_with_solver(
                    page=page,
                    modal=modal,
                    captcha_wait_sec=validated.captcha_wait_sec,
                    use_solver=validated.use_captcha_solver
                )

                if not captcha_solved:
                    try:
                        page.screenshot(path="captcha_unsolved.png", full_page=True)
                        debug["screenshot"] = "captcha_unsolved.png"
                    except Exception:
                        pass

                    browser.close()
                    return ApplyResult(
                        ok=False,
                        job_url=validated.job_url,
                        applied=False,
                        step="captcha",
                        error="Капча не решена (ни автоматически, ни вручную)",
                        debug=debug,
                    ).model_dump()


                logger.info("✅ Капча решена, повторяем submit...")
                page.wait_for_timeout(1000)

                try:
                    modal = _get_modal_root(page)
                    _submit_fast(modal, timeout_ms=timeout_ms)
                except Exception as e:
                    logger.warning(f"Не удалось повторить submit после капчи: {e}")


            step = "confirm"
            try:
                page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
            except Exception:
                pass
            page.wait_for_timeout(1000)

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

            try:
                page.screenshot(path="apply_failure.png", full_page=True)
                debug["screenshot"] = "apply_failure.png"
            except Exception:
                pass

            browser.close()
            return ApplyResult(
                ok=False,
                job_url=validated.job_url,
                applied=False,
                step="confirm",
                error=err_text or "No success confirmation detected",
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
    import json
    import argparse

    parser = argparse.ArgumentParser(description="Apply to JustJoin job with auto captcha solver")
    parser.add_argument("--url", required=True, help="Job URL")
    parser.add_argument("--name", required=True, help="Full name")
    parser.add_argument("--email", required=True, help="Email")
    parser.add_argument("--resume", required=True, help="Resume path")
    parser.add_argument("--message", default=None, help="Optional message")
    parser.add_argument("--headed", action="store_true", help="Run with visible browser")
    parser.add_argument("--slow", type=int, default=0, help="Slow motion ms")
    parser.add_argument("--timeout", type=int, default=45, help="Timeout seconds")
    parser.add_argument("--captcha-wait", type=int, default=180, help="Manual captcha wait")
    parser.add_argument("--no-solver", action="store_true", help="Disable auto captcha solver")

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
        captcha_wait_sec=args.captcha_wait,
        use_captcha_solver=not args.no_solver,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))