"""
Her ilan için 1-10 uygunluk skoru üretir.
Toplu işlem: birden fazla ilanı tek API çağrısında değerlendirir.
"""
import json
import anthropic
from config.settings import get_settings
from config.cv_base import CV_DATA
from models.job import Job


SYSTEM_PROMPT = """
Sen bir kıdemli işe alım uzmanısın. Sana bir aday profili ve iş ilanları verilecek.
Her ilan için 1-10 arası uygunluk skoru ver.

Skorlama kriterleri:
- 9-10: Çok güçlü eşleşme, başvurulmalı
- 7-8: İyi eşleşme, başvurulabilir
- 5-6: Kısmi eşleşme, revize ile uygun olabilir
- 1-4: Zayıf eşleşme, atla

JSON formatında yanıt ver:
{
  "evaluations": [
    {
      "job_id": "...",
      "score": 8,
      "reason": "...",
      "missing_keywords": ["keyword1", "keyword2"]
    }
  ]
}
"""


class JobMatcher:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=get_settings().anthropic_api_key)
        self._cv_summary = self._build_cv_summary()

    def _build_cv_summary(self) -> str:
        cv = CV_DATA
        exp_lines = []
        for e in cv["experience"][:4]:  # Son 4 pozisyon yeterli
            exp_lines.append(f"- {e['title']} @ {e['company']} ({e['period']})")

        return f"""
Aday: {cv['personal']['name']}
Başlık: {cv['personal']['title']}

Deneyim:
{chr(10).join(exp_lines)}

Temel başarılar:
{chr(10).join('- ' + m for m in cv['key_metrics'][:5])}

Sertifikalar: {', '.join(cv['certifications'][:5])}

Beceriler: Product Strategy, CRM (Salesforce), Digital Transformation,
OKR Management, Data-driven Decision-making, Cross-functional Leadership,
Customer Experience, Agile/Scrum, PRINCE2, Business Analysis
"""

    def score_jobs(self, jobs: list[Job], batch_size: int = 10) -> list[Job]:
        """İlanları batch'ler halinde puanlar ve günceller."""
        results = []
        for i in range(0, len(jobs), batch_size):
            batch = jobs[i:i + batch_size]
            scored = self._score_batch(batch)
            results.extend(scored)
        return results

    def _score_batch(self, jobs: list[Job]) -> list[Job]:
        jobs_text = json.dumps([
            {
                "job_id": j.job_id,
                "title": j.title,
                "company": j.company,
                "location": j.location,
                "description": j.description[:1500] if j.description else "",
            }
            for j in jobs
        ], ensure_ascii=False)

        prompt = f"""
Aday Profili:
{self._cv_summary}

Değerlendirilecek ilanlar:
{jobs_text}

Her ilan için JSON formatında uygunluk değerlendirmesi yap.
"""
        try:
            msg = self.client.messages.create(
                model="claude-opus-4-5",
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            content = msg.content[0].text

            # JSON bloğunu çıkar
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            data = json.loads(content.strip())
            score_map = {e["job_id"]: e for e in data.get("evaluations", [])}

            for job in jobs:
                if job.job_id in score_map:
                    ev = score_map[job.job_id]
                    job.ai_score = float(ev.get("score", 0))
                    job.ai_score_reason = ev.get("reason", "")
                    job.ai_keywords = ev.get("missing_keywords", [])

        except Exception as e:
            from rich.console import Console
            Console().print(f"[red]Matcher hatası: {e}[/red]")

        return jobs
