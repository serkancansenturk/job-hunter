"""
Remote job boards: Remote.co, WeWorkRemotely, Indeed, StepStone, Reed, EURES
"""
import httpx
from bs4 import BeautifulSoup
from models.job import Job
from .base import BaseScraper


class RemoteCoScraper(BaseScraper):
    name = "remote.co"
    BASE_URL = "https://remote.co/remote-jobs"

    def scrape(self, search_terms: list[str], locations: list[str], results_wanted: int = 20) -> list[Job]:
        jobs = []
        keywords = " ".join(search_terms[:2])

        try:
            url = f"{self.BASE_URL}/search?q={keywords}"
            resp = httpx.get(url, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            for card in soup.select("div.job-card, div.job-post, article.job")[:results_wanted]:
                title = card.select_one("h2, h3, a.job-title")
                company = card.select_one(".company, .employer")
                url_el = card.select_one("a[href*='/jobs/']")

                if not (title and url_el):
                    continue

                job = Job(
                    title=title.get_text(strip=True),
                    company=company.get_text(strip=True) if company else "Remote.co",
                    location="Remote",
                    url="https://remote.co" + url_el.get("href", "") if url_el.get("href", "").startswith("/") else url_el.get("href", ""),
                    platform="remote.co",
                    is_remote=True,
                )
                jobs.append(job)

        except Exception as e:
            self._log(f"Remote.co hatası: {str(e)[:50]}")

        return jobs


class WeWorkRemoteScraper(BaseScraper):
    name = "weworkremotely"
    BASE_URL = "https://weworkremotely.com"

    def scrape(self, search_terms: list[str], locations: list[str], results_wanted: int = 20) -> list[Job]:
        jobs = []

        try:
            # Search endpoint
            keywords = "+".join(search_terms[:2])
            url = f"{self.BASE_URL}/remote-jobs/search?term={keywords}"
            resp = httpx.get(url, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            for card in soup.select("section.jobs li, div.job-card, article.job")[:results_wanted]:
                title_el = card.select_one("h3, a.job-title, a.title")
                company_el = card.select_one(".company, span.company-name")
                url_el = card.select_one("a[href*='/jobs/']") or card.select_one("a[href]")

                if not (title_el and url_el):
                    continue

                href = url_el.get("href", "")
                full_url = self.BASE_URL + href if href.startswith("/") else href

                job = Job(
                    title=title_el.get_text(strip=True),
                    company=company_el.get_text(strip=True) if company_el else "WeWorkRemotely",
                    location="Remote",
                    url=full_url,
                    platform="weworkremotely",
                    is_remote=True,
                )
                jobs.append(job)

        except Exception as e:
            self._log(f"WeWorkRemotely hatası: {str(e)[:50]}")

        return jobs


class LinkedInRSSScraper(BaseScraper):
    name = "linkedin_rss"

    def scrape(self, search_terms: list[str], locations: list[str], results_wanted: int = 20) -> list[Job]:
        """LinkedIn RSS feed'den (limited ama güvenli)"""
        jobs = []

        try:
            # LinkedIn RSS feed public, bot detection yok
            for term in search_terms[:2]:
                rss_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting?keywords={term}&locationId=90000490&start=0"

                resp = httpx.get(rss_url, timeout=10)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "xml")

                for item in soup.select("job")[:results_wanted]:
                    title = item.select_one("title")
                    company = item.select_one("company-name")
                    url = item.select_one("apply-url")

                    if not (title and url):
                        continue

                    job = Job(
                        title=title.get_text(strip=True),
                        company=company.get_text(strip=True) if company else "LinkedIn",
                        location="Multiple",
                        url=url.get_text(strip=True),
                        platform="linkedin",
                        is_remote="remote" in title.get_text(strip=True).lower(),
                    )
                    jobs.append(job)

        except Exception as e:
            self._log(f"LinkedIn RSS hatası: {str(e)[:50]}")

        return jobs[:results_wanted]


class StepStoneScraper(BaseScraper):
    name = "stepstone"
    BASE_URL = "https://www.stepstone.de"

    def scrape(self, search_terms: list[str], locations: list[str], results_wanted: int = 20) -> list[Job]:
        jobs = []

        try:
            for term in search_terms[:2]:
                url = f"{self.BASE_URL}/jobs?keywords={term}&location=Germany,Netherlands,Austria"
                resp = httpx.get(url, timeout=15, follow_redirects=True)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                for card in soup.select("article.job, div.job-item, a.jobList")[:results_wanted]:
                    title = card.select_one("h2, h3, span.jobTitle")
                    company = card.select_one(".company, .employer, span.company")
                    url_el = card.select_one("a[href*='/job/']") or card.select_one("a")

                    if not (title and url_el):
                        continue

                    href = url_el.get("href", "")
                    full_url = self.BASE_URL + href if href.startswith("/") else href

                    job = Job(
                        title=title.get_text(strip=True),
                        company=company.get_text(strip=True) if company else "StepStone",
                        location="Avrupa",
                        url=full_url,
                        platform="stepstone",
                        is_remote="remote" in title.get_text(strip=True).lower(),
                    )
                    jobs.append(job)

        except Exception as e:
            self._log(f"StepStone hatası: {str(e)[:50]}")

        return jobs[:results_wanted]


class ReedScraper(BaseScraper):
    name = "reed"
    BASE_URL = "https://www.reed.co.uk"

    def scrape(self, search_terms: list[str], locations: list[str], results_wanted: int = 20) -> list[Job]:
        jobs = []

        try:
            for term in search_terms[:2]:
                url = f"{self.BASE_URL}/jobs/{term}"
                resp = httpx.get(url, timeout=15, follow_redirects=True)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                for card in soup.select("article, div.job-search__item, a.job-title")[:results_wanted]:
                    title = card.select_one("h2, h3, a.job-title")
                    company = card.select_one(".job-item__company, span.company")
                    url_el = card.select_one("a[href*='/jobs/']") or card.select_one("a")

                    if not (title and url_el):
                        continue

                    href = url_el.get("href", "")
                    full_url = self.BASE_URL + href if href.startswith("/") else href

                    job = Job(
                        title=title.get_text(strip=True),
                        company=company.get_text(strip=True) if company else "Reed",
                        location="UK",
                        url=full_url,
                        platform="reed",
                        is_remote="remote" in title.get_text(strip=True).lower(),
                    )
                    jobs.append(job)

        except Exception as e:
            self._log(f"Reed hatası: {str(e)[:50]}")

        return jobs[:results_wanted]


class EURESScraper(BaseScraper):
    name = "eures"
    BASE_URL = "https://eures.ec.europa.eu"

    def scrape(self, search_terms: list[str], locations: list[str], results_wanted: int = 20) -> list[Job]:
        """EU Official Job Portal"""
        jobs = []

        try:
            # EURES public search (limited API)
            for term in search_terms[:2]:
                url = f"{self.BASE_URL}/portal/en/job-mobility/job-search"
                params = {"keywords": term, "pageSize": results_wanted}

                resp = httpx.get(url, params=params, timeout=15)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")

                for card in soup.select("div.job-item, article.job, li.job-posting")[:results_wanted]:
                    title = card.select_one("h2, h3, a.job-link")
                    company = card.select_one(".employer, .company-name")
                    url_el = card.select_one("a[href*='/job/']") or card.select_one("a")

                    if not (title and url_el):
                        continue

                    job = Job(
                        title=title.get_text(strip=True),
                        company=company.get_text(strip=True) if company else "EURES",
                        location="Europe",
                        url=url_el.get("href", ""),
                        platform="eures",
                        is_remote="remote" in title.get_text(strip=True).lower(),
                    )
                    jobs.append(job)

        except Exception as e:
            self._log(f"EURES hatası: {str(e)[:50]}")

        return jobs[:results_wanted]
