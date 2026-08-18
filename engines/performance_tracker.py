"""
Post-Publish Performance Tracker — Track every published video's performance.

Tracks:
- Views, watch time, completion rate
- Shares, saves, comments, follows
- Engagement rate per video
- Performance by niche, hook type, format, length
- Trend over time
- Weekly/monthly reports
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("performance_tracker")

DATA_DIR = Path(__file__).parent.parent / "data"
PERF_DIR = DATA_DIR / "performance"
PERF_DIR.mkdir(parents=True, exist_ok=True)

# ─── Performance Database (SQLite) ────────────────────────────────────────────

def _get_db():
    """Get performance database connection."""
    import sqlite3
    db_path = DATA_DIR / "performance.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def init_performance_db():
    """Initialize performance tracking tables."""
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS published_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            media_id TEXT,
            agent_type TEXT,
            niche TEXT,
            hook_type TEXT,
            hook_text TEXT,
            topic TEXT,
            duration_seconds REAL,
            template TEXT,
            caption_style TEXT,
            publish_time TEXT,
            source_url TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS performance_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            media_id TEXT,
            snapshot_time TEXT,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            saves INTEGER DEFAULT 0,
            reach INTEGER DEFAULT 0,
            impressions INTEGER DEFAULT 0,
            watch_time_total REAL DEFAULT 0,
            watch_time_avg REAL DEFAULT 0,
            completion_rate REAL DEFAULT 0,
            profile_visits INTEGER DEFAULT 0,
            follows INTEGER DEFAULT 0,
            website_clicks INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS performance_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            summary_date TEXT,
            period TEXT,
            total_videos INTEGER DEFAULT 0,
            total_views INTEGER DEFAULT 0,
            total_reach INTEGER DEFAULT 0,
            total_interactions INTEGER DEFAULT 0,
            avg_engagement_rate REAL DEFAULT 0,
            avg_completion_rate REAL DEFAULT 0,
            best_performing_video TEXT,
            worst_performing_video TEXT,
            top_niche TEXT,
            top_hook_type TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS niche_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            niche TEXT,
            period_start TEXT,
            period_end TEXT,
            video_count INTEGER DEFAULT 0,
            total_views INTEGER DEFAULT 0,
            total_reach INTEGER DEFAULT 0,
            total_interactions INTEGER DEFAULT 0,
            avg_engagement_rate REAL DEFAULT 0,
            avg_completion_rate REAL DEFAULT 0,
            avg_watch_time REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS hook_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hook_type TEXT,
            hook_text TEXT,
            video_count INTEGER DEFAULT 0,
            total_views INTEGER DEFAULT 0,
            total_reach INTEGER DEFAULT 0,
            total_interactions INTEGER DEFAULT 0,
            avg_engagement_rate REAL DEFAULT 0,
            avg_completion_rate REAL DEFAULT 0,
            avg_watch_time REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()
    logger.info("Performance database initialized")


class PerformanceTracker:
    """
    Track post-publish performance for all videos.
    
    Usage:
        tracker = PerformanceTracker()
        tracker.register_published(video_id=1, media_id="...", hook_type="curiosity", ...)
        tracker.update_snapshot(media_id="...", views=1000, likes=50, ...)
        report = tracker.get_period_report(period="7d")
    """
    
    def __init__(self):
        init_performance_db()
    
    # ─── Registration ─────────────────────────────────────────────────────────
    
    def register_published(self, video_id: int, media_id: str, agent_type: str,
                           niche: str, hook_type: str = "", hook_text: str = "",
                           topic: str = "", duration_seconds: float = 0,
                           template: str = "", caption_style: str = "",
                           source_url: str = "") -> int:
        """Register a newly published video for tracking."""
        conn = _get_db()
        cursor = conn.execute("""
            INSERT INTO published_videos 
            (video_id, media_id, agent_type, niche, hook_type, hook_text, topic,
             duration_seconds, template, caption_style, publish_time, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (video_id, media_id, agent_type, niche, hook_type, hook_text, topic,
              duration_seconds, template, caption_style, datetime.now().isoformat(), source_url))
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Registered published video: id={row_id}, media_id={media_id}")
        return row_id
    
    # ─── Snapshot Updates ─────────────────────────────────────────────────────
    
    def update_snapshot(self, media_id: str, views: int = 0, likes: int = 0,
                        comments: int = 0, shares: int = 0, saves: int = 0,
                        reach: int = 0, impressions: int = 0,
                        watch_time_total: float = 0, watch_time_avg: float = 0,
                        completion_rate: float = 0, profile_visits: int = 0,
                        follows: int = 0, website_clicks: int = 0) -> bool:
        """Store a performance snapshot for a video."""
        conn = _get_db()
        
        # Check if video exists
        row = conn.execute("SELECT id FROM published_videos WHERE media_id=?", (media_id,)).fetchone()
        if not row:
            conn.close()
            logger.warning(f"Video not found: {media_id}")
            return False
        
        conn.execute("""
            INSERT INTO performance_snapshots
            (video_id, media_id, snapshot_time, views, likes, comments, shares, saves,
             reach, impressions, watch_time_total, watch_time_avg, completion_rate,
             profile_visits, follows, website_clicks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (row["id"], media_id, datetime.now().isoformat(), views, likes, comments,
              shares, saves, reach, impressions, watch_time_total, watch_time_avg,
              completion_rate, profile_visits, follows, website_clicks))
        conn.commit()
        conn.close()
        logger.info(f"Snapshot saved: {media_id}, views={views}, likes={likes}")
        return True
    
    # ─── Queries ──────────────────────────────────────────────────────────────
    
    def get_video_performance(self, media_id: str) -> dict:
        """Get latest performance for a single video."""
        conn = _get_db()
        
        row = conn.execute("""
            SELECT p.*, v.niche, v.hook_type, v.hook_text, v.agent_type, v.topic
            FROM performance_snapshots p
            JOIN published_videos v ON p.video_id = v.id
            WHERE p.media_id=?
            ORDER BY p.snapshot_time DESC LIMIT 1
        """, (media_id,)).fetchone()
        
        conn.close()
        if row:
            return dict(row)
        return {}
    
    def get_period_report(self, period: str = "7d") -> dict:
        """
        Get performance report for a period.
        
        Args:
            period: "7d", "30d", "90d", or "all"
        """
        conn = _get_db()
        
        if period == "7d":
            since = (datetime.now() - timedelta(days=7)).isoformat()
        elif period == "30d":
            since = (datetime.now() - timedelta(days=30)).isoformat()
        elif period == "90d":
            since = (datetime.now() - timedelta(days=90)).isoformat()
        else:
            since = "2000-01-01"
        
        # Get all videos with their latest snapshots
        rows = conn.execute("""
            SELECT v.*, 
                   p.views, p.likes, p.comments, p.shares, p.saves,
                   p.reach, p.impressions, p.watch_time_total, p.watch_time_avg,
                   p.completion_rate, p.profile_visits, p.follows, p.website_clicks
            FROM published_videos v
            LEFT JOIN performance_snapshots p ON v.id = p.video_id
            WHERE v.publish_time >= ?
            AND p.id = (
                SELECT MAX(p2.id) FROM performance_snapshots p2 
                WHERE p2.video_id = v.id
            )
        """, (since,)).fetchall()
        
        conn.close()
        
        if not rows:
            return {"period": period, "videos": 0, "message": "No data for this period"}
        
        videos = [dict(r) for r in rows]
        
        total_views = sum(v.get("views", 0) or 0 for v in videos)
        total_reach = sum(v.get("reach", 0) or 0 for v in videos)
        total_interactions = sum(
            (v.get("likes", 0) or 0) + (v.get("comments", 0) or 0) + 
            (v.get("shares", 0) or 0) + (v.get("saves", 0) or 0)
            for v in videos
        )
        
        avg_engagement = total_interactions / len(videos) if videos else 0
        avg_completion = sum(v.get("completion_rate", 0) or 0 for v in videos) / len(videos)
        avg_watch_time = sum(v.get("watch_time_avg", 0) or 0 for v in videos) / len(videos)
        
        # Best/worst
        best = max(videos, key=lambda v: v.get("views", 0) or 0) if videos else None
        worst = min(videos, key=lambda v: v.get("views", 0) or 0) if videos else None
        
        # By niche
        niche_stats = {}
        for v in videos:
            niche = v.get("niche", "unknown")
            if niche not in niche_stats:
                niche_stats[niche] = {"count": 0, "views": 0, "interactions": 0}
            niche_stats[niche]["count"] += 1
            niche_stats[niche]["views"] += v.get("views", 0) or 0
            niche_stats[niche]["interactions"] += (
                (v.get("likes", 0) or 0) + (v.get("comments", 0) or 0) +
                (v.get("shares", 0) or 0) + (v.get("saves", 0) or 0)
            )
        
        # By hook type
        hook_stats = {}
        for v in videos:
            hook = v.get("hook_type", "unknown")
            if hook not in hook_stats:
                hook_stats[hook] = {"count": 0, "views": 0, "interactions": 0}
            hook_stats[hook]["count"] += 1
            hook_stats[hook]["views"] += v.get("views", 0) or 0
            hook_stats[hook]["interactions"] += (
                (v.get("likes", 0) or 0) + (v.get("comments", 0) or 0) +
                (v.get("shares", 0) or 0) + (v.get("saves", 0) or 0)
            )
        
        return {
            "period": period,
            "videos": len(videos),
            "total_views": total_views,
            "total_reach": total_reach,
            "total_interactions": total_interactions,
            "avg_engagement_rate": round(avg_engagement, 2),
            "avg_completion_rate": round(avg_completion, 2),
            "avg_watch_time": round(avg_watch_time, 2),
            "best_performing": {
                "media_id": best.get("media_id") if best else None,
                "hook": best.get("hook_text") if best else None,
                "views": best.get("views", 0) if best else 0,
            } if best else None,
            "worst_performing": {
                "media_id": worst.get("media_id") if worst else None,
                "hook": worst.get("hook_text") if worst else None,
                "views": worst.get("views", 0) if worst else 0,
            } if worst else None,
            "niche_performance": niche_stats,
            "hook_performance": hook_stats,
        }
    
    def get_top_performing(self, limit: int = 10, metric: str = "views") -> list:
        """Get top performing videos."""
        conn = _get_db()
        
        rows = conn.execute("""
            SELECT v.*, p.views, p.likes, p.comments, p.shares, p.saves,
                   p.reach, p.completion_rate, p.watch_time_avg
            FROM published_videos v
            LEFT JOIN performance_snapshots p ON v.id = p.video_id
            WHERE p.id = (
                SELECT MAX(p2.id) FROM performance_snapshots p2 
                WHERE p2.video_id = v.id
            )
            ORDER BY p.{metric} DESC
            LIMIT ?
        """.format(metric=metric), (limit,)).fetchall()
        
        conn.close()
        return [dict(r) for r in rows]
    
    def get_niche_leaderboard(self) -> list:
        """Get niches ranked by total performance."""
        conn = _get_db()
        
        rows = conn.execute("""
            SELECT v.niche,
                   COUNT(DISTINCT v.id) as video_count,
                   SUM(p.views) as total_views,
                   SUM(p.likes + p.comments + p.shares + p.saves) as total_interactions,
                   AVG(p.completion_rate) as avg_completion
            FROM published_videos v
            LEFT JOIN performance_snapshots p ON v.id = p.video_id
            GROUP BY v.niche
            ORDER BY total_interactions DESC
        """).fetchall()
        
        conn.close()
        return [dict(r) for r in rows]
    
    def get_hook_leaderboard(self) -> list:
        """Get hook types ranked by performance."""
        conn = _get_db()
        
        rows = conn.execute("""
            SELECT v.hook_type,
                   COUNT(DISTINCT v.id) as video_count,
                   SUM(p.views) as total_views,
                   SUM(p.likes + p.comments + p.shares + p.saves) as total_interactions,
                   AVG(p.completion_rate) as avg_completion
            FROM published_videos v
            LEFT JOIN performance_snapshots p ON v.id = p.video_id
            WHERE v.hook_type != ''
            GROUP BY v.hook_type
            ORDER BY total_interactions DESC
        """).fetchall()
        
        conn.close()
        return [dict(r) for r in rows]


# ─── Convenience Functions ────────────────────────────────────────────────────

def register_video(video_id: int, media_id: str, **kwargs) -> int:
    """Register a published video."""
    t = PerformanceTracker()
    return t.register_published(video_id, media_id, **kwargs)

def update_stats(media_id: str, **kwargs) -> bool:
    """Update performance stats for a video."""
    t = PerformanceTracker()
    return t.update_snapshot(media_id, **kwargs)

def get_report(period: str = "7d") -> dict:
    """Get performance report."""
    t = PerformanceTracker()
    return t.get_period_report(period)

def get_top(limit: int = 10, metric: str = "views") -> list:
    """Get top performing videos."""
    t = PerformanceTracker()
    return t.get_top_performing(limit, metric)

def get_niche_ranks() -> list:
    """Get niche leaderboard."""
    t = PerformanceTracker()
    return t.get_niche_leaderboard()

def get_hook_ranks() -> list:
    """Get hook leaderboard."""
    t = PerformanceTracker()
    return t.get_hook_leaderboard()
