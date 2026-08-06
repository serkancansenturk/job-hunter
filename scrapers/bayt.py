"""
Bayt.com scraper — Orta Doğu'nun en büyük iş platformu.
"""
import time
import httpx
from bs4 import BeautifulSoup
from models.job import Job
from .base import BaseScraper


class BaytScraper(BaseScraper):
    name = "bayt"
    SEARCH_URL = "https://www.bayt.com/en/international/jobs/"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    def scrape(
        self,
        search_terms: list[str],
        locations: list[str],
        results_wanted: int = 20,
    ) -> list[Job]:
        jobs: list[Job] = []

        for term in search_terms:
            self._log(f"Bayt.com tarıyor: '{term}'")
            try:
                slug = term.lower().replace(" ", "-").replace("&", "and")
                url = f"{self.SEARCH_URL}{slug}-jobs/"
                resp = httpx.get(
                    url,
                    headers=self.HEADERS,
                    timeout=15,
                    follow_redirects=True,
                )
                if resp.status_code == 404:
                    # Fallback: search endpoint
                    resp = httpx.get(
                        "https://www.bayt.com/en/international/jobs/",
                        params={"q": term},
                        headers=self.HEADERS,
                        timeout=15,
                        follow_redirects=True,
                    )

                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")

                cards = soup.select("li[data-js-job]")
                for card in cards[:results_wanted]:
                    title_el = card.select_one("h2.m0 a")
                    company_el = card.select_one("b.jb-company")
                    location_el = card.select_one("span.jb-loc")
                    url_el = card.select_one("h2.m0 a")

                    if not title_el:
                        continue

                    job = Job(
                        title=title_el.get_text(strip=True),
                        company=company_el.get_text(strip=True) if company_el else "",
                        location=location_el.get_text(strip=True) if location_el else "Middle East",
                        url="https://www.bayt.com" + url_el["href"] if url_el and url_el.get("href") else "",
                        platform="bayt",
                        is_remote=False,
                    )
                    jobs.append(job)

                time.sleep(2)

            except Exception as e:
                self._log(f"[red]Bayt.com hatası ({term}): {e}[/red]")

        self._log(f"{len(jobs)} ilan bulundu")
        return jobs
