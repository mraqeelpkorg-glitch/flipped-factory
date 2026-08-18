"""
Podcast Clipper Database Models

Extends the existing revenue_tracker database with podcast-specific tables.
All tables use SQLite via the existing get_db() connection.
"""
import sqlite3
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("podcast_db")

DB_PATH = Path(__file__).parent.parent / "data" / "revenue.db"


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_podcast_tables():
    """Create all podcast clipper tables."""
    conn = get_db()
    conn.executescript("""
        -- Source podcast/episode tracking
        CREATE TABLE IF NOT EXISTS podcast_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            channel TEXT,
            duration_seconds REAL,
            niche TEXT DEFAULT 'education',
            thumbnail_url TEXT,
            description TEXT,
            source_type TEXT DEFAULT 'youtube',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Transcription results
        CREATE TABLE IF NOT EXISTS transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            full_text TEXT,
            language TEXT DEFAULT 'en',
            segments_json TEXT,
            speakers_json TEXT,
            word_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_id) REFERENCES podcast_sources(id)
        );

        -- Speaker detection
        CREATE TABLE IF NOT EXISTS speakers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transcript_id INTEGER,
            speaker_label TEXT,
            segment_count INTEGER DEFAULT 0,
            total_duration REAL DEFAULT 0,
            avg_confidence REAL DEFAULT 0,
            FOREIGN KEY (transcript_id) REFERENCES transcripts(id)
        );

        -- Candidate clips before selection
        CREATE TABLE IF NOT EXISTS clip_candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            transcript_id INTEGER,
            start_seconds REAL,
            end_seconds REAL,
            duration_seconds REAL,
            hook_score REAL DEFAULT 0,
            interest_score REAL DEFAULT 0,
            emotion_score REAL DEFAULT 0,
            educational_score REAL DEFAULT 0,
            context_score REAL DEFAULT 0,
            viral_score REAL DEFAULT 0,
            ending_score REAL DEFAULT 0,
            total_score REAL DEFAULT 0,
            status TEXT DEFAULT 'candidate',
            rejection_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_id) REFERENCES podcast_sources(id),
            FOREIGN KEY (transcript_id) REFERENCES transcripts(id)
        );

        -- Final approved clips
        CREATE TABLE IF NOT EXISTS clips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER,
            source_id INTEGER,
            title TEXT,
            hook_text TEXT,
            caption TEXT,
            hashtags TEXT,
            video_path TEXT,
            thumbnail_path TEXT,
            srt_path TEXT,
            duration_seconds REAL,
            file_size_bytes INTEGER,
            video_template TEXT DEFAULT 'SPEAKER_FOCUS',
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES clip_candidates(id),
            FOREIGN KEY (source_id) REFERENCES podcast_sources(id)
        );

        -- Render jobs
        CREATE TABLE IF NOT EXISTS render_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clip_id INTEGER,
            status TEXT DEFAULT 'pending',
            progress REAL DEFAULT 0,
            output_path TEXT,
            error_message TEXT,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (clip_id) REFERENCES clips(id)
        );

        -- QA validation results
        CREATE TABLE IF NOT EXISTS qa_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clip_id INTEGER,
            resolution_check TEXT DEFAULT 'pending',
            aspect_ratio_check TEXT DEFAULT 'pending',
            codec_check TEXT DEFAULT 'pending',
            audio_codec_check TEXT DEFAULT 'pending',
            fps_check TEXT DEFAULT 'pending',
            bitrate_check TEXT DEFAULT 'pending',
            duration_check TEXT DEFAULT 'pending',
            file_size_check TEXT DEFAULT 'pending',
            playability_check TEXT DEFAULT 'pending',
            black_bars_check TEXT DEFAULT 'pending',
            caption_safe_zone_check TEXT DEFAULT 'pending',
            overall_status TEXT DEFAULT 'pending',
            error_details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (clip_id) REFERENCES clips(id)
        );

        -- Content rights tracking
        CREATE TABLE IF NOT EXISTS content_rights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clip_id INTEGER,
            source_id INTEGER,
            rights_status TEXT DEFAULT 'UNKNOWN',
            rights_holder TEXT,
            license_type TEXT,
            can_publish INTEGER DEFAULT 0,
            notes TEXT,
            confirmed_by TEXT,
            confirmed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (clip_id) REFERENCES clips(id),
            FOREIGN KEY (source_id) REFERENCES podcast_sources(id)
        );

        -- Safety review results
        CREATE TABLE IF NOT EXISTS safety_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clip_id INTEGER,
            hate_score REAL DEFAULT 0,
            harassment_score REAL DEFAULT 0,
            threats_score REAL DEFAULT 0,
            sexual_content_score REAL DEFAULT 0,
            violence_score REAL DEFAULT 0,
            illegal_activity_score REAL DEFAULT 0,
            dangerous_score REAL DEFAULT 0,
            fraud_score REAL DEFAULT 0,
            medical_misinfo_score REAL DEFAULT 0,
            overall_risk REAL DEFAULT 0,
            status TEXT DEFAULT 'pending',
            requires_human_review INTEGER DEFAULT 0,
            reviewer_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (clip_id) REFERENCES clips(id)
        );

        -- Duplicate detection hashes
        CREATE TABLE IF NOT EXISTS content_hashes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clip_id INTEGER,
            source_id INTEGER,
            video_hash TEXT,
            audio_hash TEXT,
            transcript_hash TEXT,
            clip_start REAL,
            clip_end REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (clip_id) REFERENCES clips(id),
            FOREIGN KEY (source_id) REFERENCES podcast_sources(id)
        );

        -- Publish queue
        CREATE TABLE IF NOT EXISTS publish_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clip_id INTEGER,
            status TEXT DEFAULT 'queued',
            priority INTEGER DEFAULT 5,
            scheduled_for TIMESTAMP,
            timezone TEXT DEFAULT 'Asia/Karachi',
            retry_count INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,
            last_error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (clip_id) REFERENCES clips(id)
        );

        -- Instagram account tracking
        CREATE TABLE IF NOT EXISTS instagram_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            account_id TEXT,
            token_status TEXT DEFAULT 'unknown',
            token_expires_at TIMESTAMP,
            last_verified_at TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Published posts
        CREATE TABLE IF NOT EXISTS published_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clip_id INTEGER,
            queue_id INTEGER,
            account_id INTEGER,
            platform TEXT DEFAULT 'instagram',
            post_id TEXT,
            post_url TEXT,
            media_id TEXT,
            published_at TIMESTAMP,
            status TEXT DEFAULT 'published',
            analytics_synced_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (clip_id) REFERENCES clips(id),
            FOREIGN KEY (queue_id) REFERENCES publish_queue(id),
            FOREIGN KEY (account_id) REFERENCES instagram_accounts(id)
        );

        -- Job execution logs
        CREATE TABLE IF NOT EXISTS job_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT,
            stage TEXT,
            status TEXT,
            duration_ms INTEGER DEFAULT 0,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            metadata_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Clip hooks (3 candidates per clip)
        CREATE TABLE IF NOT EXISTS clip_hooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clip_id INTEGER,
            hook_text TEXT,
            hook_type TEXT DEFAULT 'question',
            is_selected INTEGER DEFAULT 0,
            ai_score REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (clip_id) REFERENCES clips(id)
        );
    """)
    conn.commit()
    conn.close()
    logger.info("Podcast clipper tables initialized")


