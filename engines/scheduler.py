"""
Scheduler — Publishing queue, human approval, scheduled posting.

Manages the publish queue:
1. Agent creates content → QA passes → enters queue as "pending_approval"
2. Human approves → status changes to "approved" or "scheduled"
3. Scheduler picks up approved/scheduled items → publishes to Instagram
4. Records post_id, post_url, analytics sync timestamp

Every agent MUST call:
    queue_for_publishing(video_path, caption, hashtags, agent_type, job_id)

Dashboard MUST provide:
    approve_clip(clip_id) / reject_clip(clip_id)
"""
import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("scheduler")

DB_PATH = Path(__file__).parent.parent / "data" / "revenue.db"

# Approval statuses
APPROVAL_PENDING = "pending_approval"
APPROVAL_APPROVED = "approved"
APPROVAL_REJECTED = "rejected"
APPROVAL_SCHEDULED = "scheduled"
APPROVAL_PUBLISHED = "published"
APPROVAL_FAILED = "failed"


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_scheduler_tables():
    """Create scheduler tables."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS production_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT,
            video_id INTEGER,
            video_path TEXT NOT NULL,
            caption TEXT DEFAULT '',
            hashtags TEXT DEFAULT '[]',
            agent_type TEXT,
            approval_status TEXT DEFAULT 'pending_approval',
            approved_by TEXT,
            approved_at TIMESTAMP,
            scheduled_for TIMESTAMP,
            published_at TIMESTAMP,
            post_id TEXT,
            post_url TEXT,
            priority INTEGER DEFAULT 5,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES videos(id)
        );

        CREATE TABLE IF NOT EXISTS approval_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            queue_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            performed_by TEXT DEFAULT 'system',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (queue_id) REFERENCES production_queue(id)
        );

        CREATE INDEX IF NOT EXISTS idx_prodq_status ON production_queue(approval_status);
        CREATE INDEX IF NOT EXISTS idx_prodq_scheduled ON production_queue(scheduled_for);
        CREATE INDEX IF NOT EXISTS idx_prodq_agent ON production_queue(agent_type);
    """)
    conn.commit()
    conn.close()
    logger.info("Scheduler tables initialized")


# ─── Queue Management ─────────────────────────────────────────────────────────

def queue_for_publishing(
    video_path: str,
    caption: str = "",
    hashtags: list = None,
    agent_type: str = "",
    job_id: str = "",
    video_id: int = None,
    priority: int = 5,
    auto_approve: bool = False,
) -> int:
    """
    Add a video to the publish queue.

    Every agent MUST call after QA passes:
        queue_id = queue_for_publishing(
            video_path="/path/to/clip.mp4",
            caption="Amazing tech insight!",
            hashtags=["tech", "AI", "innovation"],
            agent_type="youtube_clipper",
            job_id="job_youtube_clipper_20260818_abc123",
        )
    """
    conn = get_db()

    status = APPROVAL_APPROVED if auto_approve else APPROVAL_PENDING

    cursor = conn.execute("""
        INSERT INTO production_queue
            (job_id, video_id, video_path, caption, hashtags, agent_type,
             approval_status, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (job_id, video_id, video_path, caption, json.dumps(hashtags or []),
          agent_type, status, priority))

    queue_id = cursor.lastrowid
    conn.commit()
    conn.close()

    logger.info(f"Queued for publishing: id={queue_id}, agent={agent_type}, status={status}")
    return queue_id


def approve_item(queue_id: int, approved_by: str = "human") -> bool:
    """
    Approve a queued item for publishing.

    Dashboard calls this when user clicks approve:
        approve_item(queue_id=42, approved_by="admin")
    """
    conn = get_db()
    conn.execute("""
        UPDATE production_queue SET
            approval_status = ?,
            approved_by = ?,
            approved_at = CURRENT_TIMESTAMP
        WHERE id = ? AND approval_status = ?
    """, (APPROVAL_APPROVED, approved_by, queue_id, APPROVAL_PENDING))

    conn.execute("""
        INSERT INTO approval_log (queue_id, action, performed_by)
        VALUES (?, 'approved', ?)
    """, (queue_id, approved_by))

    conn.commit()
    conn.close()
    logger.info(f"Item approved: queue_id={queue_id} by {approved_by}")
    return True


def reject_item(queue_id: int, notes: str = "", performed_by: str = "human") -> bool:
    """Reject a queued item."""
    conn = get_db()
    conn.execute("""
        UPDATE production_queue SET approval_status = ?, notes = ?
        WHERE id = ?
    """, (APPROVAL_REJECTED, notes, queue_id))

    conn.execute("""
        INSERT INTO approval_log (queue_id, action, performed_by, notes)
        VALUES (?, 'rejected', ?, ?)
    """, (queue_id, performed_by, notes))

    conn.commit()
    conn.close()
    logger.info(f"Item rejected: queue_id={queue_id}")
    return True


def schedule_item(queue_id: int, scheduled_for: str) -> bool:
    """
    Schedule an approved item for future publishing.

    Format: "2026-08-19T10:00:00" or "tomorrow 10am"
    """
    conn = get_db()

    # Parse schedule time
    if scheduled_for == "tomorrow":
        dt = datetime.now() + timedelta(days=1)
        dt = dt.replace(hour=10, minute=0, second=0)
        scheduled_for = dt.isoformat()
    elif scheduled_for == "asap":
        scheduled_for = datetime.now().isoformat()

    conn.execute("""
        UPDATE production_queue SET
            approval_status = ?,
            scheduled_for = ?
        WHERE id = ?
    """, (APPROVAL_SCHEDULED, scheduled_for, queue_id))

    conn.commit()
    conn.close()
    logger.info(f"Item scheduled: queue_id={queue_id} at {scheduled_for}")
    return True


def mark_published(queue_id: int, post_id: str, post_url: str) -> bool:
    """Mark an item as published."""
    conn = get_db()
    conn.execute("""
        UPDATE production_queue SET
            approval_status = ?,
            post_id = ?,
            post_url = ?,
            published_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (APPROVAL_PUBLISHED, post_id, post_url, queue_id))
    conn.commit()
    conn.close()
    logger.info(f"Item published: queue_id={queue_id}, post={post_url}")
    return True


