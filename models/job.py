from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import hashlib


class JobStatus(str, Enum):
    NEW = "new"
    SCORED = "scored"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    INTERVIEW = "interview"
    OFFER = "offer"
    CLOSED = "closed"


class Job(BaseModel):
    id: Optional[int] = None
    job_id: str = ""            # Platform-specific ID or hash
    title: str
    company: str
    location: str = ""
    description: str = ""
    url: str = ""
    platform: str = ""          # linkedin, indeed, remote_ok, kariyer, bayt...
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: str = "USD"
    is_remote: bool = False
    posted_at: Optional[datetime] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    # AI-generated fields
    ai_score: Optional[float] = None        # 1-10 uygunluk skoru
    ai_score_reason: Optional[str] = None
    ai_keywords: list[str] = Field(default_factory=list)  # CV'de eksik anahtar kelimeler

    status: JobStatus = JobStatus.NEW

    def compute_job_id(self) -> str:
        raw = f"{self.platform}:{self.company}:{self.title}:{self.url}"
        return hashlib.md5(raw.encode()).hexdigest()

    def model_post_init(self, __context) -> None:
        if not self.job_id:
            self.job_id = self.compute_job_id()