# ─── Source Operations ────────────────────────────────────────────────────────
def create_source(url: str, title: str, channel: str, duration: float,
                  niche: str = "education", description: str = "") -> int:
    """Create or get podcast source."""
    conn = get_db()
    existing = conn.execute("SELECT id FROM podcast_sources WHERE url = ?", (url,)).fetchone()
    if existing:
        conn.close()
        return existing["id"]
    
    cursor = conn.execute(
        "INSERT INTO podcast_sources (url, title, channel, duration_seconds, niche, description) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (url, title, channel, duration, niche, description)
    )
    source_id = cursor.lastrowid
    conn.commit()
    conn.close()
    logger.info(f"Source created: ID={source_id}, {title[:50]}")
    return source_id


def get_source(source_id: int) -> dict:
    """Get source by ID."""
    conn = get_db()
    row = conn.execute("SELECT * FROM podcast_sources WHERE id = ?", (source_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


# ─── Transcript Operations ────────────────────────────────────────────────────
def save_transcript(source_id: int, full_text: str, segments: list,
                    speakers: list, language: str = "en") -> int:
    """Save transcription result."""
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO transcripts (source_id, full_text, segments_json, speakers_json, language, word_count) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (source_id, full_text, json.dumps(segments), json.dumps(speakers),
         language, len(full_text.split()))
    )
    transcript_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return transcript_id


def get_transcript(source_id: int) -> dict:
    """Get transcript for a source."""
    conn = get_db()
    row = conn.execute("SELECT * FROM transcripts WHERE source_id = ? ORDER BY id DESC LIMIT 1", (source_id,)).fetchone()
    conn.close()
    if row:
        result = dict(row)
        result["segments"] = json.loads(result.get("segments_json", "[]"))
        result["speakers"] = json.loads(result.get("speakers_json", "[]"))
        return result
    return {}


# ─── Clip Candidate Operations ────────────────────────────────────────────────
def save_candidate(source_id: int, transcript_id: int, start: float, end: float,
                   scores: dict) -> int:
    """Save a clip candidate with scores."""
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO clip_candidates "
        "(source_id, transcript_id, start_seconds, end_seconds, duration_seconds, "
        "hook_score, interest_score, emotion_score, educational_score, "
        "context_score, viral_score, ending_score, total_score) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (source_id, transcript_id, start, end, end - start,
         scores.get("hook", 0), scores.get("interest", 0),
         scores.get("emotion", 0), scores.get("educational", 0),
         scores.get("context", 0), scores.get("viral", 0),
         scores.get("ending", 0), scores.get("total", 0))
    )
    candidate_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return candidate_id


