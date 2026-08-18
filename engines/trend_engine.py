"""
Trend Engine — Detects trending topics across platforms.
FREE: pytrends (Google Trends), web scraping
"""
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger("trend_engine")

# ─── Google Trends (FREE) ─────────────────────────────────────────────────────
def fetch_google_trends(keywords: list[str], timeframe: str = "now 7-d") -> dict:
    """Fetch trend scores from Google Trends. Returns {keyword: score}."""
    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 30), retries=2)
        pytrends.build_payload(keywords[:5], timeframe=timeframe, geo="")
        df = pytrends.interest_over_time()

        scores = {}
        if not df.empty:
            for kw in keywords[:5]:
                if kw in df.columns:
                    scores[kw] = max(1, int(df[kw].mean()))
        return scores
    except Exception as e:
        logger.warning(f"Google Trends fetch failed: {e}")
        return {kw: 50 for kw in keywords[:5]}  # Fallback scores


def fetch_niche_trends(niche_keywords: dict) -> dict:
    """Fetch trends for all niches. Returns {niche: {keyword: score}}."""
    results = {}
    for niche, keywords in niche_keywords.items():
        logger.info(f"Fetching trends for niche: {niche}")
        scores = fetch_google_trends(keywords)
        avg_score = sum(scores.values()) // max(len(scores), 1)
        results[niche] = {
            "keywords": scores,
            "average_score": avg_score,
            "top_keyword": max(scores, key=scores.get) if scores else keywords[0],
            "fetched_at": datetime.now().isoformat(),
        }
    return results


# ─── Trend Scoring ────────────────────────────────────────────────────────────
def calculate_trend_score(niche_data: dict) -> float:
    """Calculate weighted trend score for a niche."""
    base_score = niche_data.get("average_score", 50)
    recency = 1.0
    fetched = niche_data.get("fetched_at", "")
    if fetched:
        try:
            dt = datetime.fromisoformat(fetched)
            hours_old = (datetime.now() - dt).total_seconds() / 3600
            recency = max(0.5, 1.0 - (hours_old / 48))  # Decay over 48 hours
        except Exception:
            pass
    return base_score * recency


def rank_niches(trend_data: dict) -> list[dict]:
    """Rank niches by trend score. Returns sorted list."""
    ranked = []
    for niche, data in trend_data.items():
        score = calculate_trend_score(data)
        ranked.append({
            "niche": niche,
            "score": round(score, 2),
            "top_keyword": data.get("top_keyword", ""),
            "keywords": data.get("keywords", {}),
        })
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked


# ─── Persistence ──────────────────────────────────────────────────────────────
TRENDS_FILE = Path(__file__).parent.parent / "data" / "trends.json"

def save_trends(data: dict):
    TRENDS_FILE.write_text(json.dumps(data, indent=2))

def load_trends() -> dict:
    if TRENDS_FILE.exists():
        return json.loads(TRENDS_FILE.read_text())
    return {}


# ─── Main ─────────────────────────────────────────────────────────────────────
def refresh_trends(niche_keywords: dict) -> dict:
    """Full trend refresh cycle."""
    logger.info("Starting trend refresh...")
    data = fetch_niche_trends(niche_keywords)
    save_trends(data)
    ranked = rank_niches(data)
    logger.info(f"Top niche: {ranked[0]['niche']} (score: {ranked[0]['score']})" if ranked else "No niches")
    return {"trends": data, "ranked": ranked}
