"""
Job Hunter — CLI giriş noktası
Kullanım:
  python main.py scrape          # İlanları tara
  python main.py score           # AI ile puanla
  python main.py dashboard       # Web arayüzünü başlat
  python main.py run             # Tara + puanla + dashboard
"""
import sys
import subprocess
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(help="Job Hunter — AI destekli iş başvuru asistanı")
console = Console()


@app.command()
def scrape():
    """Tüm platformları tara, ilanları veritabanına kaydet."""
    from scripts.run_scrape import run_full_scrape
    run_full_scrape()


@app.command()
def score():
    """Veritabanındaki yeni ilanları AI ile puanla."""
    from scripts.run_score import run_scoring
    run_scoring()


@app.command()
def dashboard():
    """Streamlit dashboard'ı başlat."""
    dash_path = Path(__file__).parent / "dashboard" / "app.py"
    console.print("[cyan]Dashboard başlatılıyor → http://localhost:8501[/cyan]")
    subprocess.run(["streamlit", "run", str(dash_path)])


@app.command()
def run():
    """Tam iş akışı: tara → puanla → dashboard."""
    from scripts.run_scrape import run_full_scrape
    from scripts.run_score import run_scoring

    console.rule("[cyan]1/3 — Tarama")
    run_full_scrape()

    console.rule("[cyan]2/3 — Puanlama")
    run_scoring()

    console.rule("[cyan]3/3 — Dashboard")
    dashboard()


if __name__ == "__main__":
    app()
