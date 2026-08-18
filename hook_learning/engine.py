"""
Hook Learning Engine — Track hook performance, learn what works.

Responsibilities:
1. Record hook experiments (which hook was used for which content)
2. Track performance metrics (views, likes, shares, comments)
3. Identify winning hooks (high engagement)
4. Identify losing hooks (low engagement)
5. Generate recommendations for future hooks
6. Persist to hook_learning/ directory

The system learns from its own content performance.
"""
import json
import os
import logging
from pathlib import Path
from datetime import datetime, date
from collections import defaultdict

logger = logging.getLogger("hook_learning")

LEARNING_DIR = Path(__file__).parent
LEARNING_DIR.mkdir(parents=True, exist_ok=True)

WINNERS_FILE = LEARNING_DIR / "winners.json"
LOSERS_FILE = LEARNING_DIR / "losers.json"
EXPERIMENTS_FILE = LEARNING_DIR / "experiments.json"
RECOMMENDATIONS_FILE = LEARNING_DIR / "recommendations.json"


def record_experiment(
    hook_text: str,
    hook_pattern: str,
    niche: str,
    agent_type: str,
    video_id: int = None,
    video_path: str = "",
) -> dict:
    """
    Record a hook experiment.
    
    Returns the experiment record.
    """
    experiments = _load_json(EXPERIMENTS_FILE, [])
    
    experiment = {
        "id": len(experiments) + 1,
        "hook_text": hook_text,
        "hook_pattern": hook_pattern,
        "niche": niche,
        "agent_type": agent_type,
        "video_id": video_id,
        "video_path": video_path,
        "created_at": datetime.now().isoformat(),
        "metrics": {
            "views": 0,
            "likes": 0,
            "shares": 0,
            "comments": 0,
            "saves": 0,
            "engagement_rate": 0.0,
        },
        "status": "active",
    }
    
    experiments.append(experiment)
    _save_json(EXPERIMENTS_FILE, experiments)
    
    logger.info(f"Hook experiment recorded: #{experiment['id']} — {hook_text[:50]}")
    return experiment


def update_metrics(experiment_id: int, metrics: dict) -> dict:
    """
    Update metrics for an experiment.
    
    metrics = {
        "views": 1000,
        "likes": 50,
        "shares": 10,
        "comments": 5,
        "saves": 20,
    }
    """
    experiments = _load_json(EXPERIMENTS_FILE, [])
    
    for exp in experiments:
        if exp["id"] == experiment_id:
            exp["metrics"].update(metrics)
            
            # Calculate engagement rate
            views = exp["metrics"].get("views", 0)
            if views > 0:
                engagement = (
                    exp["metrics"].get("likes", 0) +
                    exp["metrics"].get("shares", 0) +
                    exp["metrics"].get("comments", 0) +
                    exp["metrics"].get("saves", 0)
                ) / views
                exp["metrics"]["engagement_rate"] = round(engagement, 4)
            
            _save_json(EXPERIMENTS_FILE, experiments)
            logger.info(f"Metrics updated for experiment #{experiment_id}")
            return exp
    
    logger.warning(f"Experiment #{experiment_id} not found")
    return {}


def get_performance_summary() -> dict:
    """
    Get performance summary across all experiments.
    
    Returns:
    - total_experiments
    - avg_engagement_rate
    - best_hooks: top 5 by engagement
    - worst_hooks: bottom 5 by engagement
    - by_pattern: performance grouped by hook pattern
    - by_niche: performance grouped by niche
    """
    experiments = _load_json(EXPERIMENTS_FILE, [])
    
    if not experiments:
        return {
            "total_experiments": 0,
            "avg_engagement_rate": 0,
            "best_hooks": [],
            "worst_hooks": [],
            "by_pattern": {},
            "by_niche": {},
        }
    
    # Sort by engagement rate
    scored = [e for e in experiments if e["metrics"].get("views", 0) > 0]
    scored.sort(key=lambda e: e["metrics"].get("engagement_rate", 0), reverse=True)
    
    # Average engagement
    avg_engagement = (
        sum(e["metrics"].get("engagement_rate", 0) for e in scored) / len(scored)
        if scored else 0
    )
    
    # By pattern
    by_pattern = defaultdict(list)
    for e in scored:
        by_pattern[e.get("hook_pattern", "unknown")].append(e)
    
    pattern_stats = {}
    for pattern, exps in by_pattern.items():
        avg = sum(e["metrics"]["engagement_rate"] for e in exps) / len(exps)
        pattern_stats[pattern] = {
            "count": len(exps),
            "avg_engagement": round(avg, 4),
        }
    
    # By niche
    by_niche = defaultdict(list)
    for e in scored:
        by_niche[e.get("niche", "unknown")].append(e)
    
    niche_stats = {}
    for niche, exps in by_niche.items():
        avg = sum(e["metrics"]["engagement_rate"] for e in exps) / len(exps)
        niche_stats[niche] = {
            "count": len(exps),
            "avg_engagement": round(avg, 4),
        }
    
    return {
        "total_experiments": len(experiments),
        "total_with_metrics": len(scored),
        "avg_engagement_rate": round(avg_engagement, 4),
        "best_hooks": [_summarize_hook(e) for e in scored[:5]],
        "worst_hooks": [_summarize_hook(e) for e in scored[-5:]],
        "by_pattern": pattern_stats,
        "by_niche": niche_stats,
    }


