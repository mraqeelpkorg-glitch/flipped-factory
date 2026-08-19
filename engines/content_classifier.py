"""
Content Classifier — Automatic agent selection for Flipped Factory.

Analyzes source content and determines which of the12 agents should handle it.
Returns agent type, confidence, reason, and any missing inputs.

Classification signals:
- URL pattern (youtube.com, podcast platforms, blog URLs, etc.)
- Content metadata (title, description, duration)
- Transcript analysis (speech vs text vs screenshots)
- File type (video, audio, images, text)
"""
import logging
import re
from typing import Optional

logger = logging.getLogger("content_classifier")

# ─── Agent Definitions ────────────────────────────────────────────────────────

AGENTS = {
    "youtube_clipper": {
        "name": "YouTube Clipper",
        "description": "YouTube video → Instagram Reels",
        "required_inputs": ["youtube_url"],
        "optional_inputs": ["niche", "max_clips", "language"],
        "signals": ["youtube.com", "youtu.be", "video tutorial", "explainer"],
    },
    "podcast_clipper": {
        "name": "Podcast Clipper",
        "description": "Podcast/interview → Clips with TTS",
        "required_inputs": ["source"],
        "optional_inputs": ["max_clips", "niche"],
        "signals": ["podcast", "interview", "spotify.com", "apple.com/podcast", "audio"],
    },
    "blog_to_video": {
        "name": "Blog to Video",
        "description": "Blog post/article → Video",
        "required_inputs": ["blog_url_or_text"],
        "optional_inputs": ["niche", "language"],
        "signals": ["blog", "article", "medium.com", "substack", "wordpress"],
    },
    "remix_flip": {
        "name": "Remix Flip",
        "description": "Re-edit content with new hook",
        "required_inputs": ["video_path"],
        "optional_inputs": ["niche", "hook_style"],
        "signals": ["remix", "re-edit", "new version", "remake"],
    },
    "dub_flip": {
        "name": "Dub Flip",
        "description": "Multi-language video versions",
        "required_inputs": ["video_path"],
        "optional_inputs": ["languages", "niche"],
        "signals": ["translate", "dub", "multi-language", "hindi", "spanish"],
    },
    "data_to_video": {
        "name": "Data to Video",
        "description": "Research/stats → Infographic Reel",
        "required_inputs": ["niche"],
        "optional_inputs": ["data_points", "statistics"],
        "signals": ["data", "statistics", "research", "study", "survey"],
    },
    "product_compilation": {
        "name": "Product Compilation",
        "description": "Product showcase/comparison Reel",
        "required_inputs": ["niche"],
        "optional_inputs": ["products"],
        "signals": ["product", "review", "comparison", "best", "top"],
    },
    "bts_educational": {
        "name": "BTS Educational",
        "description": "Behind-the-scenes → Tutorial",
        "required_inputs": ["bts_video_path"],
        "optional_inputs": ["niche"],
        "signals": ["behind the scenes", "bts", "tutorial", "how to make"],
    },
    "trending_niche": {
        "name": "Trending Audio",
        "description": "Trending audio + topic Reel",
        "required_inputs": ["niche"],
        "optional_inputs": ["trend_topic"],
        "signals": ["trending", "viral", "challenge", "audio"],
    },
    "course_teaser": {
        "name": "Course Teaser",
        "description": "Course preview clip",
        "required_inputs": ["course_module"],
        "optional_inputs": ["niche"],
        "signals": ["course", "lesson", "module", "preview", "teaser"],
    },
    "live_highlights": {
        "name": "Live Highlights",
        "description": "Livestream → Highlight clips",
        "required_inputs": ["live_video_path"],
        "optional_inputs": ["niche"],
        "signals": ["live", "stream", "twitch", "livestream"],
    },
    "screenshot_tutorial": {
        "name": "Screenshot Tutorial",
        "description": "Screenshots → Video tutorial",
        "required_inputs": ["screenshots_dir"],
        "optional_inputs": ["niche"],
        "signals": ["screenshot", "screen capture", "software", "app"],
    },
}


