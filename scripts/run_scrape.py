"""
Tüm platformları tarar ve sonuçları veritabanına kaydeder.
Çalıştır: python scripts/run_scrape.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.progress import track
from storage.database import Database, init_db
from scrapers import JobSpyScraper, RemoteOKScraper, KariyerScraper, BaytScraper
from config.settings import load_config

console = Console()


def run_full_scrape() -> int:
    init_db()
    config = load_config()

    search_terms = config["search"]["job_titles"]
    locations = config["search"]["locations"]
    platforms_cfg = config["search"]["platforms"]

    all_jobs = []

    # JobSpy: LinkedIn + Indeed + Glassdoor
    if platforms_cfg.get("linkedin", {}).get("enabled"):
        console.rule("[cyan]JobSpy (LinkedIn + Indeed + Glassdoor)")
        scraper = JobSpyScraper(platforms=["linkedin", "indeed", "glassdoor"])
        jobs = scraper.scrape(
            search_terms=search_terms[:4],  # İlk 4 terim yeterli
            locations=locations[:3],
            results_wanted=platforms_cfg["linkedin"].get("results_wanted", 30),
        )
        all_jobs.extend(jobs)

    # Remote OK
    if platforms_cfg.get("remote_ok", {}).get("enabled"):
        console.rule("[cyan]Remote OK")
        scraper = RemoteOKScraper()
        jobs = scraper.scrape(
            search_terms=search_terms,
            locations=[],
            results_wanted=platforms_cfg["remote_ok"].get("results_wanted", 20),
        )
        all_jobs.extend(jobs)

    # Kariyer.net
    if platforms_cfg.get("kariyer_net", {}).get("enabled"):
        console.rule("[cyan]Kariyer.net")
        scraper = KariyerScraper()
        jobs = scraper.scrape(
            search_terms=search_terms[:3],
            locations=["İstanbul"],
            results_wanted=platforms_cfg["kariyer_net"].get("results_wanted", 20),
        )
        all_jobs.extend(jobs)

    # Bayt.com
    if platforms_cfg.get("bayt", {}).get("enabled"):
        console.rule("[cyan]Bayt.com")
        scraper = BaytScraper()
        jobs = scraper.scrape(
            search_terms=search_terms[:3],
            locations=["UAE", "Saudi Arabia", "Qatar"],
            results_wanted=platforms_cfg["bayt"].get("results_wanted", 20),
        )
        all_jobs.extend(jobs)

    # Kaydet
    console.rule("[green]Veritabanına kaydediliyor")
    saved = 0
    for job in track(all_jobs, description="Kaydediliyor..."):
        Database.upsert_job(job)
        saved += 1

    console.print(f"\n[bold green]✓ {saved} ilan kaydedildi[/bold green]")
    return saved


if __name__ == "__main__":
    run_full_scrape()
