#!/usr/bin/env python3
"""
Dub Flip Source of Truth Auto-Update Script
Runs daily to update the source of truth document with latest data.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
SOURCE_OF_TRUTH = Path(__file__).parent / "dub_flip_SOURCE_OF_TRUTH.md"
METRICS_FILE = BASE_DIR / "data" / "dub_flip_metrics.json"
HISTORY_FILE = BASE_DIR / "data" / "dub_flip_history.json"


def load_metrics() -> dict:
    """Load current metrics from database."""
    try:
        import sqlite3
        db_path = BASE_DIR / "data" / "revenue.db"
        if not db_path.exists():
            return {}
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get Dub Flip statistics
        cursor.execute("""
            SELECT 
                language,
                COUNT(*) as total,
                SUM(CASE WHEN qa_status = 'PASSED' THEN 1 ELSE 0 END) as passed,
                AVG(file_size) as avg_size,
                AVG(duration) as avg_duration
            FROM videos 
            WHERE agent_type = 'dub_flip'
            GROUP BY language
        """)
        
        stats = {}
        for row in cursor.fetchall():
            lang, total, passed, avg_size, avg_duration = row
            stats[lang] = {
                "total": total,
                "passed": passed,
                "pass_rate": (passed / total * 100) if total > 0 else 0,
                "avg_size_kb": avg_size / 1024 if avg_size else 0,
                "avg_duration": avg_duration or 0,
            }
        
        conn.close()
        return stats
        
    except Exception as e:
        print(f"Error loading metrics: {e}")
        return {}


def load_history() -> list:
    """Load update history."""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []


def save_history(history: list):
    """Save update history."""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)


def update_source_of_truth(metrics: dict, history: list):
    """Update the source of truth document with latest data."""
    if not SOURCE_OF_TRUTH.exists():
        print(f"Source of truth not found: {SOURCE_OF_TRUTH}")
        return
    
    # Read current content
    with open(SOURCE_OF_TRUTH, 'r') as f:
        content = f.read()
    
    # Update timestamp
    today = datetime.now().strftime("%Y-%m-%d")
    content = content.replace(
        "Last Updated: 2026-08-19",
        f"Last Updated: {today}"
    )
    
    # Update performance metrics section
    if metrics:
        # Calculate overall metrics
        total_videos = sum(m.get("total", 0) for m in metrics.values())
        total_passed = sum(m.get("passed", 0) for m in metrics.values())
        overall_pass_rate = (total_passed / total_videos * 100) if total_videos > 0 else 0
        
        # Update metrics in document
        old_metrics = """## Target Metrics
| Metric | Target | Current |
|--------|--------|---------|
| Languages per run | 4 | 4 |
| Time per language | < 60s | ~45s |
| Translation accuracy | ≥ 90% | ~85% |
| Audio quality | ≥ 4/5 | ~3.5/5 |
| QA pass rate | ≥ 95% | ~90% |
| Safety pass rate | 100% | 100% |"""
        
        new_metrics = f"""## Target Metrics
| Metric | Target | Current |
|--------|--------|---------|
| Languages per run | 4 | 4 |
| Time per language | < 60s | ~45s |
| Translation accuracy | ≥ 90% | ~85% |
| Audio quality | ≥ 4/5 | ~3.5/5 |
| QA pass rate | ≥ 95% | {overall_pass_rate:.1f}% |
| Safety pass rate | 100% | 100% |
| Total videos | - | {total_videos} |
| Overall pass rate | - | {overall_pass_rate:.1f}% |"""
        
        content = content.replace(old_metrics, new_metrics)
        
        # Add language-specific metrics
        lang_section = "\n## Actual Language Performance\n\n"
        lang_section += "| Language | Total | Passed | Pass Rate | Avg Size | Avg Duration |\n"
        lang_section += "|----------|-------|--------|-----------|----------|--------------|\n"
        
        for lang, data in metrics.items():
            lang_section += f"| {lang} | {data.get('total', 0)} | {data.get('passed', 0)} | {data.get('pass_rate', 0):.1f}% | {data.get('avg_size_kb', 0):.1f} KB | {data.get('avg_duration', 0):.1f}s |\n"
        
        # Find and replace language performance section
        if "## Actual Language Performance" in content:
            start = content.find("## Actual Language Performance")
            end = content.find("\n## ", start + 1)
            if end == -1:
                end = len(content)
            content = content[:start] + lang_section + content[end:]
        else:
            # Add before FUTURE IMPROVEMENTS section
            if "## FUTURE IMPROVEMENTS" in content:
                content = content.replace(
                    "## FUTURE IMPROVEMENTS",
                    lang_section + "\n## FUTURE IMPROVEMENTS"
                )
    
    # Update history
    history.append({
        "date": today,
        "metrics": metrics,
        "updated": True
    })
    
    # Keep only last 30 days
    if len(history) > 30:
        history = history[-30:]
    
    # Save updated document
    with open(SOURCE_OF_TRUTH, 'w') as f:
        f.write(content)
    
    print(f"✅ Source of truth updated: {today}")
    print(f"   - Total videos: {sum(m.get('total', 0) for m in metrics.values())}")
    print(f"   - Languages: {list(metrics.keys())}")
    
    return history


def main():
    """Main update function."""
    print("🔄 Dub Flip Source of Truth Auto-Update")
    print("=" * 50)
    
    # Load current metrics
    metrics = load_metrics()
    print(f"📊 Loaded metrics for {len(metrics)} languages")
    
    # Load history
    history = load_history()
    print(f"📜 Loaded {len(history)} historical updates")
    
    # Update source of truth
    history = update_source_of_truth(metrics, history)
    
    # Save history
    save_history(history)
    
    print("=" * 50)
    print("✅ Update complete!")


if __name__ == "__main__":
    main()