def get_candidates(source_id: int, min_score: float = 0) -> list:
    """Get all candidates for a source, filtered by minimum score."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM clip_candidates WHERE source_id = ? AND total_score >= ? "
        "ORDER BY total_score DESC",
        (source_id, min_score)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_candidate_status(candidate_id: int, status: str, reason: str = ""):
    """Update candidate status (approved/rejected)."""
    conn = get_db()
    conn.execute(
        "UPDATE clip_candidates SET status = ?, rejection_reason = ? WHERE id = ?",
        (status, reason, candidate_id)
    )
    conn.commit()
    conn.close()


# ─── Clip Operations ──────────────────────────────────────────────────────────
def create_clip(candidate_id: int, source_id: int, title: str, hook: str,
                caption: str, hashtags: str, video_path: str, duration: float,
                template: str = "SPEAKER_FOCUS") -> int:
    """Create a final clip record."""
    import os
    file_size = os.path.getsize(video_path) if os.path.exists(video_path) else 0
    
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO clips "
        "(candidate_id, source_id, title, hook_text, caption, hashtags, "
        "video_path, duration_seconds, file_size_bytes, video_template, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft')",
        (candidate_id, source_id, title, hook, caption, hashtags,
         video_path, duration, file_size, template)
    )
    clip_id = cursor.lastrowid
    conn.commit()
    conn.close()
    logger.info(f"Clip created: ID={clip_id}, {title[:40]}")
    return clip_id


def update_clip_status(clip_id: int, status: str):
    """Update clip status."""
    conn = get_db()
    conn.execute("UPDATE clips SET status = ? WHERE id = ?", (status, clip_id))
    conn.commit()
    conn.close()


def get_clip(clip_id: int) -> dict:
    """Get clip by ID."""
    conn = get_db()
    row = conn.execute("SELECT * FROM clips WHERE id = ?", (clip_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


def get_clips_by_status(status: str) -> list:
    """Get all clips with a specific status."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM clips WHERE status = ? ORDER BY created_at DESC", (status,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── QA Operations ────────────────────────────────────────────────────────────
def save_qa_result(clip_id: int, checks: dict) -> int:
    """Save QA validation result."""
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO qa_results "
        "(clip_id, resolution_check, aspect_ratio_check, codec_check, "
        "audio_codec_check, fps_check, bitrate_check, duration_check, "
        "file_size_check, playability_check, black_bars_check, "
        "caption_safe_zone_check, overall_status, error_details) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (clip_id,
         checks.get("resolution", "pending"),
         checks.get("aspect_ratio", "pending"),
         checks.get("codec", "pending"),
         checks.get("audio_codec", "pending"),
         checks.get("fps", "pending"),
         checks.get("bitrate", "pending"),
         checks.get("duration", "pending"),
         checks.get("file_size", "pending"),
         checks.get("playability", "pending"),
         checks.get("black_bars", "pending"),
         checks.get("caption_safe_zone", "pending"),
         checks.get("overall", "pending"),
         checks.get("errors", ""))
    )
    qa_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return qa_id


