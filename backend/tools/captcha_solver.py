

import os
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class CaptchaSolver:


    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("CAPTCHA_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "CAPTCHA_API_KEY не найден! "
                "Добавь в .env файл: CAPTCHA_API_KEY=твой_ключ"
            )

        try:
            from twocaptcha import TwoCaptcha
            self.solver = TwoCaptcha(self.api_key)
            logger.info("✅ CaptchaSolver инициализирован")
        except ImportError:
            raise ImportError(
                "Библиотека 2captcha-python не установлена! "
                "Установи: pip install 2captcha-python"
            )

    def solve_recaptcha_v2(self, page_url: str, site_key: str) -> Optional[str]:

        try:
            logger.info(f"📤 Отправляем reCAPTCHA на решение...")
            logger.info(f"   URL: {page_url}")
            logger.info(f"   SiteKey: {site_key[:20]}...")

            result = self.solver.recaptcha(
                sitekey=site_key,
                url=page_url
            )

            logger.info(f"✅ reCAPTCHA решена! ID: {result.get('captchaId', 'N/A')}")
            return result.get('code')

        except Exception as e:
            logger.error(f"❌ Ошибка решения reCAPTCHA: {e}")
            return None

    def solve_hcaptcha(self, page_url: str, site_key: str) -> Optional[str]:

        try:
            logger.info(f"📤 Отправляем hCaptcha на решение...")
            logger.info(f"   URL: {page_url}")
            logger.info(f"   SiteKey: {site_key[:20]}...")

            result = self.solver.hcaptcha(
                sitekey=site_key,
                url=page_url
            )

            logger.info(f"✅ hCaptcha решена! ID: {result.get('captchaId', 'N/A')}")
            return result.get('code')

        except Exception as e:
            logger.error(f"❌ Ошибка решения hCaptcha: {e}")
            return None

    def get_balance(self) -> float:

        try:
            balance = self.solver.balance()
            logger.info(f"💰 Баланс 2Captcha: ${balance:.2f}")
            return float(balance)
        except Exception as e:
            logger.error(f"❌ Ошибка получения баланса: {e}")
            return 0.0


def extract_sitekey_from_page(page) -> Optional[str]:

    try:

        recaptcha = page.locator("[data-sitekey]").first
        if recaptcha.count() > 0:
            key = recaptcha.get_attribute("data-sitekey")
            if key:
                logger.info(f"🔑 Найден reCAPTCHA sitekey (data-sitekey): {key[:20]}...")
                return key


        hcaptcha = page.locator(".h-captcha[data-sitekey]").first
        if hcaptcha.count() > 0:
            key = hcaptcha.get_attribute("data-sitekey")
            if key:
                logger.info(f"🔑 Найден hCaptcha sitekey: {key[:20]}...")
                return key


        iframes = page.locator("iframe[src*='recaptcha'], iframe[src*='hcaptcha']")
        if iframes.count() > 0:
            src = iframes.first.get_attribute("src")
            if src and ("k=" in src or "sitekey=" in src):

                match = re.search(r'[?&](?:k|sitekey)=([^&]+)', src)
                if match:
                    key = match.group(1)
                    logger.info(f"🔑 Найден sitekey в iframe src: {key[:20]}...")
                    return key


        try:

            js_sitekey = page.evaluate("""
                () => {
           
                    if (window.___grecaptcha_cfg && window.___grecaptcha_cfg.clients) {
                        for (let id in window.___grecaptcha_cfg.clients) {
                            let client = window.___grecaptcha_cfg.clients[id];
                            if (client && client.sitekey) {
                                return client.sitekey;
                            }
                        }
                    }
               
                    if (window.hcaptcha && window.hcaptcha.sitekey) {
                        return window.hcaptcha.sitekey;
                    }
                    return null;
                }
            """)
            if js_sitekey:
                logger.info(f"🔑 Найден sitekey через JavaScript: {js_sitekey[:20]}...")
                return js_sitekey
        except Exception:
            pass

        logger.warning("❌ Sitekey не найден на странице")
        return None

    except Exception as e:
        logger.error(f"❌ Ошибка извлечения sitekey: {e}")
        return None


