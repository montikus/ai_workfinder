

import logging

logger = logging.getLogger(__name__)


def kill_all_overlays(page) -> None:

    try:
        page.evaluate("""
            () => {
                console.log('[OverlayKiller] Начинаем зачистку...');

             
                const cookieIds = [
                    'cookiescript_injected_wrapper',
                    'cookiescript_injected',
                    'CybotCookiebotDialog',
                    'cookie-banner',
                    'cookie-consent',
                    'gdpr-banner'
                ];

                cookieIds.forEach(id => {
                    const el = document.getElementById(id);
                    if (el) {
                        el.remove();
                        console.log('[OverlayKiller] Удалён:', id);
                    }
                });

           
                const cookieElements = document.querySelectorAll(
                    '[id*="cookie"], [class*="cookie"], ' +
                    '[id*="Cookie"], [class*="Cookie"], ' +
                    '[id*="consent"], [class*="consent"]'
                );

                cookieElements.forEach(el => {
                   
                    if (el.offsetHeight > 30 || el.offsetWidth > 200) {
                        el.remove();
                        console.log('[OverlayKiller] Удалён cookie элемент');
                    }
                });

       
                const overlays = document.querySelectorAll(
                    '[class*="backdrop"], [class*="Backdrop"], ' +
                    '[class*="overlay"], [class*="Overlay"], ' +
                    '[id*="backdrop"], [id*="overlay"]'
                );

                overlays.forEach(el => {
                    const style = window.getComputedStyle(el);
                    const position = style.position;

                    if (position === 'fixed' || position === 'absolute') {
                        el.remove();
                        console.log('[OverlayKiller] Удалён backdrop/overlay');
                    }
                });

              
                const allElements = document.querySelectorAll('*');
                allElements.forEach(el => {
                    const style = window.getComputedStyle(el);
                    const zIndex = parseInt(style.zIndex);

                   
                    if (zIndex > 9999 && !el.querySelector('[role="dialog"]')) {
                        // Проверяем что это не наша нужная модалка
                        const text = el.textContent?.toLowerCase() || '';
                        if (!text.includes('you apply for') && !text.includes('first and last name')) {
                            el.remove();
                            console.log('[OverlayKiller] Удалён элемент с высоким z-index:', zIndex);
                        }
                    }
                });

            
                document.body.style.overflow = 'auto';
                document.body.style.pointerEvents = 'auto';
                document.documentElement.style.overflow = 'auto';

      
                allElements.forEach(el => {
                    const style = window.getComputedStyle(el);
                    if (style.pointerEvents === 'none') {
                        el.style.pointerEvents = 'auto';
                    }
                });

                console.log('[OverlayKiller] Зачистка завершена!');
            }
        """)
        logger.info("💥 OverlayKiller: Все блокирующие элементы удалены")
        page.wait_for_timeout(500)

    except Exception as e:
        logger.warning(f"OverlayKiller error: {e}")


def accept_cookies_aggressive(page) -> bool:

    selectors = [

        "button:has-text('Accept all')",
        "button:has-text('ACCEPT ALL')",
        "button:has-text('Accept All')",
        "button:has-text('Accept')",
        "button:has-text('I agree')",
        "button:has-text('I accept')",
        "button:has-text('Agree')",
        "button:has-text('OK')",


        "button:has-text('Akceptuj wszystkie')",
        "button:has-text('Akceptuj')",
        "button:has-text('Zgadzam się')",


        "#cookiescript_accept",
        "#CybotCookiebotDialogBodyButtonAccept",


        ".cookie-accept",
        ".accept-cookies",
        ".consent-accept",
    ]

    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if btn.count() > 0 and btn.is_visible():
                btn.click(timeout=500, no_wait_after=True)
                logger.info(f"✅ Нажата cookie кнопка: {sel}")
                page.wait_for_timeout(300)
                return True
        except Exception:
            continue

    return False


def ensure_no_overlays(page, max_attempts: int = 3) -> None:
    for attempt in range(max_attempts):
        logger.info(f"🔍 Проверка оверлеев (попытка {attempt + 1}/{max_attempts})...")


        if accept_cookies_aggressive(page):
            page.wait_for_timeout(500)
            continue


        kill_all_overlays(page)


        try:
            overlays = page.evaluate("""
                () => {
                    const problematic = document.querySelectorAll(
                        '#cookiescript_injected_wrapper, ' +
                        '[id*="cookie"][style*="fixed"], ' +
                        '[class*="backdrop"][style*="fixed"]'
                    );
                    return problematic.length;
                }
            """)

            if overlays == 0:
                logger.info("✅ Оверлеи полностью удалены")
                return

        except Exception:
            pass




