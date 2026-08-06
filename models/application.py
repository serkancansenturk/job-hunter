from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ApplicationStatus(str, Enum):
    PENDING = "pending"         # Onay bekliyor
    APPROVED = "approved"       # Kullanıcı onayladı
    SUBMITTED = "submitted"     # Başvuru gönderildi
    FAILED = "failed"           # Otomasyon başarısız
    INTERVIEW = "interview"     # Mülakat davetı
    OFFER = "offer"             # Teklif
    REJECTED = "rejected"       # Red
    WITHDRAWN = "withdrawn"     # Geri çekildi


class Application(BaseModel):
    id: Optional[int] = None
    job_id: str
    status: ApplicationStatus = ApplicationStatus.PENDING

    # Generated documents
    cv_version_path: Optional[str] = None      # Tailored CV dosya yolu
    cover_letter: Optional[str] = None

    # Tracking
    applied_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Notes
    notes: str = ""
    rejection_reason: Optional[str] = None
