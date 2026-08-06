from abc import ABC, abstractmethod
from models.job import Job


class BaseScraper(ABC):
    name: str = "base"

    @abstractmethod
    def scrape(self, search_terms: list[str], locations: list[str], results_wanted: int) -> list[Job]:
        """İlanları tarar ve Job listesi döner."""
        ...

    def _log(self, msg: str) -> None:
        from rich.console import Console
        Console().print(f"[cyan][{self.name}][/cyan] {msg}")
