"""
Real Hook Learning Engine — Learn from ACTUAL Instagram performance data.

Unlike the experimental hook_learning engine, this one uses REAL data from:
- Instagram Graph API analytics
- Performance tracker snapshots
- Actual views, shares, saves, completion rates

Learns:
- Which hook TYPES perform best (curiosity, mistake, contradiction, etc.)
- Which SPECIFIC hooks perform best
- Which hooks work best per NICHE
- Which hooks work best per LENGTH
- Hook patterns that go viral vs fail
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict

logger = logging.getLogger("real_hook_learning")

DATA_DIR = Path(__file__).parent.parent / "data"
LEARNING_DIR = DATA_DIR / "hook_learning_real"
LEARNING_DIR.mkdir(parents=True, exist_ok=True)

# Hook families (same as master document)
HOOK_FAMILIES = [
    "curiosity", "mistake", "contradiction", "insight",
    "story", "before_after", "question", "specific_value"
]


class RealHookLearner:
    """
    Learn hook performance from REAL Instagram data.
    
    Usage:
        learner = RealHookLearner()
        learner.ingest_performance_data()  # pulls from performance_tracker DB
        report = learner.get_hook_report()
        winning = learner.get_winning_hooks()
    """
    
    def __init__(self):
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        LEARNING_DIR.mkdir(parents=True, exist_ok=True)
    
    # ─── Data Ingestion ───────────────────────────────────────────────────────
    
    def ingest_performance_data(self) -> dict:
        """
        Pull data from performance_tracker and analyze hook performance.
        
        Returns:
            {
                "total_videos": int,
                "hook_family_stats": {...},
                "specific_hook_stats": {...},
                "niche_hook_stats": {...},
                "updated_at": str
            }
        """
        from engines.performance_tracker import PerformanceTracker
        
        tracker = PerformanceTracker()
        
        # Get all published videos with their latest performance
        import sqlite3
        db_path = DATA_DIR / "performance.db"
        if not db_path.exists():
            logger.warning("No performance database found")
            return {"total_videos": 0, "message": "No data"}
        
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        
        rows = conn.execute("""
            SELECT v.*, 
                   p.views, p.likes, p.comments, p.shares, p.saves,
                   p.reach, p.completion_rate, p.watch_time_avg, p.watch_time_total
            FROM published_videos v
            LEFT JOIN performance_snapshots p ON v.id = p.video_id
            WHERE p.id = (
                SELECT MAX(p2.id) FROM performance_snapshots p2 
                WHERE p2.video_id = v.id
            )
        """).fetchall()
        
        conn.close()
        
        if not rows:
            logger.info("No performance data to ingest")
            return {"total_videos": 0}
        
        videos = [dict(r) for r in rows]
        
        # ─── Analyze by hook family ───────────────────────────────────────────
        family_stats = defaultdict(lambda: {
            "count": 0, "total_views": 0, "total_shares": 0,
            "total_saves": 0, "total_interactions": 0,
            "avg_completion": 0, "avg_watch_time": 0
        })
        
        specific_hook_stats = defaultdict(lambda: {
            "count": 0, "total_views": 0, "total_shares": 0,
            "total_saves": 0, "total_interactions": 0,
            "avg_completion": 0, "hook_type": ""
        })
        
        niche_hook_stats = defaultdict(lambda: defaultdict(lambda: {
            "count": 0, "total_views": 0, "total_interactions": 0
        }))
        
        for v in videos:
            hook_type = v.get("hook_type", "unknown")
            hook_text = (v.get("hook_text", "") or "")[:100]
            niche = v.get("niche", "unknown")
            views = v.get("views", 0) or 0
            likes = v.get("likes", 0) or 0
            comments = v.get("comments", 0) or 0
            shares = v.get("shares", 0) or 0
            saves = v.get("saves", 0) or 0
            completion = v.get("completion_rate", 0) or 0
            watch_time = v.get("watch_time_avg", 0) or 0
            
            interactions = likes + comments + shares + saves
            
            # Family stats
            fs = family_stats[hook_type]
            fs["count"] += 1
            fs["total_views"] += views
            fs["total_shares"] += shares
            fs["total_saves"] += saves
            fs["total_interactions"] += interactions
            fs["avg_completion"] += completion
            fs["avg_watch_time"] += watch_time
            
            # Specific hook stats
            if hook_text:
                hs = specific_hook_stats[hook_text]
                hs["count"] += 1
                hs["total_views"] += views
                hs["total_shares"] += shares
                hs["total_saves"] += saves
                hs["total_interactions"] += interactions
                hs["avg_completion"] += completion
                hs["hook_type"] = hook_type
            
            # Niche + hook stats
            nh = niche_hook_stats[niche][hook_type]
            nh["count"] += 1
            nh["total_views"] += views
            nh["total_interactions"] += interactions
        
        # Calculate averages
        for family, stats in family_stats.items():
            if stats["count"] > 0:
                stats["avg_completion"] = round(stats["avg_completion"] / stats["count"], 3)
                stats["avg_watch_time"] = round(stats["avg_watch_time"] / stats["count"], 2)
                stats["avg_interactions"] = round(stats["total_interactions"] / stats["count"], 1)
                stats["engagement_rate"] = round(
                    stats["total_interactions"] / max(stats["total_views"], 1), 4
                )
        
        for hook_text, stats in specific_hook_stats.items():
            if stats["count"] > 0:
                stats["avg_completion"] = round(stats["avg_completion"] / stats["count"], 3)
                stats["avg_interactions"] = round(stats["total_interactions"] / stats["count"], 1)
                stats["engagement_rate"] = round(
                    stats["total_interactions"] / max(stats["total_views"], 1), 4
                )
        
        result = {
            "total_videos": len(videos),
            "hook_family_stats": dict(family_stats),
            "specific_hook_stats": dict(specific_hook_stats),
            "niche_hook_stats": {k: dict(v) for k, v in niche_hook_stats.items()},
            "updated_at": datetime.now().isoformat(),
        }
        
        # Save
        self._save_learning(result)
        
        logger.info(f"Hook learning ingested: {len(videos)} videos, {len(family_stats)} families")
        return result
    
    # ─── Queries ──────────────────────────────────────────────────────────────
    
    def get_winning_hooks(self, top_n: int = 10) -> list:
        """Get the top performing hooks by engagement rate."""
        learning = self._load_learning()
        hooks = learning.get("specific_hook_stats", [])
        
        # Sort by engagement_rate
        sorted_hooks = sorted(
            hooks.items(),
            key=lambda x: x[1].get("engagement_rate", 0),
            reverse=True
        )
        
        return [
            {"hook_text": h[0], **h[1]}
            for h in sorted_hooks[:top_n]
        ]
    
    def get_losing_hooks(self, bottom_n: int = 10) -> list:
        """Get the worst performing hooks."""
        learning = self._load_learning()
        hooks = learning.get("specific_hook_stats", [])
        
        sorted_hooks = sorted(
            hooks.items(),
            key=lambda x: x[1].get("engagement_rate", 0)
        )
        
        return [
            {"hook_text": h[0], **h[1]}
            for h in sorted_hooks[:bottom_n]
            if h[1].get("count", 0) >= 2  # At least 2 uses
        ]
    
    def get_winning_families(self) -> list:
        """Get hook families ranked by performance."""
        learning = self._load_learning()
        families = learning.get("hook_family_stats", {})
        
        sorted_families = sorted(
            families.items(),
            key=lambda x: x[1].get("engagement_rate", 0),
            reverse=True
        )
        
        return [
            {"family": f[0], **f[1]}
            for f in sorted_families
        ]
    
    def get_niche_hook_recommendations(self, niche: str) -> dict:
        """Get best hook type for a specific niche."""
        learning = self._load_learning()
        niche_hooks = learning.get("niche_hook_stats", {}).get(niche, {})
        
        if not niche_hooks:
            return {"niche": niche, "recommendation": "No data yet", "top_hooks": []}
        
        sorted_hooks = sorted(
            niche_hooks.items(),
            key=lambda x: x[1].get("total_interactions", 0),
            reverse=True
        )
        
        return {
            "niche": niche,
            "top_hooks": [
                {"hook_type": h[0], **h[1]}
                for h in sorted_hooks
            ],
            "recommendation": sorted_hooks[0][0] if sorted_hooks else "unknown",
        }
    
    def get_hook_report(self) -> dict:
        """Get comprehensive hook performance report."""
        learning = self._load_learning()
        
        families = self.get_winning_families()
        top_hooks = self.get_winning_hooks(20)
        losing = self.get_losing_hooks(10)
        
        # Generate recommendations
        recommendations = []
        
        if families:
            best_family = families[0]
            worst_family = families[-1] if len(families) > 1 else None
            
            recommendations.append(
                f"Best performing hook family: {best_family['family']} "
                f"({best_family.get('engagement_rate', 0):.2%} engagement rate, "
                f"{best_family['count']} videos)"
            )
            
            if worst_family and worst_family.get("count", 0) >= 3:
                recommendations.append(
                    f"Worst performing hook family: {worst_family['family']} "
                    f"({worst_family.get('engagement_rate', 0):.2%} engagement rate) "
                    f"— consider reducing usage"
                )
        
        if losing:
            recommendations.append(
                f"Avoid these hooks: {', '.join([h['hook_text'][:50] for h in losing[:3]])}"
            )
        
        return {
            "total_videos_analyzed": learning.get("total_videos", 0),
            "families_ranked": families,
            "top_hooks": top_hooks,
            "losing_hooks": losing,
            "recommendations": recommendations,
            "updated_at": learning.get("updated_at", "never"),
        }
    
    # ─── Storage ──────────────────────────────────────────────────────────────
    
    def _save_learning(self, data: dict):
        filepath = LEARNING_DIR / "hook_learning_real.json"
        filepath.write_text(json.dumps(data, indent=2, default=str))
    
    def _load_learning(self) -> dict:
        filepath = LEARNING_DIR / "hook_learning_real.json"
        if filepath.exists():
            return json.loads(filepath.read_text())
        return {"total_videos": 0, "hook_family_stats": {}, "specific_hook_stats": {}}


# ─── Convenience ──────────────────────────────────────────────────────────────

def ingest_data() -> dict:
    learner = RealHookLearner()
    return learner.ingest_performance_data()

def get_report() -> dict:
    learner = RealHookLearner()
    return learner.get_hook_report()

def get_winning() -> list:
    learner = RealHookLearner()
    return learner.get_winning_hooks()

def get_losing() -> list:
    learner = RealHookLearner()
    return learner.get_losing_hooks()

def get_recommendations(niche: str = None) -> dict:
    learner = RealHookLearner()
    if niche:
        return learner.get_niche_hook_recommendations(niche)
    return learner.get_hook_report()
