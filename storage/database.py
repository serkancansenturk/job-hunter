import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from models.job import Job, JobStatus
from models.application import Application, ApplicationStatus
import json
from datetime import datetime


DB_PATH = Path(__file__).parent.parent / "job_hunter.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id      TEXT UNIQUE NOT NULL,
                title       TEXT NOT NULL,
                company     TEXT NOT NULL,
                location    TEXT DEFAULT '',
                description TEXT DEFAULT '',
                url         TEXT DEFAULT '',
                platform    TEXT DEFAULT '',
                salary_min  REAL,
                salary_max  REAL,
                currency    TEXT DEFAULT 'USD',
                is_remote   INTEGER DEFAULT 0,
                posted_at   TEXT,
                scraped_at  TEXT NOT NULL,
                ai_score    REAL,
                ai_score_reason TEXT,
                ai_keywords TEXT DEFAULT '[]',
                status      TEXT DEFAULT 'new'
            );

            CREATE TABLE IF NOT EXISTS applications (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id          TEXT NOT NULL,
                status          TEXT DEFAULT 'pending',
                cv_version_path TEXT,
                cover_letter    TEXT,
                applied_at      TEXT,
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL,
                notes           TEXT DEFAULT '',
                rejection_reason TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id)
            );
        """)


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


class Database:
    @staticmethod
    def upsert_job(job: Job) -> Job:
        with get_db() as conn:
            conn.execute("""
                INSERT INTO jobs (job_id, title, company, location, description, url,
                    platform, salary_min, salary_max, currency, is_remote, posted_at,
                    scraped_at, ai_score, ai_score_reason, ai_keywords, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                    scraped_at = excluded.scraped_at,
                    ai_score   = COALESCE(excluded.ai_score, jobs.ai_score),
                    ai_score_reason = COALESCE(excluded.ai_score_reason, jobs.ai_score_reason),
                    ai_keywords = COALESCE(excluded.ai_keywords, jobs.ai_keywords),
                    status     = CASE WHEN jobs.status = 'new' THEN excluded.status ELSE jobs.status END
            """, (
                job.job_id, job.title, job.company, job.location, job.description,
                job.url, job.platform, job.salary_min, job.salary_max, job.currency,
                int(job.is_remote), job.posted_at.isoformat() if job.posted_at else None,
                job.scraped_at.isoformat(), job.ai_score, job.ai_score_reason,
                json.dumps(job.ai_keywords), job.status.value,
            ))
        return job

    @staticmethod
    def get_jobs(status=None, min_score: float = 0):
        with get_db() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM jobs WHERE status = ? AND (ai_score IS NULL OR ai_score >= ?) ORDER BY scraped_at DESC",
                    (status.value, min_score),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM jobs WHERE ai_score IS NULL OR ai_score >= ? ORDER BY scraped_at DESC",
                    (min_score,),
                ).fetchall()
            return [_row_to_job(r) for r in rows]

    @staticmethod
    def update_job_score(job_id: str, score: float, reason: str, keywords: list[str]) -> None:
        with get_db() as conn:
            conn.execute(
                "UPDATE jobs SET ai_score = ?, ai_score_reason = ?, ai_keywords = ?, status = 'scored' WHERE job_id = ?",
                (score, reason, json.dumps(keywords), job_id),
            )

    @staticmethod
    def update_job_status(job_id: str, status: JobStatus) -> None:
        with get_db() as conn:
            conn.execute("UPDATE jobs SET status = ? WHERE job_id = ?", (status.value, job_id))

    @staticmethod
    def save_application(app: Application) -> Application:
        now = datetime.utcnow().isoformat()
        with get_db() as conn:
            cursor = conn.execute("""
                INSERT INTO applications (job_id, status, cv_version_path, cover_letter,
                    applied_at, created_at, updated_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                app.job_id, app.status.value, app.cv_version_path, app.cover_letter,
                app.applied_at.isoformat() if app.applied_at else None,
                now, now, app.notes,
            ))
            app.id = cursor.lastrowid
        return app

    @staticmethod
    def get_applications(status=None):
        with get_db() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM applications WHERE status = ? ORDER BY created_at DESC",
                    (status.value,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM applications ORDER BY created_at DESC"
                ).fetchall()
            return [_row_to_application(r) for r in rows]

    @staticmethod
    def get_stats() -> dict:
        with get_db() as conn:
            total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            scored = conn.execute("SELECT COUNT(*) FROM jobs WHERE ai_score IS NOT NULL").fetchone()[0]
            high_match = conn.execute("SELECT COUNT(*) FROM jobs WHERE ai_score >= 7").fetchone()[0]
            applied = conn.execute("SELECT COUNT(*) FROM applications WHERE status = 'submitted'").fetchone()[0]
            return {
                "total_jobs": total,
                "scored_jobs": scored,
                "high_match": high_match,
                "applied": applied,
            }


def _row_to_job(row: sqlite3.Row) -> Job:
    d = dict(row)
    d["is_remote"] = bool(d["is_remote"])
    d["ai_keywords"] = json.loads(d.get("ai_keywords") or "[]")
    d["status"] = JobStatus(d["status"])
    for field in ("posted_at", "scraped_at"):
        if d[field]:
            d[field] = datetime.fromisoformat(d[field])
    return Job(**d)


def _row_to_application(row: sqlite3.Row) -> Application:
    d = dict(row)
    d["status"] = ApplicationStatus(d["status"])
    for field in ("applied_at", "created_at", "updated_at"):
        if d[field]:
            d[field] = datetime.fromisoformat(d[field])
    return Application(**d)
