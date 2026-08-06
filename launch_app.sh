#!/bin/bash
cd "/Users/serkansenturk/Claude Code/job-hunter"
STREAMLIT_SERVER_HEADLESS=true python3 -m streamlit run dashboard/app.py --logger.level=error 2>/dev/null &
sleep 3
open http://localhost:8501
