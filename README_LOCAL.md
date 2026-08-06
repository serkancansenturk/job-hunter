# Job Hunter — Local Setup

## Hızlı Başlangıç

### 1. Kurulum (bir kez)
```bash
cd "/Users/serkansenturk/Claude Code/job-hunter"
pip3 install -r requirements.txt
playwright install chromium
```

### 2. API Key Ekle
`.env` dosyasını aç:
```
ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE
```

### 3. Dashboard Başlat
```bash
python3 -m streamlit run dashboard/app.py
```
→ Browser açılır: `http://localhost:8501`

---

## Otomatik Tarama (Crontab)

Her gün 08:00'de otomatik tarama ve puanlama:

```bash
crontab -l  # Kontrol et
```

Kuruluysa, bitti. Değilse:
```bash
crontab -e
# Şunu ekle:
# 0 8 * * * /Users/serkansenturk/Claude\ Code/job-hunter/scripts/auto_scrape_and_score.sh
```

---

## Masaüstü Launcher

Desktop'ta **Job Hunter.app** ikonuna tıkla → Dashboard açılır.

---

## Log & Troubleshooting

Tarama log'u:
```bash
tail -50 /tmp/job_hunter.log
```

---

**That's it!** Günde 08:00'de otomatik tarama, ihtiyaç duyarsan manuel de çalıştırabilirsin.
