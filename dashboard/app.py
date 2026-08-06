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

# ── Stil ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.metric-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 16px 20px;
    text-align: center;
}
.score-high { color: #10b981; font-weight: 700; }
.score-mid  { color: #f59e0b; font-weight: 700; }
.score-low  { color: #ef4444; font-weight: 700; }
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
}
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

    if st.button("🔄 Yeni Tarama Başlat", use_container_width=True, type="primary"):
        with st.spinner("İlanlar taranıyor..."):
            try:
                from scripts.run_scrape import run_full_scrape
                run_full_scrape()
                st.success("Tarama tamamlandı!")
            except Exception as e:
                st.error(f"Tarama hatası: {e}")

    if st.button("🤖 Seçili İlanları Puanla", use_container_width=True):
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
        score_class = "score-high" if score >= 7 else "score-mid" if score >= 5 else "score-low"

        with st.expander(f"{'⭐' if score >= 7 else '·'} {job.title} — {job.company} ({job.location})", expanded=False):
            col_a, col_b = st.columns([3, 1])

            with col_a:
                st.write(f"**Platform:** {job.platform} &nbsp;·&nbsp; **Tarih:** {job.scraped_at.strftime('%d.%m.%Y') if job.scraped_at else '—'}")
                if job.url:
                    st.write(f"🔗 [İlana Git]({job.url})")
                if job.ai_score_reason:
                    st.info(f"🤖 AI Değerlendirmesi: {job.ai_score_reason}")
                if job.ai_keywords:
                    st.warning(f"📌 Eklenecek anahtar kelimeler: {', '.join(job.ai_keywords)}")
                if job.description:
                    with st.popover("İlan Açıklaması"):
                        st.write(job.description[:2000])

            with col_b:
                st.markdown(f"<p style='font-size:32px; text-align:center' class='{score_class}'>{score:.1f}</p>", unsafe_allow_html=True)
                st.caption("AI Puanı")

                if st.button("✅ Onayla", key=f"approve_{job.job_id}", use_container_width=True):
                    _prepare_and_approve(job)
                    st.rerun()

                if st.button("❌ Reddet", key=f"reject_{job.job_id}", use_container_width=True):
                    Database.update_job_status(job.job_id, JobStatus.REJECTED)
                    st.rerun()


# ── Başvurular ────────────────────────────────────────────────────────────────
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