def classify_source(
    url: str = "",
    text: str = "",
    video_path: str = "",
    metadata: dict = None,
) -> dict:
    """
    Classify a source and determine the best agent.
    
    Returns:
        {
            "agent_type": str,
            "agent_name": str,
            "confidence": float (0-1),
            "reason": str,
            "signals": list,
            "missing_inputs": list,
            "all_matches": list,  # all agents that matched, sorted by confidence
        }
    """
    metadata = metadata or {}
    scores = {}
    
    # ── URL-based signals ──────────────────────────────────────────────────
    url_lower = url.lower()
    
    if any(x in url_lower for x in ["youtube.com", "youtu.be"]):
        scores["youtube_clipper"] = scores.get("youtube_clipper", 0) + 0.8
        scores["youtube_clipper"] = min(scores["youtube_clipper"], 1.0)
    
    if any(x in url_lower for x in ["spotify.com", "apple.com/podcast", "podcasts"]):
        scores["podcast_clipper"] = scores.get("podcast_clipper", 0) + 0.8
    
    if any(x in url_lower for x in ["medium.com", "substack", "wordpress", ".blog"]):
        scores["blog_to_video"] = scores.get("blog_to_video", 0) + 0.8
    
    if any(x in url_lower for x in ["twitch.tv", "live"]):
        scores["live_highlights"] = scores.get("live_highlights", 0) + 0.6
    
    # ── Text-based signals ─────────────────────────────────────────────────
    text_lower = (text + " " + " ".join(metadata.values()) if isinstance(metadata, dict) else text).lower()
    
    signal_keywords = {
        "youtube_clipper": ["youtube", "video", "tutorial", "explainer", "how to"],
        "podcast_clipper": ["podcast", "interview", "conversation", "episode"],
        "blog_to_video": ["blog", "article", "post", "written", "read"],
        "remix_flip": ["remix", "re-edit", "new version", "remake", "reimagine"],
        "dub_flip": ["translate", "dub", "multi-language", "hindi", "spanish", "arabic"],
        "data_to_video": ["data", "statistics", "research", "study", "survey", "numbers"],
        "product_compilation": ["product", "review", "comparison", "best", "top 10", "buy"],
        "bts_educational": ["behind the scenes", "bts", "making of", "process"],
        "trending_niche": ["trending", "viral", "challenge", "trend", "hot"],
        "course_teaser": ["course", "lesson", "module", "preview", "teaser", "learn"],
        "live_highlights": ["live", "stream", "broadcast", "highlight"],
        "screenshot_tutorial": ["screenshot", "screen", "software", "app", "step by step"],
    }
    
    for agent_type, keywords in signal_keywords.items():
        for kw in keywords:
            if kw in text_lower:
                scores[agent_type] = scores.get(agent_type, 0) + 0.3
    
    # ── File-based signals ─────────────────────────────────────────────────
    if video_path:
        if video_path.lower().endswith(('.mp4', '.mov', '.avi', '.webm')):
            scores["remix_flip"] = scores.get("remix_flip", 0) + 0.3
            scores["dub_flip"] = scores.get("dub_flip", 0) + 0.2
    
    # ── Metadata signals ───────────────────────────────────────────────────
    if metadata:
        title = metadata.get("title", "").lower()
        if "podcast" in title:
            scores["podcast_clipper"] = scores.get("podcast_clipper", 0) + 0.4
        if "interview" in title:
            scores["podcast_clipper"] = scores.get("podcast_clipper", 0) + 0.3
        if "tutorial" in title:
            scores["youtube_clipper"] = scores.get("youtube_clipper", 0) + 0.3
    
    # ── Determine winner ───────────────────────────────────────────────────
    if not scores:
        return {
            "agent_type": None,
            "agent_name": "Unknown",
            "confidence": 0.0,
            "reason": "No matching signals found",
            "signals": [],
            "missing_inputs": [],
            "all_matches": [],
        }
    
    # Sort by score
    sorted_agents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_agent, best_score = sorted_agents[0]
    
    # Normalize confidence
    confidence = min(best_score, 1.0)
    
    # Check required inputs
    agent_def = AGENTS.get(best_agent, {})
    required = agent_def.get("required_inputs", [])
    missing = []
    
    # Map common input names
    input_map = {
        "youtube_url": url if url and ("youtube" in url.lower() or "youtu.be" in url.lower()) else "",
        "source": url or video_path,
        "blog_url_or_text": url or text,
        "video_path": video_path,
        "bts_video_path": video_path,
        "live_video_path": video_path,
        "screenshots_dir": metadata.get("screenshots_dir", ""),
        "course_module": metadata.get("course_module", ""),
        "niche": metadata.get("niche", ""),
    }
    
    for req in required:
        if not input_map.get(req):
            missing.append(req)
    
    # Build reason
    top_signals = []
    for agent, score in sorted_agents[:3]:
        agent_signals = []
        for kw in signal_keywords.get(agent, []):
            if kw in text_lower or kw in url_lower:
                agent_signals.append(kw)
        if agent_signals:
            top_signals.append(f"{agent}: {', '.join(agent_signals[:3])}")
    
    reason = f"Best match: {best_agent} (confidence: {confidence:.0%}). "
    if top_signals:
        reason += f"Signals: {'; '.join(top_signals)}"
    if missing:
        reason += f" Missing inputs: {', '.join(missing)}"
    
    # All matches
    all_matches = [
        {"agent": a, "confidence": min(s, 1.0)}
        for a, s in sorted_agents
        if s > 0
    ]
    
    return {
        "agent_type": best_agent,
        "agent_name": agent_def.get("name", best_agent),
        "confidence": confidence,
        "reason": reason,
        "signals": [s for s, _ in sorted_agents if _ > 0],
        "missing_inputs": missing,
        "all_matches": all_matches,
    }


def classify_from_url(url: str) -> dict:
    """Quick classification from URL only."""
    return classify_source(url=url)


def classify_from_video(video_path: str, metadata: dict = None) -> dict:
    """Quick classification from local video file."""
    return classify_source(video_path=video_path, metadata=metadata)


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    result = classify_from_url(url)
    print(f"\nAgent: {result['agent_name']} ({result['agent_type']})")
    print(f"Confidence: {result['confidence']:.0%}")
    print(f"Reason: {result['reason']}")
    print(f"Missing inputs: {result['missing_inputs']}")
    print(f"All matches: {result['all_matches']}")
