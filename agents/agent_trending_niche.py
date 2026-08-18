"""
Agent 9: Trending Audio — Trending sound + Niche = Viral content
Uses trending TikTok/Reels audio with niche content.
Full production lifecycle: rights gate → safety gate → dedup → QA → analytics.
"""
import logging
import os
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_trending_niche")

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(niche: str = "health_fitness", trending_audio_path = None, hook = None) -> dict:
    """
    Create niche content with trending audio.

    Steps:
    1. Input validation + rights gate (audio must be licensed or platform-supported)
    2. Safety gate
    3. Select topic + generate script
    4. Create video
    5. Dedup check → QA check → analytics
    """
    try:
        from engines.content_creator import generate_script_with_ai
        from engines.niche_selector import select_topic, get_hashtags
        from engines.video_builder import create_text_video
        from tools.tts_engine import text_to_speech
        from tools.video_editor import add_audio_track
        from engines.revenue_tracker import log_video
        from engines.safety_gate import check_safety, get_safety_status
        from engines.dedup_engine import check_duplicate, register_content
        from engines.shared_qa import run_qa
        from engines.content_checker import check_copyright

        logger.info(f"Agent: Trending Audio | Niche: {niche}")

        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")

        # ── 1. Rights gate on audio ───────────────────────────────────────────
        if trending_audio_path:
            if not os.path.exists(trending_audio_path):
                return {"success": False, "error": "trending_audio_path does not exist"}

            rights = check_copyright(
                title=f"Trending audio: {trending_audio_path}",
                description="Using trending audio for niche content",
            )
            if rights.get("risk_level") == "HIGH":
                return {
                    "success": False,
                    "error": f"Rights gate BLOCKED (audio): {rights.get('reason', 'high copyright risk')}",
                    "rights": rights,
                }
            logger.info(f"Audio rights gate: {rights.get('risk_level', 'LOW')}")

        # ── 2. Select topic + generate script ─────────────────────────────────
        topic = select_topic(niche)
        script = generate_script_with_ai(topic, niche, duration=30)

        full_text = f"{script.get('hook', '')} {script.get('body', '')} {script.get('cta', '')}"

        # ── 3. Safety gate ────────────────────────────────────────────────────
        safety = check_safety(full_text)
        safety_status = get_safety_status(safety)
        if safety_status == "BLOCKED":
            return {
                "success": False,
                "error": f"Safety gate BLOCKED: risk={safety.get('overall_risk', 0)}",
                "safety": safety,
            }
        logger.info(f"Safety: {safety_status} (risk={safety.get('overall_risk', 0):.3f})")

        # ── 4. Create video ───────────────────────────────────────────────────
        audio_path = str(PROCESSED_DIR / f"trending_voiceover_{timestamp}.wav")
        text_to_speech(full_text, audio_path, rate=155)

        video_path = str(PROCESSED_DIR / f"trending_video_{timestamp}.mp4")
        create_text_video(script, video_path)

        final_path = str(PROCESSED_DIR / f"trending_final_{timestamp}.mp4")
        audio_to_use = trending_audio_path or audio_path
        add_audio_track(video_path, audio_to_use, final_path, volume=0.8)

        # ── 5. Dedup check ────────────────────────────────────────────────────
        dup = check_duplicate(source_url=trending_audio_path or topic)
        if dup.get("is_duplicate"):
            return {
                "success": False,
                "error": f"Duplicate detected: {dup.get('reason')}",
            }

        # ── 6. QA check ───────────────────────────────────────────────────────
        qa = run_qa(final_path)
        if qa["overall"] == "FAILED":
            return {
                "success": False,
                "error": f"QA failed: {qa['errors']}",
            }

        # ── 7. Analytics + hashtags ───────────────────────────────────────────
        hashtags = get_hashtags(niche)

        video_id = log_video(
            title=script.get("hook", "Trending")[:60],
            niche=niche,
            agent_type="trending_niche",
            video_path=final_path,
        )

        register_content(
            video_path=final_path,
            source_url=trending_audio_path or topic,
            agent_type="trending_niche",
        )

        return {
            "success": True,
            "topic": topic,
            "hashtags": hashtags,
            "video_path": final_path,
            "video_id": video_id,
            "safety_status": safety_status,
            "qa_status": qa["overall"],
        }

    except Exception as e:
        logger.error(f"Agent Trending Niche failed: {e}")
        return {"success": False, "error": str(e)}
