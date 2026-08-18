"""
Dedup Engine — Duplicate prevention for all agents.

Uses content hashing (video, audio, transcript, source segment) to prevent
the same source + segment from ever being published twice.

Every agent MUST call:
    1. check_duplicate(source_url, segment_start, segment_end) before creating content
    2. register_content(video_path, source_url, ...) after creating content
"""
import hashlib
import json
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger("dedup_engine")

DB_PATH = Path(__file__).parent.parent / "data" / "revenue.db"


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_dedup_tables():
    """Create content dedup tables if they don't exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS content_dedup (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT,
            source_url TEXT,
            source_segment_start REAL,
            source_segment_end REAL,
            video_hash TEXT,
            audio_hash TEXT,
            transcript_hash TEXT,
            content_fingerprint TEXT,
            agent_type TEXT,
            video_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_url, source_segment_start, source_segment_end)
        );

        CREATE INDEX IF NOT EXISTS idx_dedup_video ON content_dedup(video_hash);
        CREATE INDEX IF NOT EXISTS idx_dedup_source ON content_dedup(source_url);
        CREATE INDEX IF NOT EXISTS idx_dedup_fingerprint ON content_dedup(content_fingerprint);
    """)
    conn.commit()
    conn.close()
    logger.info("Dedup tables initialized")


# ─── Hashing Functions ────────────────────────────────────────────────────────