def get_qa_result(clip_id: int) -> dict:
    """Get latest QA result for a clip."""
    conn = get_db()
    row = conn.execute("SELECT * FROM qa_results WHERE clip_id = ? ORDER BY id DESC LIMIT 1", (clip_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


# ─── Rights Operations ────────────────────────────────────────────────────────
def save_rights(clip_id: int, source_id: int, status: str = "UNKNOWN",
                holder: str = "", notes: str = "") -> int:
    """Save content rights status."""
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO content_rights (clip_id, source_id, rights_status, rights_holder, can_publish, notes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (clip_id, source_id, status, holder, 1 if status != "UNKNOWN" else 0, notes)
    )
    rights_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return rights_id


# ─── Safety Operations ────────────────────────────────────────────────────────
def save_safety_review(clip_id: int, scores: dict, status: str = "pending") -> int:
    """Save safety review result."""
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO safety_reviews "
        "(clip_id, hate_score, harassment_score, threats_score, sexual_content_score, "
        "violence_score, illegal_activity_score, dangerous_score, fraud_score, "
        "medical_misinfo_score, overall_risk, status, requires_human_review) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (clip_id,
         scores.get("hate", 0), scores.get("harassment", 0),
         scores.get("threats", 0), scores.get("sexual_content", 0),
         scores.get("violence", 0), scores.get("illegal_activity", 0),
         scores.get("dangerous", 0), scores.get("fraud", 0),
         scores.get("medical_misinfo", 0), scores.get("overall_risk", 0),
         status, 1 if status == "HUMAN_REVIEW_REQUIRED" else 0)
    )
    review_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return review_id


# ─── Duplicate Detection ──────────────────────────────────────────────────────
def check_duplicate(video_hash: str = "", audio_hash: str = "",
                    transcript_hash: str = "") -> bool:
    """Check if content already exists (duplicate detection)."""
    conn = get_db()
    
    if video_hash:
        row = conn.execute(
            "SELECT id FROM content_hashes WHERE video_hash = ?", (video_hash,)
        ).fetchone()
        if row:
            conn.close()
            return True
    
    if audio_hash:
        row = conn.execute(
            "SELECT id FROM content_hashes WHERE audio_hash = ?", (audio_hash,)
        ).fetchone()
        if row:
            conn.close()
            return True
    
    if transcript_hash:
        row = conn.execute(
            "SELECT id FROM content_hashes WHERE transcript_hash = ?", (transcript_hash,)
        ).fetchone()
        if row:
            conn.close()
            return True
    
    conn.close()
    return False


def save_hash(clip_id: int, source_id: int, video_hash: str = "",
              audio_hash: str = "", transcript_hash: str = "",
              clip_start: float = 0, clip_end: float = 0):
    """Save content hashes for duplicate detection."""
    conn = get_db()
    conn.execute(
        "INSERT INTO content_hashes "
        "(clip_id, source_id, video_hash, audio_hash, transcript_hash, clip_start, clip_end) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (clip_id, source_id, video_hash, audio_hash, transcript_hash, clip_start, clip_end)
    )
    conn.commit()
    conn.close()


# ─── Queue Operations ─────────────────────────────────────────────────────────
def enqueue_clip(clip_id: int, scheduled_for: str = None, priority: int = 5) -> int:
    """Add clip to publish queue."""
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO publish_queue (clip_id, scheduled_for, priority) VALUES (?, ?, ?)",
        (clip_id, scheduled_for, priority)
    )
    queue_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return queue_id