def mark_failed(queue_id: int, error: str) -> bool:
    """Mark an item as failed to publish."""
    conn = get_db()
    conn.execute("""
        UPDATE production_queue SET approval_status = ?, notes = ?
        WHERE id = ?
    """, (APPROVAL_FAILED, error, queue_id))
    conn.commit()
    conn.close()
    return True


# ─── Queue Queries ────────────────────────────────────────────────────────────

def get_pending_approvals(limit: int = 50) -> list:
    """Get items waiting for human approval."""
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM production_queue
        WHERE approval_status = ?
        ORDER BY priority ASC, created_at ASC
        LIMIT ?
    """, (APPROVAL_PENDING, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_approved_items(limit: int = 50) -> list:
    """Get approved items ready for publishing."""
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM production_queue
        WHERE approval_status = ?
        ORDER BY priority ASC, created_at ASC
        LIMIT ?
    """, (APPROVAL_APPROVED, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_ready_to_publish(limit: int = 10) -> list:
    """
    Get items ready to publish NOW (approved or scheduled & past due).

    Scheduler calls this periodically:
        items = get_ready_to_publish()
        for item in items:
            publish(item)
    """
    now = datetime.now().isoformat()
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM production_queue
        WHERE approval_status IN (?, ?)
          AND (scheduled_for IS NULL OR scheduled_for <= ?)
        ORDER BY priority ASC, created_at ASC
        LIMIT ?
    """, (APPROVAL_APPROVED, APPROVAL_SCHEDULED, now, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_published_history(limit: int = 50) -> list:
    """Get published items."""
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM production_queue
        WHERE approval_status = ?
        ORDER BY published_at DESC
        LIMIT ?
    """, (APPROVAL_PUBLISHED, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_queue_stats() -> dict:
    """Get queue statistics."""
    conn = get_db()
    stats = {}
    for s in [APPROVAL_PENDING, APPROVAL_APPROVED, APPROVAL_REJECTED,
              APPROVAL_SCHEDULED, APPROVAL_PUBLISHED, APPROVAL_FAILED]:
        count = conn.execute(
            "SELECT COUNT(*) as c FROM production_queue WHERE approval_status = ?", (s,)
        ).fetchone()["c"]
        stats[s] = count

    # Per agent
    agent_stats = conn.execute("""
        SELECT agent_type, approval_status, COUNT(*) as count
        FROM production_queue GROUP BY agent_type, approval_status
    """).fetchall()
    stats["by_agent"] = {}
    for row in agent_stats:
        agent = row["agent_type"]
        if agent not in stats["by_agent"]:
            stats["by_agent"][agent] = {}
        stats["by_agent"][agent][row["approval_status"]] = row["count"]

    conn.close()
    return stats


def get_approval_log(queue_id: int) -> list:
    """Get approval history for an item."""
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM approval_log WHERE queue_id = ? ORDER BY created_at
    """, (queue_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Auto-Init ────────────────────────────────────────────────────────────────
try:
    init_scheduler_tables()
except Exception:
    pass
