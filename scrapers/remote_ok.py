"""
Remote OK — ücretsiz public API kullanır, auth gerektirmez.
"""
import httpx
from models.job import Job
from .base import BaseScraper


class RemoteOKScraper(BaseScraper):
    name = "remote_ok"
    API_URL = "https://remoteok.com/api"

    def scrape(
        self,
        search_terms: list[str],
        locations: list[str],
        results_wanted: int = 20,
    ) -> list[Job]:
        self._log("Remote OK API sorgulanıyor...")
        try:
            resp = httpx.get(
                self.API_URL,
                headers={"User-Agent": "JobHunterBot/1.0"},
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            self._log(f"[red]Remote OK API hatası: {e}[/red]")
            return []

        # İlk eleman metadata, atla
        posts = [p for p in data if isinstance(p, dict) and p.get("position")]

        keywords_lower = [t.lower() for t in search_terms]
        jobs: list[Job] = []

        for post in posts[:results_wanted * 3]:
            title = str(post.get("position", ""))
            title_lower = title.lower()
            tags = [str(t).lower() for t in (post.get("tags") or [])]

            # Arama terimleriyle eşleşiyor mu?
            if not any(kw in title_lower or kw in " ".join(tags) for kw in keywords_lower):
                continue

            job = Job(
                title=title,
                company=str(post.get("company", "")),
                location="Remote",
                description=str(post.get("description", "") or ""),
                url=str(post.get("url", "")),
                platform="remote_ok",
                is_remote=True,
            )
            jobs.append(job)

            if len(jobs) >= results_wanted:
                break

        self._log(f"{len(jobs)} ilan bulundu")
        return jobs
