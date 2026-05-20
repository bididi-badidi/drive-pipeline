"""
pipeline/queue.py — SQLite-backed job queue.

Schema
------
jobs(id, filename, source_path, source_type, status, error, created_at, updated_at)

Statuses: pending → processing → done | failed
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import config


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.SQLITE_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the jobs table if it doesn't exist."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                filename    TEXT NOT NULL,
                source_path TEXT NOT NULL,
                source_type TEXT,
                status      TEXT DEFAULT 'pending',
                error       TEXT,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            )
        """)


def enqueue(filename: str, source_path: Path, source_type: str | None = None) -> int:
    """Insert a new pending job. Returns the new job id."""
    now = _now()
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO jobs (filename, source_path, source_type, status, created_at, updated_at)
            VALUES (?, ?, ?, 'pending', ?, ?)
            """,
            (filename, str(source_path), source_type, now, now),
        )
        return cur.lastrowid  # type: ignore[return-value]


def claim_pending() -> sqlite3.Row | None:
    """Atomically claim the oldest pending job and set it to 'processing'."""
    now = _now()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM jobs WHERE status = 'pending' ORDER BY id LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        conn.execute(
            "UPDATE jobs SET status = 'processing', updated_at = ? WHERE id = ?",
            (now, row["id"]),
        )
        return row


def mark_done(job_id: int) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE jobs SET status = 'done', updated_at = ? WHERE id = ?",
            (_now(), job_id),
        )


def mark_failed(job_id: int, error: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE jobs SET status = 'failed', error = ?, updated_at = ? WHERE id = ?",
            (error, _now(), job_id),
        )
