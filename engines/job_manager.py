"""
Job Manager — Production job lifecycle for all 12 agents.

Every agent run produces a job with:
- job_id (unique identifier)
- status (queued → running → completed/failed/cancelled)
- checkpoint data (resume after failure)
- structured output (standardized format)
- retry tracking
- artifact paths
- timing metrics
"""
import json
import sqlite3
import logging
import uuid
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger("job_manager")

DB_PATH = Path(__file__).parent.parent / "data" / "revenue.db"

# Status constants
STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_CANCELLED = "cancelled"
STATUS_RESUMING = "resuming"

# Agent types (must match agent file names without 'agent_' prefix and '.py' suffix)
AGENT_TYPES = [
    "youtube_clipper",
    "podcast_clipper",
    "blog_to_video",
    "remix_flip",
    "dub_flip",
    "data_to_video",
    "product_compilation",
    "bts_educational",
    "trending_niche",
    "course_teaser",
    "live_highlights",
    "screenshot_tutorial",
]


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_job_tables():
    """Create job tracking tables if they don't exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT UNIQUE NOT NULL,
            agent_type TEXT NOT NULL,
            status TEXT DEFAULT 'queued',
            input_params TEXT DEFAULT '{}',
            checkpoint TEXT DEFAULT '{}',
            output TEXT DEFAULT '{}',
            error_message TEXT DEFAULT '',
            retry_count INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,
            artifacts TEXT DEFAULT '[]',
            video_id INTEGER,
            post_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            duration_seconds REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS job_stages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            stage_name TEXT NOT NULL,
            stage_order INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            input_data TEXT DEFAULT '{}',
            output_data TEXT DEFAULT '{}',
            error_message TEXT DEFAULT '',
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            duration_seconds REAL DEFAULT 0,
            FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        );

        CREATE INDEX IF NOT EXISTS idx_jobs_agent ON jobs(agent_type);
        CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
        CREATE INDEX IF NOT EXISTS idx_stages_job ON job_stages(job_id);
    """)
    conn.commit()
    conn.close()
    logger.info("Job manager tables initialized")


