"""
Revenue Tracker — Track views, engagement, affiliate clicks, revenue.
FREE: SQLite database
"""
import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, date

logger = logging.getLogger("revenue_tracker")

DB_PATH = Path(__file__).parent.parent / "data" / "revenue.db"


# ─── Database Setup ───────────────────────────────────────────────────────────
def get_db():
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize revenue tracking database."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            niche TEXT,
            agent_type TEXT,
            video_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            language TEXT DEFAULT 'en',
            status TEXT DEFAULT 'created'
        );
        
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            platform TEXT DEFAULT 'instagram',
            post_id TEXT,
            post_url TEXT,
            posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES videos(id)
        );
        
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            metric_type TEXT,
            value INTEGER,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id)
        );
        
        CREATE TABLE IF NOT EXISTS revenue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            amount REAL,
            niche TEXT,
            notes TEXT,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS daily_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date DATE UNIQUE,
            videos_created INTEGER DEFAULT 0,
            videos_posted INTEGER DEFAULT 0,
            total_views INTEGER DEFAULT 0,
            total_likes INTEGER DEFAULT 0,
            total_comments INTEGER DEFAULT 0,
            total_revenue REAL DEFAULT 0.0,
            top_niche TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()
    logger.info("Revenue database initialized")


# ─── Video Tracking ───────────────────────────────────────────────────────────
def log_video(title: str, niche: str, agent_type: str, video_path: str, language: str = "en") -> int:
    """Log a new video creation."""
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO videos (title, niche, agent_type, video_path, language) VALUES (?, ?, ?, ?, ?)",
        (title, niche, agent_type, video_path, language)
    )
    video_id = cursor.lastrowid
    conn.commit()
    conn.close()
    logger.info(f"Video logged: ID={video_id}, title={title}")
    return video_id


def update_video_status(video_id: int, status: str):
    """Update video status."""
    conn = get_db()
    conn.execute("UPDATE videos SET status = ? WHERE id = ?", (status, video_id))
    conn.commit()
    conn.close()


# ─── Post Tracking ────────────────────────────────────────────────────────────
def log_post(video_id: int, platform: str, post_id: str, post_url: str = "") -> int:
    """Log a new post."""
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO posts (video_id, platform, post_id, post_url) VALUES (?, ?, ?, ?)",
        (video_id, platform, post_id, post_url)
    )
    post_id_db = cursor.lastrowid
    conn.commit()
    conn.close()
    return post_id_db


# ─── Metrics Tracking ─────────────────────────────────────────────────────────
def log_metric(post_id: int, metric_type: str, value: int):
    """Log a metric (views, likes, comments, shares)."""
    conn = get_db()
    conn.execute(
        "INSERT INTO metrics (post_id, metric_type, value) VALUES (?, ?, ?)",
        (post_id, metric_type, value)
    )
    conn.commit()
    conn.close()


def get_post_metrics(post_id: int) -> dict:
    """Get all metrics for a post."""
    conn = get_db()
    rows = conn.execute(
        "SELECT metric_type, value FROM metrics WHERE post_id = ?", (post_id,)
    ).fetchall()
    conn.close()
    return {row["metric_type"]: row["value"] for row in rows}


# ─── Revenue Tracking ─────────────────────────────────────────────────────────
def log_revenue(source: str, amount: float, niche: str, notes: str = ""):
    """Log revenue entry."""
    conn = get_db()
    conn.execute(
        "INSERT INTO revenue (source, amount, niche, notes) VALUES (?, ?, ?, ?)",
        (source, amount, niche, notes)
    )
    conn.commit()
    conn.close()


def get_total_revenue() -> float:
    """Get total revenue."""
    conn = get_db()
    result = conn.execute("SELECT COALESCE(SUM(amount), 0) as total FROM revenue").fetchone()
    conn.close()
    return result["total"]


def get_revenue_by_niche() -> dict:
    """Get revenue breakdown by niche."""
    conn = get_db()
    rows = conn.execute(
        "SELECT niche, SUM(amount) as total FROM revenue GROUP BY niche"
    ).fetchall()
    conn.close()
    return {row["niche"]: row["total"] for row in rows}


