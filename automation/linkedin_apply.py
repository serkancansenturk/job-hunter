"""
LinkedIn Easy Apply otomasyonu.
Playwright kullanır — önce `playwright install chromium` çalıştır.
"""
from pathlib import Path
from config.cv_base import CV_DATA
from config.settings import get_settings
from models.application import Application, ApplicationStatus
from storage.database import Database


class LinkedInApplier:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self._browser = None
        self._page = None

    def apply(self, application: Application, job_url: str) -> bool:
        """
        Onaylanmış başvuru için LinkedIn Easy Apply akışını yürütür.
        True: başarılı, False: başarısız/manuel müdahale gerekiyor.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise RuntimeError("Playwright yüklü değil: pip install playwright && playwright install chromium")

        settings = get_settings()
        personal = CV_DATA["personal"]

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            ctx = browser.new_context()
            page = ctx.new_page()

            # Login
            if not self._login(page, settings.linkedin_email, settings.linkedin_password):
                browser.close()
                return False

            # İlan sayfasına git
            page.goto(job_url, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            # Easy Apply butonunu bul
            easy_apply = page.locator("button:has-text('Easy Apply'), button:has-text('Kolay Başvur')")
            if easy_apply.count() == 0:
                print(f"Easy Apply butonu bulunamadı: {job_url}")
                browser.close()
                return False

            easy_apply.first.click()
            page.wait_for_timeout(1500)

            # Form adımlarını doldur
            success = self._fill_form_steps(page, personal, application)

            browser.close()
            return success

    def _login(self, page, email: str, password: str) -> bool:
        if not email or not password:
            print("LinkedIn kimlik bilgileri .env dosyasında tanımlı değil.")
            return False

        page.goto("https://www.linkedin.com/login")
        page.fill("#username", email)
        page.fill("#password", password)
        page.click("button[type=submit]")
        page.wait_for_timeout(3000)

        if "feed" in page.url or "mynetwork" in page.url:
            return True
        print("LinkedIn login başarısız — CAPTCHA veya 2FA gerekebilir.")
        return False

    def _fill_form_steps(self, page, personal: dict, application: Application) -> bool:
        """Multi-step Easy Apply formunu doldurur."""
        max_steps = 10
        for step in range(max_steps):
            page.wait_for_timeout(1000)

            # İletişim bilgileri
            self._try_fill(page, "input[name*='phone'], input[id*='phone']", personal["phone"])
            self._try_fill(page, "input[name*='city'], input[id*='city']", "İstanbul")

            # CV yükleme
            if application.cv_version_path:
                cv_path = Path(application.cv_version_path)
                if cv_path.exists():
                    upload = page.locator("input[type='file']")
                    if upload.count() > 0:
                        upload.first.set_input_files(str(cv_path))
                        page.wait_for_timeout(1000)

            # İlerle veya gönder
            next_btn = page.locator("button:has-text('Next'), button:has-text('Continue'), button:has-text('İleri')")
            submit_btn = page.locator("button:has-text('Submit application'), button:has-text('Gönder')")

            if submit_btn.count() > 0:
                submit_btn.first.click()
                page.wait_for_timeout(2000)
                print("✓ Başvuru gönderildi!")
                return True
            elif next_btn.count() > 0:
                next_btn.first.click()
            else:
                break

        return False

    @staticmethod
    def _try_fill(page, selector: str, value: str) -> None:
        try:
            el = page.locator(selector)
            if el.count() > 0 and el.first.is_visible():
                el.first.fill(value)
        except Exception:
            pass