def generate_job_id(agent_type: str) -> str:
    """Generate unique job ID."""
    short_id = uuid.uuid4().hex[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"job_{agent_type}_{timestamp}_{short_id}"


def create_job(agent_type: str, input_params: dict = None, max_retries: int = 3) -> str:
    """
    Create a new job. Returns job_id.

    Every agent MUST call this at entry:
        job_id = create_job("youtube_clipper", {"url": "...", "niche": "tech"})
    """
    job_id = generate_job_id(agent_type)
    conn = get_db()
    conn.execute("""
        INSERT INTO jobs (job_id, agent_type, status, input_params, max_retries)
        VALUES (?, ?, ?, ?, ?)
    """, (job_id, agent_type, STATUS_QUEUED, json.dumps(input_params or {}), max_retries))
    conn.commit()
    conn.close()
    logger.info(f"Job created: {job_id} (agent={agent_type})")
    return job_id


def start_job(job_id: str):
    """Mark job as running."""
    conn = get_db()
    conn.execute("""
        UPDATE jobs SET status = ?, started_at = CURRENT_TIMESTAMP WHERE job_id = ?
    """, (STATUS_RUNNING, job_id))
    conn.commit()
    conn.close()
    logger.info(f"Job started: {job_id}")


def complete_job(job_id: str, output: dict = None, video_id: int = None):
    """Mark job as completed."""
    conn = get_db()
    conn.execute("""
        UPDATE jobs SET status = ?, completed_at = CURRENT_TIMESTAMP,
            output = ?, video_id = ?,
            duration_seconds = JULIANDAY(CURRENT_TIMESTAMP) - JULIANDAY(started_at)
        WHERE job_id = ?
    """, (STATUS_COMPLETED, json.dumps(output or {}), video_id, job_id))
    conn.commit()
    conn.close()
    logger.info(f"Job completed: {job_id}")


def fail_job(job_id: str, error: str, can_retry: bool = True):
    """
    Mark job as failed. Auto-retries if possible.

    Returns True if will retry, False if permanently failed.
    """
    conn = get_db()
    job = conn.execute(
        "SELECT retry_count, max_retries FROM jobs WHERE job_id = ?", (job_id,)
    ).fetchone()

    if not job:
        conn.close()
        return False

    retry_count = job["retry_count"]
    max_retries = job["max_retries"]

    if can_retry and retry_count < max_retries:
        # Increment retry count, set back to queued
        conn.execute("""
            UPDATE jobs SET status = ?, retry_count = retry_count + 1,
                error_message = ? WHERE job_id = ?
        """, (STATUS_QUEUED, error, job_id))
        conn.commit()
        conn.close()
        logger.warning(f"Job {job_id} failed (retry {retry_count + 1}/{max_retries}): {error}")
        return True
    else:
        # Permanent failure
        conn.execute("""
            UPDATE jobs SET status = ?, error_message = ?,
                completed_at = CURRENT_TIMESTAMP,
                duration_seconds = JULIANDAY(CURRENT_TIMESTAMP) - JULIANDAY(started_at)
            WHERE job_id = ?
        """, (STATUS_FAILED, error, job_id))
        conn.commit()
        conn.close()
        logger.error(f"Job {job_id} permanently failed: {error}")
        return False


def cancel_job(job_id: str):
    """Cancel a job."""
    conn = get_db()
    conn.execute("""
        UPDATE jobs SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE job_id = ?
    """, (STATUS_CANCELLED, job_id))
    conn.commit()
    conn.close()


def save_checkpoint(job_id: str, checkpoint: dict):
    """
    Save checkpoint data for resume.

    Agents MUST call this after each major stage:
        save_checkpoint(job_id, {"stage": "download", "video_path": "/path/to/video.mp4"})
    """
    conn = get_db()
    conn.execute("""
        UPDATE jobs SET checkpoint = ? WHERE job_id = ?
    """, (json.dumps(checkpoint), job_id))
    conn.commit()
    conn.close()
    logger.debug(f"Checkpoint saved for {job_id}: stage={checkpoint.get('stage')}")


def load_checkpoint(job_id: str) -> dict:
    """Load checkpoint data."""
    conn = get_db()
    row = conn.execute(
        "SELECT checkpoint FROM jobs WHERE job_id = ?", (job_id,)
    ).fetchone()
    conn.close()
    if row:
        return json.loads(row["checkpoint"])
    return {}


def get_resumable_jobs(agent_type: str = None) -> list:
    """
    Get jobs that can be resumed (failed with retry available).

    Agents call this at startup to resume interrupted work:
        jobs = get_resumable_jobs("youtube_clipper")
    """
    conn = get_db()
    if agent_type:
        rows = conn.execute("""
            SELECT job_id, agent_type, input_params, checkpoint, retry_count, max_retries
            FROM jobs WHERE status = ? AND agent_type = ? AND retry_count < max_retries
            ORDER BY created_at
        """, (STATUS_FAILED, agent_type)).fetchall()
    else:
        rows = conn.execute("""
            SELECT job_id, agent_type, input_params, checkpoint, retry_count, max_retries
            FROM jobs WHERE status = ? AND retry_count < max_retries
            ORDER BY created_at
        """, (STATUS_FAILED,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_artifact(job_id: str, artifact_path: str, artifact_type: str = "video"):
    """Track an artifact (video, audio, script, image, etc.)."""
    conn = get_db()
    row = conn.execute(
        "SELECT artifacts FROM jobs WHERE job_id = ?", (job_id,)
    ).fetchone()
    if row:
        artifacts = json.loads(row["artifacts"])
    else:
        artifacts = []

    artifacts.append({
        "path": artifact_path,
        "type": artifact_type,
        "created_at": datetime.now().isoformat(),
    })

    conn.execute("""
        UPDATE jobs SET artifacts = ? WHERE job_id = ?
    """, (json.dumps(artifacts), job_id))
    conn.commit()
    conn.close()


# ─── Stage Tracking ────────────────────────────────────────────────────────────

def start_stage(job_id: str, stage_name: str, stage_order: int = 0, input_data: dict = None):
    """Start a pipeline stage."""
    conn = get_db()
    # Check if stage already exists (for resume)
    existing = conn.execute("""
        SELECT id, status FROM job_stages
        WHERE job_id = ? AND stage_name = ?
    """, (job_id, stage_name)).fetchone()

    if existing and existing["status"] == "completed":
        # Stage already done, skip
        conn.close()
        return existing["id"]

    if existing:
        # Resume from this stage
        conn.execute("""
            UPDATE job_stages SET status = 'running', started_at = CURRENT_TIMESTAMP,
                input_data = ? WHERE id = ?
        """, (json.dumps(input_data or {}), existing["id"]))
        conn.commit()
        stage_id = existing["id"]
    else:
        cursor = conn.execute("""
            INSERT INTO job_stages (job_id, stage_name, stage_order, status, input_data)
            VALUES (?, ?, ?, 'running', ?)
        """, (job_id, stage_name, stage_order, json.dumps(input_data or {})))
        stage_id = cursor.lastrowid
        conn.commit()
    conn.close()
    logger.debug(f"Stage started: {job_id}/{stage_name}")
    return stage_id


def complete_stage(job_id: str, stage_name: str, output_data: dict = None):
    """Mark a stage as completed."""
    conn = get_db()
    conn.execute("""
        UPDATE job_stages SET status = 'completed', output_data = ?,
            completed_at = CURRENT_TIMESTAMP,
            duration_seconds = JULIANDAY(CURRENT_TIMESTAMP) - JULIANDAY(started_at)
        WHERE job_id = ? AND stage_name = ?
    """, (json.dumps(output_data or {}), job_id, stage_name))
    conn.commit()
    conn.close()
    logger.debug(f"Stage completed: {job_id}/{stage_name}")


def fail_stage(job_id: str, stage_name: str, error: str):
    """Mark a stage as failed."""
    conn = get_db()
    conn.execute("""
        UPDATE job_stages SET status = 'failed', error_message = ?,
            completed_at = CURRENT_TIMESTAMP,
            duration_seconds = JULIANDAY(CURRENT_TIMESTAMP) - JULIANDAY(started_at)
        WHERE job_id = ? AND stage_name = ?
    """, (error, job_id, stage_name))
    conn.commit()
    conn.close()
    logger.error(f"Stage failed: {job_id}/{stage_name}: {error}")


def get_completed_stages(job_id: str) -> list:
    """Get list of completed stages for a job (for resume)."""
    conn = get_db()
    rows = conn.execute("""
        SELECT stage_name, output_data FROM job_stages
        WHERE job_id = ? AND status = 'completed'
        ORDER BY stage_order
    """, (job_id,)).fetchall()
    conn.close()
    return [{"stage": r["stage_name"], "output": json.loads(r["output_data"])} for r in rows]


# ─── Query Functions ───────────────────────────────────────────────────────────

def get_job(job_id: str) -> dict:
    """Get full job details."""
    conn = get_db()
    row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    conn.close()
    if row:
        return dict(row)
    return {}


def get_jobs(agent_type: str = None, status: str = None, limit: int = 50) -> list:
    """Get jobs with optional filters."""
    conn = get_db()
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []
    if agent_type:
        query += " AND agent_type = ?"
        params.append(agent_type)
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_job_stages(job_id: str) -> list:
    """Get all stages for a job."""
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM job_stages WHERE job_id = ? ORDER BY stage_order
    """, (job_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_queue_stats() -> dict:
    """Get queue statistics."""
    conn = get_db()
    stats = {}
    for s in [STATUS_QUEUED, STATUS_RUNNING, STATUS_COMPLETED, STATUS_FAILED]:
        count = conn.execute(
            "SELECT COUNT(*) as c FROM jobs WHERE status = ?", (s,)
        ).fetchone()["c"]
        stats[s] = count

    # Per agent type
    agent_stats = conn.execute("""
        SELECT agent_type, status, COUNT(*) as count
        FROM jobs GROUP BY agent_type, status
    """).fetchall()
    stats["by_agent"] = {}
    for row in agent_stats:
        agent = row["agent_type"]
        if agent not in stats["by_agent"]:
            stats["by_agent"][agent] = {}
        stats["by_agent"][agent][row["status"]] = row["count"]

    conn.close()
    return stats


# ─── Structured Output ────────────────────────────────────────────────────────

def build_output(
    success: bool,
    video_path: str = "",
    post_id: str = "",
    post_url: str = "",
    caption: str = "",
    hashtags: list = None,
    metadata: dict = None,
    error: str = "",
) -> dict:
    """
    Build standardized agent output.

    Every agent MUST return this format from run():
        return build_output(success=True, video_path="...", ...)
    """
    return {
        "success": success,
        "video_path": video_path,
        "post_id": post_id,
        "post_url": post_url,
        "caption": caption,
        "hashtags": hashtags or [],
        "metadata": metadata or {},
        "error": error,
        "timestamp": datetime.now().isoformat(),
    }


# ─── Auto-Init ────────────────────────────────────────────────────────────────
# Initialize tables on import
try:
    init_job_tables()
except Exception:
    pass  # Allow import without DB