# ─── Daily Log ────────────────────────────────────────────────────────────────
def update_daily_log(videos_created: int = 0, videos_posted: int = 0,
                     views: int = 0, likes: int = 0, comments: int = 0,
                     revenue: float = 0.0, top_niche: str = ""):
    """Update today's daily log."""
    today = date.today()
    conn = get_db()
    
    existing = conn.execute(
        "SELECT * FROM daily_log WHERE log_date = ?", (today,)
    ).fetchone()
    
    if existing:
        conn.execute("""
            UPDATE daily_log SET
                videos_created = videos_created + ?,
                videos_posted = videos_posted + ?,
                total_views = total_views + ?,
                total_likes = total_likes + ?,
                total_comments = total_comments + ?,
                total_revenue = total_revenue + ?
            WHERE log_date = ?
        """, (videos_created, videos_posted, views, likes, comments, revenue, today))
    else:
        conn.execute("""
            INSERT INTO daily_log (log_date, videos_created, videos_posted,
                total_views, total_likes, total_comments, total_revenue, top_niche)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (today, videos_created, videos_posted, views, likes, comments, revenue, top_niche))
    
    conn.commit()
    conn.close()


# ─── Dashboard Data ───────────────────────────────────────────────────────────
def get_dashboard_stats() -> dict:
    """Get comprehensive stats for dashboard."""
    conn = get_db()
    
    total_videos = conn.execute("SELECT COUNT(*) as c FROM videos").fetchone()["c"]
    total_posts = conn.execute("SELECT COUNT(*) as c FROM posts").fetchone()["c"]
    total_revenue = get_total_revenue()
    
    today = date.today()
    today_videos = conn.execute(
        "SELECT COUNT(*) as c FROM videos WHERE DATE(created_at) = ?", (today,)
    ).fetchone()["c"]
    today_posts = conn.execute(
        "SELECT COUNT(*) as c FROM posts WHERE DATE(posted_at) = ?", (today,)
    ).fetchone()["c"]
    
    # Niche breakdown
    niche_stats = conn.execute("""
        SELECT niche, COUNT(*) as count FROM videos GROUP BY niche ORDER BY count DESC
    """).fetchall()
    
    # Agent type breakdown
    agent_stats = conn.execute("""
        SELECT agent_type, COUNT(*) as count FROM videos GROUP BY agent_type ORDER BY count DESC
    """).fetchall()
    
    # Daily trend (last 7 days)
    daily_trend = conn.execute("""
        SELECT DATE(created_at) as day, COUNT(*) as count
        FROM videos WHERE created_at >= DATE('now', '-7 days')
        GROUP BY DATE(created_at) ORDER BY day
    """).fetchall()
    
    # Revenue by niche
    revenue_by_niche = get_revenue_by_niche()
    
    # Top performing posts
    top_posts = conn.execute("""
        SELECT p.post_id, p.platform, v.title, v.niche,
               COALESCE(SUM(CASE WHEN m.metric_type='views' THEN m.value ELSE 0 END), 0) as views,
               COALESCE(SUM(CASE WHEN m.metric_type='likes' THEN m.value ELSE 0 END), 0) as likes
        FROM posts p
        JOIN videos v ON p.video_id = v.id
        LEFT JOIN metrics m ON p.id = m.post_id
        GROUP BY p.id
        ORDER BY views DESC
        LIMIT 10
    """).fetchall()
    
    conn.close()
    
    return {
        "total_videos": total_videos,
        "total_posts": total_posts,
        "total_revenue": total_revenue,
        "today_videos": today_videos,
        "today_posts": today_posts,
        "niche_stats": [{"niche": r["niche"], "count": r["count"]} for r in niche_stats],
        "agent_stats": [{"agent": r["agent_type"], "count": r["count"]} for r in agent_stats],
        "daily_trend": [{"date": str(r["day"]), "count": r["count"]} for r in daily_trend],
        "revenue_by_niche": revenue_by_niche,
        "top_posts": [dict(r) for r in top_posts],
    }
