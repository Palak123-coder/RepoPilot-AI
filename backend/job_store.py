import sqlite3
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


DB_PATH = Path("data/repopilot_jobs.db")
_db_lock = threading.Lock()


def current_timestamp() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        DB_PATH,
        timeout=30,
        check_same_thread=False
    )
    connection.row_factory = sqlite3.Row

    return connection


def _column_exists(connection, table_name: str, column_name: str) -> bool:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row["name"] == column_name for row in rows)


def init_job_store() -> None:
    with _db_lock:
        with _connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA foreign_keys=ON")

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS indexing_jobs (
                    job_id TEXT PRIMARY KEY,
                    repo_url TEXT NOT NULL,
                    status TEXT NOT NULL,
                    files_indexed INTEGER DEFAULT 0,
                    chunks_indexed INTEGER DEFAULT 0,
                    indexing_time_ms INTEGER DEFAULT 0,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    attempts INTEGER DEFAULT 0
                )
                """
            )

            if not _column_exists(connection, "indexing_jobs", "attempts"):
                connection.execute(
                    "ALTER TABLE indexing_jobs ADD COLUMN attempts INTEGER DEFAULT 0"
                )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS job_logs (
                    log_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    attempt INTEGER NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (job_id) REFERENCES indexing_jobs(job_id)
                )
                """
            )

            connection.commit()


def _row_to_job(row) -> Optional[dict]:
    if row is None:
        return None

    return dict(row)


def create_indexing_job(repo_url: str) -> dict:
    init_job_store()

    job = {
        "job_id": str(uuid.uuid4()),
        "repo_url": repo_url,
        "status": "pending",
        "files_indexed": 0,
        "chunks_indexed": 0,
        "indexing_time_ms": 0,
        "error": None,
        "created_at": current_timestamp(),
        "started_at": None,
        "completed_at": None,
        "attempts": 0,
    }

    with _db_lock:
        with _connect() as connection:
            connection.execute(
                """
                INSERT INTO indexing_jobs (
                    job_id,
                    repo_url,
                    status,
                    files_indexed,
                    chunks_indexed,
                    indexing_time_ms,
                    error,
                    created_at,
                    started_at,
                    completed_at,
                    attempts
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job["job_id"],
                    job["repo_url"],
                    job["status"],
                    job["files_indexed"],
                    job["chunks_indexed"],
                    job["indexing_time_ms"],
                    job["error"],
                    job["created_at"],
                    job["started_at"],
                    job["completed_at"],
                    job["attempts"],
                ),
            )

            connection.commit()

    return job


def update_job(job_id: str, **updates) -> None:
    init_job_store()

    allowed_fields = {
        "status",
        "files_indexed",
        "chunks_indexed",
        "indexing_time_ms",
        "error",
        "started_at",
        "completed_at",
        "attempts",
    }

    clean_updates = {
        key: value
        for key, value in updates.items()
        if key in allowed_fields
    }

    if not clean_updates:
        return

    set_clause = ", ".join(f"{key} = ?" for key in clean_updates.keys())
    values = list(clean_updates.values())
    values.append(job_id)

    with _db_lock:
        with _connect() as connection:
            connection.execute(
                f"""
                UPDATE indexing_jobs
                SET {set_clause}
                WHERE job_id = ?
                """,
                values,
            )

            connection.commit()


def get_job(job_id: str) -> Optional[dict]:
    init_job_store()

    with _db_lock:
        with _connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM indexing_jobs
                WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()

    return _row_to_job(row)


def list_jobs(status: Optional[str] = None, limit: int = 50) -> list[dict]:
    init_job_store()

    safe_limit = max(1, min(limit, 200))

    with _db_lock:
        with _connect() as connection:
            if status:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM indexing_jobs
                    WHERE status = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (status, safe_limit),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM indexing_jobs
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (safe_limit,),
                ).fetchall()

    return [dict(row) for row in rows]


def create_job_log(
    job_id: str,
    attempt: int,
    level: str,
    message: str,
    error: Optional[str] = None,
) -> dict:
    init_job_store()

    log = {
        "log_id": str(uuid.uuid4()),
        "job_id": job_id,
        "attempt": attempt,
        "level": level,
        "message": message,
        "error": error,
        "created_at": current_timestamp(),
    }

    with _db_lock:
        with _connect() as connection:
            connection.execute(
                """
                INSERT INTO job_logs (
                    log_id,
                    job_id,
                    attempt,
                    level,
                    message,
                    error,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log["log_id"],
                    log["job_id"],
                    log["attempt"],
                    log["level"],
                    log["message"],
                    log["error"],
                    log["created_at"],
                ),
            )

            connection.commit()

    return log


def get_job_logs(job_id: str) -> list[dict]:
    init_job_store()

    with _db_lock:
        with _connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM job_logs
                WHERE job_id = ?
                ORDER BY created_at ASC
                """,
                (job_id,),
            ).fetchall()

    return [dict(row) for row in rows]

