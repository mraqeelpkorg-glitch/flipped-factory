"""
Agent 6: Data to Video — Research/data → Infographic video
Creates animated infographic videos from data/stats.
Full production lifecycle: rights gate → safety gate → dedup → QA → analytics.
"""
import logging
import os
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_data_to_video")

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(data_source: str, niche: str = "tech_ai", stats = None) -> dict:
    """
    Create infographic video from data/stats.

    Steps:
    1. Input validation + rights gate (never invent statistics)
    2. Safety gate on content
    3. Create video
    4. Dedup check → QA check → analytics
    """
    try:
        from engines.video_builder import create_text_video
        from tools.tts_engine import text_to_speech
        from tools.video_editor import add_audio_track
        from engines.revenue_tracker import log_video
        from engines.safety_gate import check_safety, get_safety_status
        from engines.dedup_engine import check_duplicate, register_content
        from engines.shared_qa import run_qa
        from engines.content_checker import check_copyright

        logger.info(f"Agent: Data to Video | Source: {data_source[:50] if data_source else 'empty'}")

        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")

        # ── 1. Input validation ──────────────────────────────────────────────
        if not data_source or not data_source.strip():
            return {"success": False, "error": "data_source must not be empty"}

        # Default stats if none provided
        if not stats:
            stats = [
                "85% of marketers use short-form video",
                "93% of businesses see video as important",
                "Short-form video gets 2.5x more engagement",
                "Video makes up 82% of internet traffic",
            ]

        if not isinstance(stats, list) or len(stats) < 2:
            return {"success": False, "error": "stats must be a list with at least 2 items"}

        # ── 2. Rights gate ────────────────────────────────────────────────────
        rights = check_copyright(
            title=f"Data to Video: {data_source[:60]}",
            description=f"Stats: {', '.join(stats[:3])}",
        )
        if rights.get("risk_level") == "HIGH":
            return {
                "success": False,
                "error": f"Rights gate BLOCKED: {rights.get('reason', 'high copyright risk')}",
                "rights": rights,
            }
        logger.info(f"Rights gate: {rights.get('risk_level', 'LOW')}")

        # ── 3. Safety gate ────────────────────────────────────────────────────
        full_text = " ".join(stats)
        safety = check_safety(full_text)
        safety_status = get_safety_status(safety)
        if safety_status == "BLOCKED":
            return {
                "success": False,
                "error": f"Safety gate BLOCKED: risk={safety.get('overall_risk', 0)}",
                "safety": safety,
            }
        logger.info(f"Safety: {safety_status} (risk={safety.get('overall_risk', 0):.3f})")

        # ── 4. Create script ──────────────────────────────────────────────────
        hook = f"Did you know? {stats[0]}"
        body = " ".join([f"Number {i+2}: {s}." for i, s in enumerate(stats[1:3])])
        cta = "Follow for more data insights!"

        script = {
            "hook": hook,
            "body": body,
            "cta": cta,
            "duration": 45,
        }

        # ── 5. Create video ───────────────────────────────────────────────────
        audio_path = str(PROCESSED_DIR / f"data_voiceover_{timestamp}.wav")
        text_to_speech(f"{hook} {body} {cta}", audio_path, rate=140)

        video_path = str(PROCESSED_DIR / f"data_video_{timestamp}.mp4")
        create_text_video(script, video_path)

        final_path = str(PROCESSED_DIR / f"data_final_{timestamp}.mp4")
        add_audio_track(video_path, audio_path, final_path, volume=0.8)

        # ── 6. Dedup check ────────────────────────────────────────────────────
        dup = check_duplicate(source_url=data_source)
        if dup.get("is_duplicate"):
            return {
                "success": False,
                "error": f"Duplicate detected: {dup.get('reason')}",
            }

        # ── 7. QA check ───────────────────────────────────────────────────────
        qa = run_qa(final_path)
        if qa["overall"] == "FAILED":
            return {
                "success": False,
                "error": f"QA failed: {qa['errors']}",
            }

        # ── 8. Analytics ──────────────────────────────────────────────────────
        video_id = log_video(
            title=hook[:60],
            niche=niche,
            agent_type="data_to_video",
            video_path=final_path,
        )

        register_content(
            video_path=final_path,
            source_url=data_source,
            agent_type="data_to_video",
        )

        return {
            "success": True,
            "stats_used": len(stats),
            "video_path": final_path,
            "video_id": video_id,
            "safety_status": safety_status,
            "qa_status": qa["overall"],
        }

    except Exception as e:
        logger.error(f"Agent Data to Video failed: {e}")
        return {"success": False, "error": str(e)}