def hash_file(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        logger.error(f"Hash failed for {file_path}: {e}")
        return ""


def hash_video_quick(file_path: str) -> str:
    """
    Quick video hash — samples first 1MB, middle 1MB, last 1MB.
    Much faster than full hash for large videos.
    """
    try:
        h = hashlib.sha256()
        size = Path(file_path).stat().st_size

        with open(file_path, "rb") as f:
            # First 1MB
            h.update(f.read(1024 * 1024))

            # Middle 1MB
            if size > 2 * 1024 * 1024:
                f.seek(size // 2)
                h.update(f.read(1024 * 1024))

            # Last 1MB
            if size > 1024 * 1024:
                f.seek(max(0, size - 1024 * 1024))
                h.update(f.read(1024 * 1024))

        return h.hexdigest()
    except Exception as e:
        logger.error(f"Quick hash failed for {file_path}: {e}")
        return ""


def hash_text(text: str) -> str:
    """Hash a text string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_fingerprint(source_url: str, start: float, end: float) -> str:
    """
    Compute a content fingerprint from source + segment.
    Same source + same segment = same fingerprint = duplicate.
    """
    raw = f"{source_url}|{start:.2f}|{end:.2f}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ─── Duplicate Detection ─────────────────────────────────────────────────────

def check_duplicate(
    source_url: str,
    segment_start: float = None,
    segment_end: float = None,
) -> dict:
    """
    Check if this source + segment has been processed before.

    Returns:
        {"is_duplicate": bool, "existing_id": int|None, "reason": str}

    Every agent MUST call before creating content:
        dup = check_duplicate("https://youtube.com/watch?v=...", 93.9, 135.2)
        if dup["is_duplicate"]:
            return build_output(success=False, error="Duplicate content")
    """
    conn = get_db()

    # Check by fingerprint (source + segment)
    if segment_start is not None and segment_end is not None:
        fp = compute_fingerprint(source_url, segment_start, segment_end)
        row = conn.execute("""
            SELECT id, video_path, agent_type, created_at
            FROM content_dedup WHERE content_fingerprint = ?
        """, (fp,)).fetchone()

        if row:
            conn.close()
            logger.warning(f"Duplicate detected: source={source_url}, segment={segment_start}-{segment_end}")
            return {
                "is_duplicate": True,
                "existing_id": row["id"],
                "existing_path": row["video_path"],
                "reason": f"Same source+segment already processed (id={row['id']})",
            }

    # Check by source URL (any segment from same source)
    if source_url:
        rows = conn.execute("""
            SELECT id, source_segment_start, source_segment_end, video_path
            FROM content_dedup WHERE source_url = ?
        """, (source_url,)).fetchall()

        # Check for overlapping segments
        if rows and segment_start is not None and segment_end is not None:
            for row in rows:
                existing_start = row["source_segment_start"]
                existing_end = row["source_segment_end"]
                if existing_start is None or existing_end is None:
                    continue
                # Check overlap
                if (segment_start < existing_end and segment_end > existing_start):
                    conn.close()
                    return {
                        "is_duplicate": True,
                        "existing_id": row["id"],
                        "existing_path": row["video_path"],
                        "reason": f"Overlapping segment: existing={existing_start}-{existing_end}, new={segment_start}-{segment_end}",
                    }

    conn.close()
    return {"is_duplicate": False, "existing_id": None, "reason": ""}


def check_video_hash(video_path: str) -> dict:
    """
    Check if this exact video file has been processed before.

    Returns:
        {"is_duplicate": bool, "existing_id": int|None}
    """
    conn = get_db()
    vhash = hash_video_quick(video_path)
    if not vhash:
        conn.close()
        return {"is_duplicate": False, "existing_id": None}

    row = conn.execute("""
        SELECT id, source_url, video_path, created_at
        FROM content_dedup WHERE video_hash = ?
    """, (vhash,)).fetchone()

    conn.close()
    if row:
        return {
            "is_duplicate": True,
            "existing_id": row["id"],
            "reason": f"Identical video hash (path={row['video_path']})",
        }
    return {"is_duplicate": False, "existing_id": None}


# ─── Registration ─────────────────────────────────────────────────────────────

def register_content(
    video_path: str,
    source_url: str = "",
    segment_start: float = None,
    segment_end: float = None,
    transcript: str = "",
    agent_type: str = "",
    job_id: str = "",
) -> int:
    """
    Register a new content piece to prevent future duplicates.

    Every agent MUST call after creating content:
        register_content(
            video_path="/path/to/clip.mp4",
            source_url="https://youtube.com/watch?v=...",
            segment_start=93.9,
            segment_end=135.2,
            transcript="...",
            agent_type="youtube_clipper",
        )
    """
    conn = get_db()

    vhash = hash_video_quick(video_path) if video_path and Path(video_path).exists() else ""
    thash = hash_text(transcript) if transcript else ""
    fp = compute_fingerprint(source_url, segment_start, segment_end) if source_url else ""

    try:
        cursor = conn.execute("""
            INSERT OR REPLACE INTO content_dedup
                (job_id, source_url, source_segment_start, source_segment_end,
                 video_hash, transcript_hash, content_fingerprint,
                 agent_type, video_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (job_id, source_url, segment_start, segment_end,
              vhash, thash, fp, agent_type, video_path))
        row_id = cursor.lastrowid
        conn.commit()
        logger.info(f"Content registered: id={row_id}, source={source_url}, segment={segment_start}-{segment_end}")
    except sqlite3.IntegrityError:
        row_id = -1
        logger.warning(f"Content already registered: {source_url} {segment_start}-{segment_end}")
    finally:
        conn.close()

    return row_id


# ─── Query ────────────────────────────────────────────────────────────────────

def get_content_history(agent_type: str = None, limit: int = 100) -> list:
    """Get recent content history."""
    conn = get_db()
    if agent_type:
        rows = conn.execute("""
            SELECT * FROM content_dedup WHERE agent_type = ?
            ORDER BY created_at DESC LIMIT ?
        """, (agent_type, limit)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM content_dedup ORDER BY created_at DESC LIMIT ?
        """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_source_count(source_url: str) -> int:
    """How many clips have been created from this source."""
    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) as c FROM content_dedup WHERE source_url = ?",
        (source_url,)
    ).fetchone()["c"]
    conn.close()
    return count


# ─── Auto-Init ────────────────────────────────────────────────────────────────
try:
    init_dedup_tables()
except Exception:
    pass
