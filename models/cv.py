from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TailoredCV(BaseModel):
    job_id: str
    job_title: str
    company: str

    # AI-tailored content
    summary: str
    highlighted_bullets: dict[str, list[str]]   # {company: [selected bullets]}
    added_keywords: list[str] = Field(default_factory=list)
    ats_score: Optional[float] = None
    cover_letter: str = ""

    # File paths
    docx_path: Optional[str] = None
    pdf_path: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
