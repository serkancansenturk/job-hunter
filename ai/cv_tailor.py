"""
İlana özel CV üretir:
- Summary'yi pozisyona göre yeniden yazar
- En uygun deneyim bullet'larını seçer ve güçlendirir
- Eksik ATS anahtar kelimelerini organik biçimde ekler
"""
import json
import anthropic
from config.settings import get_settings
from config.cv_base import CV_DATA
from models.job import Job
from models.cv import TailoredCV


SYSTEM_PROMPT = """
Sen kıdemli bir CV yazarı ve ATS uzmanısın.
Görevin: verilen iş ilanına göre bir CV'yi özelleştirmek.

Kurallar:
1. Tüm bilgiler doğru olmalı — hiçbir şey uydurma
2. Anahtar kelimeleri ORGANIK biçimde ekle, keyword stuffing yapma
3. Bullet'lar güçlü fiille başlamalı (Led, Delivered, Achieved, Drove...)
4. Summary 3-4 cümle, ilan pozisyonuna özel
5. En alakalı 4-5 bullet'ı öne çıkar, zayıf olanları kaldır
6. Çıktı JSON formatında olmalı
"""

TAILOR_TEMPLATE = """
İş İlanı:
Pozisyon: {title}
Şirket: {company}
Açıklama:
{description}

Eksik ATS anahtar kelimeleri: {keywords}

Aday'ın orijinal CV verisi:
{cv_json}

Lütfen şu formatta JSON döndür:
{{
  "summary": "...(3-4 cümle, pozisyona özel)...",
  "experience": [
    {{
      "company": "Edenred",
      "selected_bullets": ["bullet1", "bullet2", "bullet3"]
    }},
    ...
  ],
  "added_keywords": ["keyword1", "keyword2"],
  "ats_score": 8.5
}}
"""


class CVTailor:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=get_settings().anthropic_api_key)

    def tailor(self, job: Job) -> TailoredCV:
        cv_snapshot = {
            "summary": CV_DATA["summary"],
            "key_metrics": CV_DATA["key_metrics"],
            "skills": CV_DATA["skills"],
            "experience": [
                {
                    "title": e["title"],
                    "company": e["company"],
                    "period": e["period"],
                    "bullets": e["bullets"],
                }
                for e in CV_DATA["experience"]
            ],
        }

        prompt = TAILOR_TEMPLATE.format(
            title=job.title,
            company=job.company,
            description=(job.description or "")[:2000],
            keywords=", ".join(job.ai_keywords or []),
            cv_json=json.dumps(cv_snapshot, ensure_ascii=False, indent=2),
        )

        try:
            msg = self.client.messages.create(
                model="claude-opus-4-5",
                max_tokens=4000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            content = msg.content[0].text

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            data = json.loads(content.strip())

            highlighted = {
                item["company"]: item["selected_bullets"]
                for item in data.get("experience", [])
            }

            return TailoredCV(
                job_id=job.job_id,
                job_title=job.title,
                company=job.company,
                summary=data.get("summary", CV_DATA["summary"]),
                highlighted_bullets=highlighted,
                added_keywords=data.get("added_keywords", []),
                ats_score=data.get("ats_score"),
            )

        except Exception as e:
            from rich.console import Console
            Console().print(f"[red]CV tailor hatası: {e}[/red]")
            # Fallback: orijinal CV
            return TailoredCV(
                job_id=job.job_id,
                job_title=job.title,
                company=job.company,
                summary=CV_DATA["summary"],
                highlighted_bullets={
                    e["company"]: e["bullets"][:3]
                    for e in CV_DATA["experience"]
                },
            )
