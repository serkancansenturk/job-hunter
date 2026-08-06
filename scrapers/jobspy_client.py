"""
LinkedIn, Indeed, Glassdoor ve ZipRecruiter için python-jobspy kullanır.
Tek scraper, dört platform.
"""
from datetime import datetime
from models.job import Job
from .base import BaseScraper


class JobSpyScraper(BaseScraper):
    name = "jobspy"

    def __init__(self, platforms: list[str] = None):
        # linkedin, indeed, glassdoor, zip_recruiter, google
        self.platforms = platforms or ["linkedin", "indeed", "glassdoor"]

    def scrape(
        self,
        search_terms: list[str],
        locations: list[str],
        results_wanted: int = 20,
    ) -> list[Job]:
        try:
            from jobspy import scrape_jobs
        except ImportError:
            raise RuntimeError("python-jobspy yüklü değil: pip install python-jobspy")

        jobs: list[Job] = []

        for term in search_terms:
            for location in locations:
                self._log(f"Tarıyor: '{term}' @ {location}")
                try:
                    df = scrape_jobs(
                        site_name=self.platforms,
                        search_term=term,
                        location=location,
                        results_wanted=results_wanted,
                        hours_old=168,      # Son 7 gün
                        country_indeed="Turkey" if "Turkey" in location else "worldwide",
                    )
                    if df is None or df.empty:
                        continue

                    for _, row in df.iterrows():
                        job = Job(
                            title=str(row.get("title", "")),
                            company=str(row.get("company", "")),
                            location=str(row.get("location", "")),
                            description=str(row.get("description", "") or ""),
                            url=str(row.get("job_url", "") or ""),
                            platform=str(row.get("site", "jobspy")),
                            is_remote=bool(row.get("is_remote", False)),
                            posted_at=self._parse_date(row.get("date_posted")),
                        )
                        jobs.append(job)

                except Exception as e:
                    self._log(f"[red]Hata ({term}/{location}): {e}[/red]")

        # Deduplicate by job_id
        seen: set[str] = set()
        unique: list[Job] = []
        for j in jobs:
            if j.job_id not in seen:
                seen.add(j.job_id)
                unique.append(j)

        self._log(f"{len(unique)} benzersiz ilan bulundu")
        return unique

    @staticmethod
    def _parse_date(val) -> datetime:
        if val is None:
            return None
        if isinstance(val, datetime):
            return val
        try:
            return datetime.fromisoformat(str(val))
        except Exception:
            return None