def identify_winners(threshold: float = 0.05) -> list:
    """
    Identify winning hooks (engagement rate >= threshold).
    Default threshold: 5% engagement rate.
    """
    experiments = _load_json(EXPERIMENTS_FILE, [])
    
    winners = []
    for e in experiments:
        if e["metrics"].get("engagement_rate", 0) >= threshold:
            winners.append(_summarize_hook(e))
    
    # Save winners
    _save_json(WINNERS_FILE, winners)
    
    logger.info(f"Identified {len(winners)} winning hooks (threshold={threshold})")
    return winners


def identify_losers(threshold: float = 0.01) -> list:
    """
    Identify losing hooks (engagement rate <= threshold and has views).
    Default threshold: 1% engagement rate.
    """
    experiments = _load_json(EXPERIMENTS_FILE, [])
    
    losers = []
    for e in experiments:
        views = e["metrics"].get("views", 0)
        engagement = e["metrics"].get("engagement_rate", 0)
        if views > 100 and engagement <= threshold:
            losers.append(_summarize_hook(e))
    
    # Save losers
    _save_json(LOSERS_FILE, losers)
    
    logger.info(f"Identified {len(losers)} losing hooks (threshold={threshold})")
    return losers


def generate_recommendations() -> list:
    """
    Generate hook recommendations based on performance data.
    
    Returns list of recommendations:
    - best_pattern: which hook pattern works best
    - best_niche: which niche gets highest engagement
    - avoid: patterns/niches to avoid
    - suggestions: specific hook templates to try
    """
    summary = get_performance_summary()
    winners = identify_winners()
    losers = identify_losers()
    
    recommendations = []
    
    # Best pattern
    if summary["by_pattern"]:
        best_pattern = max(summary["by_pattern"].items(), key=lambda x: x[1]["avg_engagement"])
        recommendations.append({
            "type": "best_pattern",
            "pattern": best_pattern[0],
            "avg_engagement": best_pattern[1]["avg_engagement"],
            "action": f"Use '{best_pattern[0]}' hooks more often",
        })
    
    # Best niche
    if summary["by_niche"]:
        best_niche = max(summary["by_niche"].items(), key=lambda x: x[1]["avg_engagement"])
        recommendations.append({
            "type": "best_niche",
            "niche": best_niche[0],
            "avg_engagement": best_niche[1]["avg_engagement"],
            "action": f"Focus on '{best_niche[0]}' niche",
        })
    
    # Avoid patterns
    if summary["by_pattern"]:
        worst_pattern = min(summary["by_pattern"].items(), key=lambda x: x[1]["avg_engagement"])
        if worst_pattern[1]["avg_engagement"] < 0.02:
            recommendations.append({
                "type": "avoid_pattern",
                "pattern": worst_pattern[0],
                "avg_engagement": worst_pattern[1]["avg_engagement"],
                "action": f"Reduce '{worst_pattern[0]}' hooks",
            })
    
    # Winning hook examples
    if winners:
        recommendations.append({
            "type": "winning_hooks",
            "examples": [w["hook_text"] for w in winners[:3]],
            "action": "Model future hooks after these winners",
        })
    
    # Save recommendations
    _save_json(RECOMMENDATIONS_FILE, {
        "generated_at": datetime.now().isoformat(),
        "recommendations": recommendations,
        "summary": summary,
    })
    
    logger.info(f"Generated {len(recommendations)} recommendations")
    return recommendations


def _summarize_hook(experiment: dict) -> dict:
    """Create a summary of a hook experiment."""
    return {
        "id": experiment["id"],
        "hook_text": experiment["hook_text"],
        "hook_pattern": experiment.get("hook_pattern", "unknown"),
        "niche": experiment.get("niche", "unknown"),
        "agent_type": experiment.get("agent_type", "unknown"),
        "engagement_rate": experiment["metrics"].get("engagement_rate", 0),
        "views": experiment["metrics"].get("views", 0),
        "likes": experiment["metrics"].get("likes", 0),
        "shares": experiment["metrics"].get("shares", 0),
        "created_at": experiment.get("created_at", ""),
    }


def _load_json(filepath: Path, default):
    """Load JSON file, return default if not found."""
    if filepath.exists():
        try:
            with open(filepath) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return default
    return default


def _save_json(filepath: Path, data):
    """Save data to JSON file."""
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    # Demo
    exp1 = record_experiment(
        hook_text="Did you know 85% of marketers use short-form video?",
        hook_pattern="question",
        niche="tech_ai",
        agent_type="youtube_clipper",
    )
    exp2 = record_experiment(
        hook_text="This changes everything about fitness",
        hook_pattern="shock",
        niche="health_fitness",
        agent_type="podcast_clipper",
    )
    
    update_metrics(exp1["id"], {"views": 1000, "likes": 80, "shares": 20, "comments": 10})
    update_metrics(exp2["id"], {"views": 500, "likes": 10, "shares": 2, "comments": 1})
    
    summary = get_performance_summary()
    print(json.dumps(summary, indent=2))
    
    recs = generate_recommendations()
    print(json.dumps(recs, indent=2))