def inject_captcha_solution(page, token: str, captcha_type: str = "recaptcha") -> bool:

    try:
        if captcha_type == "recaptcha":

            page.evaluate(f"""
                () => {{
            
                    let textarea = document.getElementById('g-recaptcha-response');
                    if (textarea) {{
                        textarea.innerHTML = '{token}';
                        textarea.value = '{token}';
                    }}

                
                    try {{
                        if (window.___grecaptcha_cfg && window.___grecaptcha_cfg.clients) {{
                            for (let id in window.___grecaptcha_cfg.clients) {{
                                let client = window.___grecaptcha_cfg.clients[id];
                                if (client && client.callback) {{
                                    client.callback('{token}');
                                }}
                            }}
                        }}
                    }} catch(e) {{
                        console.log('reCAPTCHA callback error:', e);
                    }}
                }}
            """)
            logger.info("✅ reCAPTCHA токен вставлен в страницу")

        elif captcha_type == "hcaptcha":

            page.evaluate(f"""
                () => {{
                    // Заполняем textarea
                    let textarea = document.querySelector('[name="h-captcha-response"]');
                    if (textarea) {{
                        textarea.innerHTML = '{token}';
                        textarea.value = '{token}';
                    }}

                    // Вызываем callback если есть
                    try {{
                        if (window.hcaptcha && window.hcaptcha.callback) {{
                            window.hcaptcha.callback('{token}');
                        }}
                    }} catch(e) {{
                        console.log('hCaptcha callback error:', e);
                    }}
                }}
            """)
            logger.info("✅ hCaptcha токен вставлен в страницу")


        page.wait_for_timeout(1500)
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка вставки токена: {e}")
        return False



if __name__ == "__main__":

    import sys
    from playwright.sync_api import sync_playwright


    try:
        solver = CaptchaSolver()
        balance = solver.get_balance()
        print(f"\n💰 Ваш баланс 2Captcha: ${balance:.2f}")

        if balance < 0.01:
            print("⚠️ Баланс слишком низкий! Пополните аккаунт на https://2captcha.com")
            sys.exit(1)

    except ValueError as e:
        print(f"\n❌ ОШИБКА: {e}")
        print("\nИнструкция:")
        print("1. Зарегистрируйся на https://2captcha.com")
        print("2. Пополни баланс (~$3)")
        print("3. Получи API ключ")
        print("4. Добавь в .env: CAPTCHA_API_KEY=твой_ключ")
        sys.exit(1)
    except ImportError as e:
        print(f"\n❌ ОШИБКА: {e}")
        print("\nУстанови библиотеку: pip install 2captcha-python")
        sys.exit(1)


    print("\n🧪 Запускаем тест на странице с капчей...")

    TEST_URL = "https://www.google.com/recaptcha/api2/demo"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print(f"📄 Открываем: {TEST_URL}")
        page.goto(TEST_URL)
        page.wait_for_timeout(2000)


        site_key = extract_sitekey_from_page(page)

        if not site_key:
            print("❌ Не удалось найти sitekey")
            browser.close()
            sys.exit(1)


        print(f"🤖 Отправляем капчу на решение...")
        token = solver.solve_recaptcha_v2(TEST_URL, site_key)

        if not token:
            print("❌ Не удалось получить токен от 2Captcha")
            browser.close()
            sys.exit(1)

        print(f"✅ Получен токен: {token[:30]}...")


        success = inject_captcha_solution(page, token, "recaptcha")

        if success:
            print("✅ Токен вставлен! Пробуем нажать Submit...")
            page.locator("#recaptcha-demo-submit").click()
            page.wait_for_timeout(3000)
            print("✅ Тест завершён! Проверь браузер.")

        input("Нажми Enter чтобы закрыть браузер...")
        browser.close()