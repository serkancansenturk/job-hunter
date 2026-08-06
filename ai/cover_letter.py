"""
İlana ve şirkete özel kapak mektubu üretir.
"""
import anthropic
from config.settings import get_settings
from config.cv_base import CV_DATA
from models.job import Job
from models.cv import TailoredCV


SYSTEM_PROMPT = """
Sen deneyimli bir kariyer koçusun. Profesyonel ama samimi, güçlü kapak mektupları yazıyorsun.

Kurallar:
- 3-4 paragraf, maksimum 350 kelime
- İlk paragrafta pozisyon ve neden bu şirkete ilgi duyulduğu
- İkinci paragrafta en güçlü 2-3 başarı (ölçülebilir metriklerle)
- Üçüncü paragrafta kültürel uyum ve değer önerisi
- Kapanış paragrafı - mülakata davet
- Keyword stuffing yapma, akıcı ve özgün yaz
- İngilizce yaz
"""


class CoverLetterGenerator:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=get_settings().anthropic_api_key)

    def generate(self, job: Job, tailored_cv: TailoredCV) -> str:
        cv = CV_DATA
        key_metrics = "\n".join(f"- {m}" for m in cv["key_metrics"][:5])
        certs = ", ".join(cv["certifications"][:3])

        prompt = f"""
Aşağıdaki bilgilere dayanarak kapak mektubu yaz:

Pozisyon: {job.title}
Şirket: {job.company}
Lokasyon: {job.location}

İlan açıklaması:
{(job.description or '')[:1500]}

Aday bilgileri:
- İsim: {cv['personal']['name']}
- Mevcut pozisyon: {cv['experience'][0]['title']} @ {cv['experience'][0]['company']}
- Deneyim: 15+ yıl (Product, CRM, Digital Transformation)
- Öne çıkan başarılar:
{key_metrics}
- Sertifikalar: {certs}

Özelleştirilmiş CV özeti: {tailored_cv.summary}

Profesyonel, insan sesi taşıyan, güçlü bir kapak mektubu yaz.
"""
        try:
            msg = self.client.messages.create(
                model="claude-opus-4-5",
                max_tokens=1500,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        except Exception as e:
            from rich.console import Console
            Console().print(f"[red]Cover letter hatası: {e}[/red]")
            return ""
