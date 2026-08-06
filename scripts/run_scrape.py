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
from scrapers import (
    RemoteOKScraper,
    KariyerScraper,
    BaytScraper,
    RemoteCoScraper,
    WeWorkRemoteScraper,
    LinkedInRSSScraper,
    StepStoneScraper,
    ReedScraper,
    EURESScraper,
)
from config.settings import load_config

console = Console()


def run_full_scrape() -> int:
    init_db()
    config = load_config()

    search_terms = config["search"]["job_titles"]
    locations = config["search"]["locations"]
    platforms_cfg = config["search"]["platforms"]

    all_jobs = []

    # MVP Platforms
    scrapers = [
        ("remote_ok", RemoteOKScraper()),
        ("kariyer_net", KariyerScraper()),
        ("bayt", BaytScraper()),
        ("remote.co", RemoteCoScraper()),
        ("weworkremotely", WeWorkRemoteScraper()),
        ("linkedin_rss", LinkedInRSSScraper()),
    ]

    # Tier 2 Platforms
    scrapers.extend([
        ("stepstone", StepStoneScraper()),
        ("reed", ReedScraper()),
        ("eures", EURESScraper()),
    ])

    for platform_name, scraper in scrapers:
        if not platforms_cfg.get(platform_name, {}).get("enabled", True):
            continue

        console.rule(f"[cyan]{scraper.name.upper()}")

        try:
            jobs = scraper.scrape(
                search_terms=search_terms[:2],
                locations=locations[:2],
                results_wanted=platforms_cfg.get(platform_name, {}).get("results_wanted", 20),
            )
            all_jobs.extend(jobs)
        except Exception as e:
            console.print(f"[red]{scraper.name} hatası: {e}[/red]")

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
