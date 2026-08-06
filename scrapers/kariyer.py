"""
Kariyer.net scraper — BeautifulSoup ile HTML parse eder.
Rate limiting'e dikkat: aramalar arası 2 saniye bekleme var.
"""
import time
import httpx
from bs4 import BeautifulSoup
from models.job import Job
from .base import BaseScraper


class KariyerScraper(BaseScraper):
    name = "kariyer"
    BASE_URL = "https://www.kariyer.net"
    SEARCH_URL = "https://www.kariyer.net/is-ilanlari"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    }

    def scrape(
        self,
        search_terms: list[str],
        locations: list[str],
        results_wanted: int = 20,
    ) -> list[Job]:
        jobs: list[Job] = []

        for term in search_terms:
            self._log(f"Kariyer.net tarıyor: '{term}'")
            try:
                params = {"q": term}
                resp = httpx.get(
                    self.SEARCH_URL,
                    params=params,
                    headers=self.HEADERS,
                    timeout=15,
                    follow_redirects=True,
                )
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                # CSS selector'lar güncellendi
                cards = soup.select("div[data-test-id='jobCard']") or soup.select("article.job-card") or soup.select("a.job-item")

                for card in cards[:results_wanted]:
                    if isinstance(card, str):
                        continue

                    title_el = card.select_one("h2") or card.select_one("a[title]")
                    company_el = card.select_one("[data-test-id='company']") or card.select_one(".company-name")
                    location_el = card.select_one("[data-test-id='location']") or card.select_one(".location")
                    url_el = card.select_one("a[href*='is-ilani']") or card.select_one("a[href]")

                    if not (title_el and url_el):
                        continue

                    title = title_el.get_text(strip=True)
                    if len(title) < 3:
                        continue

                    job = Job(
                        title=title,
                        company=company_el.get_text(strip=True) if company_el else "Bilinmiyor",
                        location=location_el.get_text(strip=True) if location_el else "Türkiye",
                        url=url_el.get("href", "") if url_el.get("href", "").startswith("http") else self.BASE_URL + (url_el.get("href", "") or ""),
                        platform="kariyer",
                        is_remote="remote" in title.lower() or "uzaktan" in title.lower(),
                    )
                    jobs.append(job)

                time.sleep(1)

            except Exception as e:
                self._log(f"Kariyer.net hatası ({term}): {str(e)[:50]}")

        self._log(f"{len(jobs)} ilan bulundu")
        return jobs
