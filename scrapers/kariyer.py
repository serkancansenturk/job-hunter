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
                params = {"q": term, "wt": "1"}  # wt=1 -> tam zamanlı
                resp = httpx.get(
                    self.SEARCH_URL,
                    params=params,
                    headers=self.HEADERS,
                    timeout=15,
                    follow_redirects=True,
                )
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")

                cards = soup.select("div.list-items-wrapper article.list-item")
                for card in cards[:results_wanted]:
                    title_el = card.select_one("h2.list-item-title a")
                    company_el = card.select_one("span.list-item-info-label")
                    location_el = card.select_one("span.list-item-info-cities")
                    url_el = card.select_one("h2.list-item-title a")

                    if not title_el:
                        continue

                    job = Job(
                        title=title_el.get_text(strip=True),
                        company=company_el.get_text(strip=True) if company_el else "",
                        location=location_el.get_text(strip=True) if location_el else "Türkiye",
                        url=self.BASE_URL + url_el["href"] if url_el and url_el.get("href") else "",
                        platform="kariyer",
                        is_remote=False,
                    )
                    jobs.append(job)

                time.sleep(2)  #礼貌等待

            except Exception as e:
                self._log(f"[red]Kariyer.net hatası ({term}): {e}[/red]")

        self._log(f"{len(jobs)} ilan bulundu")
        return jobs