def get_queue(status: str = "queued") -> list:
    """Get all items in queue with a specific status."""
    conn = get_db()
    rows = conn.execute(
        "SELECT pq.*, c.title, c.video_path, c.hook_text, c.hashtags "
        "FROM publish_queue pq "
        "JOIN clips c ON pq.clip_id = c.id "
        "WHERE pq.status = ? ORDER BY pq.priority DESC, pq.created_at ASC",
        (status,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_queue_status(queue_id: int, status: str, error: str = ""):
    """Update queue item status."""
    conn = get_db()
    conn.execute(
        "UPDATE publish_queue SET status = ?, last_error = ? WHERE id = ?",
        (status, error, queue_id)
    )
    conn.commit()
    conn.close()


# ─── Instagram Account Operations ─────────────────────────────────────────────
def get_active_account() -> dict:
    """Get active Instagram account."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM instagram_accounts WHERE is_active = 1 LIMIT 1"
    ).fetchone()
    conn.close()
    return dict(row) if row else {}


def save_instagram_account(username: str, account_id: str, token_status: str = "unknown") -> int:
    """Save Instagram account."""
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO instagram_accounts (username, account_id, token_status) VALUES (?, ?, ?)",
        (username, account_id, token_status)
    )
    account_db_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return account_db_id


# ─── Published Post Operations ────────────────────────────────────────────────
def save_published_post(clip_id: int, queue_id: int, account_id: int,
                        post_id: str, post_url: str = "", media_id: str = "") -> int:
    """Save published post record."""
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO published_posts "
        "(clip_id, queue_id, account_id, post_id, post_url, media_id, published_at, status) "
        "VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'published')",
        (clip_id, queue_id, account_id, post_id, post_url, media_id)
    )
    post_db_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Update clip status
    update_clip_status(clip_id, "published")
    
    return post_db_id


# ─── Job Log Operations ───────────────────────────────────────────────────────
def log_job(job_id: str, stage: str, status: str, duration_ms: int = 0,
            error: str = "", retry_count: int = 0, metadata: dict = None):
    """Log job execution."""
    conn = get_db()
    conn.execute(
        "INSERT INTO job_logs (job_id, stage, status, duration_ms, error_message, retry_count, metadata_json) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (job_id, stage, status, duration_ms, error, retry_count,
         json.dumps(metadata) if metadata else None)
    )
    conn.commit()
    conn.close()


# ─── Hook Operations ──────────────────────────────────────────────────────────
def save_hooks(clip_id: int, hooks: list) -> list:
    """Save 3 hook candidates for a clip."""
    conn = get_db()
    hook_ids = []
    for h in hooks:
        cursor = conn.execute(
            "INSERT INTO clip_hooks (clip_id, hook_text, hook_type, is_selected, ai_score) "
            "VALUES (?, ?, ?, ?, ?)",
            (clip_id, h.get("text", ""), h.get("type", "question"),
             1 if h.get("selected") else 0, h.get("score", 0))
        )
        hook_ids.append(cursor.lastrowid)
    conn.commit()
    conn.close()
    return hook_ids


def select_hook(clip_id: int, hook_id: int):
    """Select a specific hook for a clip."""
    conn = get_db()
    conn.execute("UPDATE clip_hooks SET is_selected = 0 WHERE clip_id = ?", (clip_id,))
    conn.execute("UPDATE clip_hooks SET is_selected = 1 WHERE id = ?", (hook_id,))
    conn.commit()
    conn.close()


# ─── Dashboard Aggregation ────────────────────────────────────────────────────
def get_podcast_dashboard_stats() -> dict:
    """Get podcast clipper specific stats for dashboard."""
    conn = get_db()
    
    stats = {}
    
    try:
        stats["total_sources"] = conn.execute("SELECT COUNT(*) as c FROM podcast_sources").fetchone()["c"]
        stats["total_transcripts"] = conn.execute("SELECT COUNT(*) as c FROM transcripts").fetchone()["c"]
        stats["total_candidates"] = conn.execute("SELECT COUNT(*) as c FROM clip_candidates").fetchone()["c"]
        stats["total_clips"] = conn.execute("SELECT COUNT(*) as c FROM clips").fetchone()["c"]
        stats["approved_clips"] = conn.execute("SELECT COUNT(*) as c FROM clips WHERE status = 'approved'").fetchone()["c"]
        stats["published_clips"] = conn.execute("SELECT COUNT(*) as c FROM clips WHERE status = 'published'").fetchone()["c"]
        stats["queued_clips"] = conn.execute("SELECT COUNT(*) as c FROM publish_queue WHERE status = 'queued'").fetchone()["c"]
        
        # QA stats
        stats["qa_passed"] = conn.execute(
            "SELECT COUNT(*) as c FROM qa_results WHERE overall_status = 'passed'"
        ).fetchone()["c"]
        stats["qa_failed"] = conn.execute(
            "SELECT COUNT(*) as c FROM qa_results WHERE overall_status = 'failed'"
        ).fetchone()["c"]
        
        # Safety stats
        stats["safety_approved"] = conn.execute(
            "SELECT COUNT(*) as c FROM safety_reviews WHERE status = 'approved'"
        ).fetchone()["c"]
        stats["safety_blocked"] = conn.execute(
            "SELECT COUNT(*) as c FROM safety_reviews WHERE status = 'blocked'"
        ).fetchone()["c"]
        stats["safety_human_review"] = conn.execute(
            "SELECT COUNT(*) as c FROM safety_reviews WHERE status = 'HUMAN_REVIEW_REQUIRED'"
        ).fetchone()["c"]
        
        # Recent clips
        recent = conn.execute(
            "SELECT c.*, ps.title as source_title, ps.channel "
            "FROM clips c LEFT JOIN podcast_sources ps ON c.source_id = ps.id "
            "ORDER BY c.created_at DESC LIMIT 10"
        ).fetchall()
        stats["recent_clips"] = [dict(r) for r in recent]
        
    except Exception as e:
        logger.warning(f"Stats query error (tables may not exist yet): {e}")
    
    conn.close()
    return stats


# ─── Init on import ───────────────────────────────────────────────────────────
def ensure_tables():
    """Ensure all podcast tables exist. Call at startup."""
    try:
        init_podcast_tables()
    except Exception as e:
        logger.error(f"Failed to init podcast tables: {e}")
