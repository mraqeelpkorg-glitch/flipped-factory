"""
A/B Testing Framework — Test different content strategies.

Tests:
- Hook variants (A vs B vs C)
- Caption styles
- Video lengths
- Visual templates
- Publishing times
- CTAs
- Niche angles

Tracks which variant wins based on REAL performance data.
"""

import json
import logging
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("ab_testing")

DATA_DIR = Path(__file__).parent.parent / "data"
AB_DIR = DATA_DIR / "ab_tests"
AB_DIR.mkdir(parents=True, exist_ok=True)

def _get_db():
    db_path = DATA_DIR / "ab_tests.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def init_ab_db():
    """Initialize A/B testing tables."""
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS ab_experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_name TEXT,
            test_type TEXT,
            hypothesis TEXT,
            variants TEXT,
            status TEXT DEFAULT 'draft',
            winning_variant TEXT,
            confidence_score REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            started_at TEXT,
            ended_at TEXT
        );
        
        CREATE TABLE IF NOT EXISTS ab_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER,
            video_id INTEGER,
            media_id TEXT,
            variant_label TEXT,
            variant_config TEXT,
            niche TEXT,
            hook_type TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (experiment_id) REFERENCES ab_experiments(id)
        );
        
        CREATE TABLE IF NOT EXISTS ab_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER,
            variant_label TEXT,
            video_count INTEGER DEFAULT 0,
            total_views INTEGER DEFAULT 0,
            total_interactions INTEGER DEFAULT 0,
            avg_engagement_rate REAL DEFAULT 0,
            avg_completion_rate REAL DEFAULT 0,
            avg_watch_time REAL DEFAULT 0,
            avg_shares REAL DEFAULT 0,
            avg_saves REAL DEFAULT 0,
            is_winner INTEGER DEFAULT 0,
            calculated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (experiment_id) REFERENCES ab_experiments(id)
        );
    """)
    conn.commit()
    conn.close()
    logger.info("A/B testing database initialized")

init_ab_db()


class ABTesting:
    """
    A/B Testing framework for content strategies.
    
    Usage:
        ab = ABTesting()
        exp_id = ab.create_experiment("Hook Test", "hook", "Curiosity beats mistake hooks")
        ab.assign_variant(exp_id, video_id=1, variant="A", config={"hook_type": "curiosity"})
        ab.assign_variant(exp_id, video_id=2, variant="B", config={"hook_type": "mistake"})
        results = ab.calculate_results(exp_id)
        winner = ab.declare_winner(exp_id)
    """
    
    def create_experiment(self, name: str, test_type: str, hypothesis: str,
                          variants: list = None) -> int:
        """
        Create a new A/B experiment.
        
        Args:
            name: Experiment name (e.g., "Hook Family Test #1")
            test_type: "hook", "caption", "length", "template", "time", "cta", "niche"
            hypothesis: What we're testing (e.g., "Curiosity hooks get more shares")
            variants: List of variant labels (e.g., ["A", "B", "C"])
        
        Returns:
            experiment_id
        """
        if variants is None:
            variants = ["A", "B"]
        
        conn = _get_db()
        cursor = conn.execute("""
            INSERT INTO ab_experiments (experiment_name, test_type, hypothesis, variants, status)
            VALUES (?, ?, ?, ?, 'active')
        """, (name, test_type, hypothesis, json.dumps(variants)))
        exp_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Created experiment: {name} (id={exp_id})")
        return exp_id
    
    def assign_variant(self, experiment_id: int, video_id: int, media_id: str,
                       variant: str, config: dict = None, niche: str = "",
                       hook_type: str = "") -> int:
        """Assign a video to an experiment variant."""
        conn = _get_db()
        cursor = conn.execute("""
            INSERT INTO ab_assignments 
            (experiment_id, video_id, media_id, variant_label, variant_config, niche, hook_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (experiment_id, video_id, media_id, variant,
              json.dumps(config or {}), niche, hook_type))
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Assigned video {video_id} to variant {variant} in experiment {experiment_id}")
        return row_id
    
    def calculate_results(self, experiment_id: int) -> dict:
        """
        Calculate results for an experiment based on performance data.
        
        Returns:
            {
                "experiment": {...},
                "variants": [
                    {"label": "A", "video_count": 5, "avg_engagement": 0.05, ...},
                    {"label": "B", "video_count": 5, "avg_engagement": 0.08, ...}
                ],
                "winner": "B",
                "confidence": 0.85
            }
        """
        conn = _get_db()
        
        # Get experiment
        exp = conn.execute("SELECT * FROM ab_experiments WHERE id=?", (experiment_id,)).fetchone()
        if not exp:
            conn.close()
            return {"error": "Experiment not found"}
        
        exp = dict(exp)
        variants = json.loads(exp.get("variants", "[]"))
        
        # Get all assignments
        assignments = conn.execute(
            "SELECT * FROM ab_assignments WHERE experiment_id=?", (experiment_id,)
        ).fetchall()
        
        # For each variant, get performance data
        variant_results = []
        
        for variant_label in variants:
            variant_assignments = [
                dict(a) for a in assignments if a["variant_label"] == variant_label
            ]
            
            if not variant_assignments:
                variant_results.append({
                    "label": variant_label, "video_count": 0,
                    "message": "No videos assigned"
                })
                continue
            
            # Get performance for each video
            total_views = 0
            total_interactions = 0
            total_completion = 0
            total_watch_time = 0
            total_shares = 0
            total_saves = 0
            video_count = 0
            
            for assignment in variant_assignments:
                media_id = assignment["media_id"]
                
                # Query performance
                perf = conn.execute("""
                    SELECT p.* FROM performance_snapshots p
                    WHERE p.media_id=?
                    ORDER BY p.snapshot_time DESC LIMIT 1
                """, (media_id,)).fetchone()
                
                if perf:
                    perf = dict(perf)
                    total_views += perf.get("views", 0) or 0
                    total_shares += perf.get("shares", 0) or 0
                    total_saves += perf.get("saves", 0) or 0
                    total_interactions += (
                        (perf.get("likes", 0) or 0) + (perf.get("comments", 0) or 0) +
                        (perf.get("shares", 0) or 0) + (perf.get("saves", 0) or 0)
                    )
                    total_completion += perf.get("completion_rate", 0) or 0
                    total_watch_time += perf.get("watch_time_avg", 0) or 0
                    video_count += 1
            
            avg_engagement = total_interactions / max(total_views, 1)
            avg_completion = total_completion / max(video_count, 1)
            avg_watch = total_watch_time / max(video_count, 1)
            avg_shares = total_shares / max(video_count, 1)
            avg_saves = total_saves / max(video_count, 1)
            
            variant_results.append({
                "label": variant_label,
                "video_count": video_count,
                "total_views": total_views,
                "total_interactions": total_interactions,
                "avg_engagement_rate": round(avg_engagement, 4),
                "avg_completion_rate": round(avg_completion, 3),
                "avg_watch_time": round(avg_watch, 2),
                "avg_shares": round(avg_shares, 1),
                "avg_saves": round(avg_saves, 1),
            })
        
        # Determine winner (highest engagement rate with minimum data)
        valid_variants = [v for v in variant_results if v.get("video_count", 0) >= 2]
        winner = None
        confidence = 0
        
        if valid_variants:
            best = max(valid_variants, key=lambda v: v.get("avg_engagement_rate", 0))
            runner_up = sorted(valid_variants, key=lambda v: v.get("avg_engagement_rate", 0), reverse=True)
            
            if len(runner_up) >= 2:
                best_rate = best.get("avg_engagement_rate", 0)
                second_rate = runner_up[1].get("avg_engagement_rate", 0)
                
                if best_rate > 0 and second_rate > 0:
                    improvement = (best_rate - second_rate) / second_rate
                    confidence = min(0.95, 0.5 + (improvement * 2) + (best["video_count"] * 0.05))
                else:
                    confidence = 0.6
            else:
                confidence = 0.6
            
            winner = best["label"]
        
        # Save results
        for vr in variant_results:
            conn.execute("""
                INSERT INTO ab_results 
                (experiment_id, variant_label, video_count, total_views, total_interactions,
                 avg_engagement_rate, avg_completion_rate, avg_watch_time, avg_shares, avg_saves, is_winner)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (experiment_id, vr["label"], vr.get("video_count", 0),
                  vr.get("total_views", 0), vr.get("total_interactions", 0),
                  vr.get("avg_engagement_rate", 0), vr.get("avg_completion_rate", 0),
                  vr.get("avg_watch_time", 0), vr.get("avg_shares", 0),
                  vr.get("avg_saves", 0), 1 if vr["label"] == winner else 0))
        
        # Update experiment
        conn.execute("""
            UPDATE ab_experiments 
            SET winning_variant=?, confidence_score=?
            WHERE id=?
        """, (winner, confidence, experiment_id))
        
        conn.commit()
        conn.close()
        
        return {
            "experiment": exp,
            "variants": variant_results,
            "winner": winner,
            "confidence": round(confidence, 2),
            "calculated_at": datetime.now().isoformat(),
        }
    
    def declare_winner(self, experiment_id: int) -> dict:
        """Declare the winner and close the experiment."""
        results = self.calculate_results(experiment_id)
        
        if results.get("error"):
            return results
        
        conn = _get_db()
        conn.execute("""
            UPDATE ab_experiments 
            SET status='completed', ended_at=?
            WHERE id=?
        """, (datetime.now().isoformat(), experiment_id))
        conn.commit()
        conn.close()
        
        logger.info(
            f"Experiment {experiment_id} completed: winner={results.get('winner')}, "
            f"confidence={results.get('confidence')}"
        )
        
        return {
            "experiment_id": experiment_id,
            "winner": results.get("winner"),
            "confidence": results.get("confidence"),
            "status": "completed",
        }
    
    def get_active_experiments(self) -> list:
        """Get all active experiments."""
        conn = _get_db()
        rows = conn.execute(
            "SELECT * FROM ab_experiments WHERE status='active' ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    
    def get_completed_experiments(self) -> list:
        """Get all completed experiments with winners."""
        conn = _get_db()
        rows = conn.execute(
            "SELECT * FROM ab_experiments WHERE status='completed' ORDER BY ended_at DESC"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    
    def get_recommendation(self) -> dict:
        """Get recommendation based on all completed experiments."""
        completed = self.get_completed_experiments()
        
        recommendations = []
        for exp in completed:
            if exp.get("winning_variant"):
                recommendations.append({
                    "experiment": exp["experiment_name"],
                    "test_type": exp["test_type"],
                    "hypothesis": exp["hypothesis"],
                    "winner": exp["winning_variant"],
                    "confidence": exp["confidence_score"],
                })
        
        return {
            "total_experiments": len(completed),
            "recommendations": recommendations,
        }


# ─── Convenience ──────────────────────────────────────────────────────────────

def create_test(name: str, test_type: str, hypothesis: str, variants: list = None) -> int:
    ab = ABTesting()
    return ab.create_experiment(name, test_type, hypothesis, variants)

def assign(exp_id: int, video_id: int, media_id: str, variant: str, **kwargs) -> int:
    ab = ABTesting()
    return ab.assign_variant(exp_id, video_id, media_id, variant, **kwargs)

def results(exp_id: int) -> dict:
    ab = ABTesting()
    return ab.calculate_results(exp_id)

def get_recommendation() -> dict:
    ab = ABTesting()
    return ab.get_recommendation()
