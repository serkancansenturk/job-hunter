"""
Job Hunter — Streamlit Dashboard
Çalıştır: streamlit run dashboard/app.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from datetime import datetime

from storage.database import Database, init_db
from models.job import Job, JobStatus
from models.application import Application, ApplicationStatus
from models.cv import TailoredCV

st.set_page_config(
    page_title="Job Hunter — Serkan",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# ── Modern Stil ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Ana layout */
.main { background: linear-gradient(135deg, #0f172a 0%, #1a1f3a 100%); }

/* İlan Card */
.job-card {
    background: linear-gradient(135deg, #1e293b 0%, #162035 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 20px;
    margin: 12px 0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    transition: all 0.3s ease;
}
.job-card:hover {
    border-color: #3b82f6;
    box-shadow: 0 8px 20px rgba(59,130,246,0.15);
    transform: translateY(-2px);
}

/* Score Badge */
.score-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    font-size: 24px;
    font-weight: 800;
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
}
.score-badge.high { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
.score-badge.mid { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
.score-badge.low { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }

/* Başlık & Metin */
.job-title {
    font-size: 20px;
    font-weight: 700;
    color: #f1f5f9;
    margin-bottom: 4px;
}
.company-name {
    font-size: 14px;
    color: #cbd5e1;
    font-weight: 500;
}
.match-reason {
    background: rgba(16, 185, 129, 0.1);
    border-left: 3px solid #10b981;
    padding: 12px;
    border-radius: 6px;
    margin: 12px 0;
    font-size: 13px;
    color: #d1fae5;
}

/* Info badges */
.info-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    margin: 2px 4px;
}
.badge-platform { background: rgba(59, 130, 246, 0.2); color: #93c5fd; }
.badge-remote { background: rgba(34, 197, 94, 0.2); color: #86efac; }
.badge-location { background: rgba(168, 85, 247, 0.2); color: #d8b4fe; }

/* Buttons */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    padding: 10px 20px;
    transition: all 0.2s;
}

/* Metrics */
.metric-container { background: #1e293b; border-radius: 10px; padding: 16px; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.shields.io/badge/Job_Hunter-v1.0-3b82f6?style=flat-square", width=150)
    st.title("🎯 Job Hunter")
    st.caption("Powered by Claude AI")
    st.divider()

    page = st.radio(
        "Sayfa",
        ["📊 Dashboard", "🔍 İlanlar", "📝 Başvurular", "📄 CV Önizleme"],
        label_visibility="collapsed",
    )

    st.divider()

    col_scan, col_score = st.columns(2)
    with col_scan:
        if st.button("🔄 Yeni Tarama Başlat", use_container_width=True, type="primary"):
            with st.spinner("İlanlar taranıyor..."):
                try:
                    from scripts.run_scrape import run_full_scrape
                    run_full_scrape()
                    st.success("Tarama tamamlandı!")
                except Exception as e:
                    st.error(f"Tarama hatası: {e}")

    with col_score:
        if st.button("🤖 İlanları Puanla", use_container_width=True):
            with st.spinner("AI değerlendiriyor..."):
                try:
                    from scripts.run_score import run_scoring
                    run_scoring()
                    st.success("Puanlama tamamlandı!")
                except Exception as e:
                    st.error(f"Puanlama hatası: {e}")


# ── Dashboard ─────────────────────────────────────────────────────────────────
if page == "📊 Dashboard":
    st.header("📊 Genel Bakış")

    stats = Database.get_stats()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Toplam İlan", stats["total_jobs"])
    with col2:
        st.metric("Puanlanmış", stats["scored_jobs"])
    with col3:
        st.metric("Yüksek Eşleşme (≥7)", stats["high_match"])
    with col4:
        st.metric("Başvurulan", stats["applied"])

    st.divider()

    # Son yüksek eşleşmeler
    st.subheader("🌟 En İyi Eşleşmeler")
    jobs = Database.get_jobs(min_score=7)
    if jobs:
        df = pd.DataFrame([
            {
                "Puan": j.ai_score,
                "Pozisyon": j.title,
                "Şirket": j.company,
                "Lokasyon": j.location,
                "Platform": j.platform,
                "Durum": j.status.value,
                "URL": j.url,
            }
            for j in jobs[:10]
        ])
        st.dataframe(
            df.drop("URL", axis=1),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Puan": st.column_config.ProgressColumn("Puan", min_value=0, max_value=10, format="%.1f"),
            },
        )
    else:
        st.info("Henüz yüksek eşleşme bulunamadı. Tarama başlatın.")

elif page == "🔍 İlanlar":
    st.header("🔍 İş İlanları")

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        platform_filter = st.multiselect(
            "Platform",
            ["linkedin", "indeed", "glassdoor", "remote_ok", "kariyer", "bayt"],
            default=[],
        )
    with col2:
        status_filter = st.selectbox(
            "Durum",
            ["Tümü", "new", "scored", "approved", "rejected", "applied"],
        )
    with col3:
        min_score = st.slider("Min. Puan", 0.0, 10.0, 0.0, 0.5)

    status_enum = None if status_filter == "Tümü" else JobStatus(status_filter)
    all_jobs = Database.get_jobs(status=status_enum, min_score=min_score)

    if platform_filter:
        all_jobs = [j for j in all_jobs if j.platform in platform_filter]

    st.caption(f"{len(all_jobs)} ilan gösteriliyor")

    for job in all_jobs:
        score = job.ai_score or 0
        score_level = "high" if score >= 7 else "mid" if score >= 5 else "low"

        st.markdown(f"""
        <div class="job-card">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 16px;">
                <div style="flex: 1;">
                    <div class="job-title">{job.title}</div>
                    <div class="company-name">{job.company}</div>
                </div>
                <div style="text-align: center;">
                    <div class="score-badge {score_level}">{score:.1f}</div>
                    <div style="font-size: 11px; color: #94a3b8; margin-top: 4px;">Uygunluk</div>
                </div>
            </div>

            <div style="display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap;">
                <span class="info-badge badge-location">📍 {job.location}</span>
                <span class="info-badge badge-platform">{job.platform}</span>
                {'<span class="info-badge badge-remote">🌐 Remote</span>' if job.is_remote else ''}
                <span class="info-badge" style="background: rgba(100, 116, 139, 0.2); color: #cbd5e1;">
                    📅 {job.scraped_at.strftime('%d.%m.%Y') if job.scraped_at else '—'}
                </span>
            </div>

            {'<div class="match-reason">' + (job.ai_score_reason.split(' | ')[0] if job.ai_score_reason else '') + '</div>' if job.ai_score_reason else ''}
        </div>
        """, unsafe_allow_html=True)

        # Detayları accordion'da göster
        with st.expander("📋 Detaylar & Başvuru"):
            col1, col2 = st.columns([2, 1])

            with col1:
                if job.ai_score_reason:
                    parts = job.ai_score_reason.split(" | ")
                    if len(parts) > 1:
                        st.markdown("**🎯 Eşleşme Detayları:**")
                        for detail in parts[1:]:
                            st.caption(detail)

                if job.ai_keywords:
                    st.markdown("**📌 ATS İçin Eklenecekler:**")
                    st.caption(", ".join(job.ai_keywords[:4]))

                if job.description:
                    st.markdown("**📄 İlan Açıklaması:**")
                    st.caption(job.description[:500] + "..." if len(job.description) > 500 else job.description)

            with col1:
                if job.url:
                    st.markdown(f"[🔗 İlana Git]({job.url})")

            with col2:
                st.markdown("**Aksiyon:**")
                if st.button("✅ Hazırla", key=f"approve_{job.job_id}", use_container_width=True):
                    with st.spinner(f"Hazırlanıyor..."):
                        try:
                            from ai.cv_tailor import CVTailor
                            from ai.cover_letter import CoverLetterGenerator
                            from ai.exporter import CVExporter

                            tailor = CVTailor()
                            tailored_cv = tailor.tailor(job)

                            gen = CoverLetterGenerator()
                            cover_letter_text = gen.generate(job, tailored_cv)
                            tailored_cv.cover_letter = cover_letter_text

                            exporter = CVExporter()
                            docx_path = exporter.export_docx(tailored_cv)

                            app = Application(
                                job_id=job.job_id,
                                status=ApplicationStatus.APPROVED,
                                cv_version_path=docx_path,
                                cover_letter=cover_letter_text,
                            )
                            Database.save_application(app)
                            Database.update_job_status(job.job_id, JobStatus.APPROVED)

                            st.success("✅ CV + Cover Letter hazırlandı!")
                            st.info(f"📂 Dosya kaydedildi")
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ {str(e)[:100]}")

                if st.button("❌ Reddet", key=f"reject_{job.job_id}", use_container_width=True):
                    Database.update_job_status(job.job_id, JobStatus.REJECTED)
                    st.rerun()

elif page == "📝 Başvurular":
    st.header("📝 Başvuru Takibi")

    apps = Database.get_applications()
    jobs_map = {j.job_id: j for j in Database.get_jobs()}

    if not apps:
        st.info("Henüz başvuru yok. İlanlar sayfasından onaylayın.")
    else:
        for app in apps:
            job = jobs_map.get(app.job_id)
            title = f"{job.title} @ {job.company}" if job else app.job_id

            with st.expander(f"{title} — {app.status.value.upper()}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Oluşturulma:** {app.created_at.strftime('%d.%m.%Y %H:%M') if app.created_at else '—'}")
                    st.write(f"**Başvuru tarihi:** {app.applied_at.strftime('%d.%m.%Y') if app.applied_at else '—'}")
                    if app.cv_version_path:
                        st.write(f"**CV:** `{Path(app.cv_version_path).name}`")

                with col2:
                    new_status = st.selectbox(
                        "Durum Güncelle",
                        [s.value for s in ApplicationStatus],
                        index=[s.value for s in ApplicationStatus].index(app.status.value),
                        key=f"status_{app.id}",
                    )
                    if st.button("Güncelle", key=f"update_{app.id}"):
                        # TODO: update application status in DB
                        st.success("Güncellendi")

                if app.cover_letter:
                    with st.popover("Kapak Mektubu"):
                        st.write(app.cover_letter)


# ── CV Önizleme ───────────────────────────────────────────────────────────────
elif page == "📄 CV Önizleme":
    st.header("📄 Base CV")

    from config.cv_base import CV_DATA
    cv = CV_DATA

    st.subheader(cv["personal"]["name"])
    st.caption(cv["personal"]["title"])

    st.divider()
    st.markdown("### Professional Summary")
    st.write(cv["summary"])

    st.divider()
    st.markdown("### Key Metrics")
    for m in cv["key_metrics"]:
        st.markdown(f"- {m}")

    st.divider()
    st.markdown("### Experience")
    for exp in cv["experience"]:
        st.markdown(f"**{exp['title']}** — *{exp['company']}* ({exp['period']})")
        for b in exp["bullets"]:
            st.markdown(f"  - {b}")
        st.write("")

    st.divider()
    st.markdown("### Certifications")
    for cert in cv["certifications"]:
        st.markdown(f"- {cert}")
