#!/bin/bash
cd "/Users/serkansenturk/Claude Code/job-hunter"
/usr/bin/python3 scripts/run_scrape.py >> /tmp/job_hunter.log 2>&1
/usr/bin/python3 scripts/run_score.py >> /tmp/job_hunter.log 2>&1
echo "[$(date)] Scan & score completed" >> /tmp/job_hunter.log
