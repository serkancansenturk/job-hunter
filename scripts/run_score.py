"""
Veritabanındaki puanlanmamış ilanları AI ile değerlendirir.
Çalıştır: python scripts/run_score.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from storage.database import Database, init_db
from models.job import JobStatus
from ai.matcher import JobMatcher
from config.settings import load_config

console = Console()


def run_scoring() -> None:
    init_db()
    config = load_config()
    min_score = config["ai"]["match_threshold"]

    # Henüz puanlanmamış ilanları al
    new_jobs = Database.get_jobs(status=JobStatus.NEW)
    if not new_jobs:
        console.print("[yellow]Puanlanacak yeni ilan yok.[/yellow]")
        return

    console.print(f"[cyan]{len(new_jobs)} ilan puanlanacak...[/cyan]")

    matcher = JobMatcher()
    scored_jobs = matcher.score_jobs(new_jobs, batch_size=8)

    high_match = 0
    for job in scored_jobs:
        if job.ai_score is not None:
            Database.update_job_score(
                job.job_id,
                job.ai_score,
                job.ai_score_reason or "",
                job.ai_keywords,
            )
            if job.ai_score >= min_score:
                high_match += 1

    console.print(f"\n[bold green]✓ {len(scored_jobs)} ilan puanlandı — {high_match} yüksek eşleşme (≥{min_score})[/bold green]")


if __name__ == "__main__":
    run_scoring()
