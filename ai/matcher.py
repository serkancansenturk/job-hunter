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
Sen kıdemli bir işe alım ve talent danışmanısın. Adayın CV'sini, geçmiş deneyimini, becerilerini,
başarılarını ve sektör geçmişini derinlemesine analiz ederek iş ilanları için uygunluk puanı veriyorsun.

Değerlendirme kriterleri (sadece başlık değil, tam profil analizi):
- Role/Unvan uygunluğu (başlık benzerliği + seniority seviyesi)
- Sektör/Endüstri deneyimi (ilgili şirket veya sektörde çalıştı mı?)
- Teknik/Fonksiyonel beceriler (Salesforce, OKR, CX, Leadership, vb.)
- Ölçülebilir başarılar (P&L, metrikleri yönetebiliyor mu?)
- Ekip yönetimi deneyimi
- Transformasyon/Modernizasyon deneyimi
- Lokasyon/Remote uygunluğu

Skorlama (1-10):
- 9-10: Mükemmel eşleşme — aday tam bu rol için yazılmış gibi
- 7-8: Güçlü eşleşme — geçmiş doğrudan applicable
- 5-6: Orta eşleşme — geçmiş relevant ama gap'ler var
- 3-4: Zayıf eşleşme — bazı beceriler uygun ama role uymaz
- 1-2: Çok zayıf — atlanması öneriliyor

JSON yanıt:
{
  "evaluations": [
    {
      "job_id": "...",
      "score": 8,
      "reason": "Detaylı, konkret nedenler. Hangi geçmiş rol/beceri uygun, hangi deneyim transfer edilebilir",
      "matched_skills": ["skill1", "skill2", "skill3"],
      "relevant_experience": "Hangi geçmiş pozisyon/başarı bu role uygundur",
      "gaps": ["Gap1", "Gap2 (varsa)"],
      "keywords_to_add": ["ATS keyword1", "keyword2"]
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

        # Tüm deneyimi detaylı ekle
        exp_lines = []
        for e in cv["experience"]:
            bullets = " | ".join(e["bullets"][:2])  # İlk 2 başarı
            exp_lines.append(f"• {e['title']} @ {e['company']} ({e['period']}): {bullets}")

        # Tüm beceriler
        all_skills = []
        for category, skills in cv["skills"].items():
            all_skills.extend(skills)

        return f"""
─── ADAY PROFİLİ ───
Ad: {cv['personal']['name']}
Mevcut Unvan: {cv['personal']['title']}

─── ÖZGEÇMIŞ ÖZETI ───
{cv['summary']}

─── TAM DENEYIM GEÇMİŞİ ───
{chr(10).join(exp_lines)}

─── ÖLÇÜLEBİLİR BAŞARILAR ───
{chr(10).join('• ' + m for m in cv['key_metrics'])}

─── TEKNİK BECERİLER & ARAÇLAR ───
{', '.join(sorted(set(all_skills)))}

─── SERTIFIKALAR ───
{', '.join(cv['certifications'])}

─── DILLER ───
{', '.join(f"{l['language']} ({l['level']})" for l in cv['languages'])}

─── SEKTÖRLÜ DENEYİM ───
Finans & Ödeme (Turkish Airlines, Edenred)
Lojistik & Tedarik (CEVA Logistics)
SaaS & E-Ticaret (Akinon)
Seyahat & Teknik (Amadeus)
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

                    # Detaylı reason oluştur
                    matched = ev.get("matched_skills", [])
                    relevant = ev.get("relevant_experience", "")
                    gaps = ev.get("gaps", [])

                    reason_parts = [ev.get("reason", "")]
                    if matched:
                        reason_parts.append(f"✓ Uygun beceriler: {', '.join(matched[:3])}")
                    if relevant:
                        reason_parts.append(f"✓ Deneyim: {relevant}")
                    if gaps:
                        reason_parts.append(f"⚠ Eklenecekler: {', '.join(gaps[:2])}")

                    job.ai_score_reason = " | ".join(reason_parts)
                    job.ai_keywords = ev.get("keywords_to_add", [])

        except Exception as e:
            from rich.console import Console
            Console().print(f"[red]Matcher hatası: {e}[/red]")

        return jobs
