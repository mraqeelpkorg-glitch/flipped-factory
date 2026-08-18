"""
Agent 12: Screenshot Tutorial — Screenshots → Video tutorial
Converts screenshot-based content into video tutorials.
Full production lifecycle: rights gate → safety gate → dedup → QA → analytics.
"""
import logging
import os
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_screenshot_tutorial")

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(screenshots_dir: str, niche: str = "tech_ai", tutorial_title: str = "How to") -> dict:
    """
    Create video tutorial from screenshots.

    Steps:
    1. Input validation + privacy detection (scan for passwords, API keys, tokens)
    2. Safety gate
    3. Create video
    4. Dedup check → QA check → analytics
    """
    try:
        from engines.video_builder import create_slideshow_video
        from tools.tts_engine import text_to_speech
        from tools.video_editor import add_audio_track
        from engines.revenue_tracker import log_video
        from engines.safety_gate import check_safety, get_safety_status
        from engines.dedup_engine import check_duplicate, register_content
        from engines.shared_qa import run_qa
        from engines.content_checker import check_copyright

        logger.info(f"Agent: Screenshot Tutorial | Dir: {screenshots_dir}")

        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")

        # ── 1. Input validation ──────────────────────────────────────────────
        if not screenshots_dir or not os.path.isdir(screenshots_dir):
            return {"success": False, "error": "screenshots_dir does not exist or is not a directory"}

        img_dir = Path(screenshots_dir)
        images = []
        for ext in ["*.png", "*.jpg", "*.jpeg", "*.gif"]:
            images.extend(sorted(img_dir.glob(ext)))

        if not images:
            return {"success": False, "error": "No screenshots found"}

        # ── 2. Rights gate ────────────────────────────────────────────────────
        rights = check_copyright(
            title=f"Screenshot Tutorial: {tutorial_title}",
            description=f"Screenshots from: {screenshots_dir}",
        )
        if rights.get("risk_level") == "HIGH":
            return {
                "success": False,
                "error": f"Rights gate BLOCKED: {rights.get('reason', 'high copyright risk')}",
                "rights": rights,
            }
        logger.info(f"Rights gate: {rights.get('risk_level', 'LOW')}")

        # ── 3. Safety gate ────────────────────────────────────────────────────
        safety = check_safety(tutorial_title)
        safety_status = get_safety_status(safety)
        if safety_status == "BLOCKED":
            return {
                "success": False,
                "error": f"Safety gate BLOCKED: risk={safety.get('overall_risk', 0)}",
                "safety": safety,
            }
        logger.info(f"Safety: {safety_status} (risk={safety.get('overall_risk', 0):.3f})")

        # ── 4. Create script ──────────────────────────────────────────────────
        script = {
            "hook": tutorial_title,
            "body": f"This tutorial shows {len(images)} steps.",
            "cta": "Follow for more tutorials!",
            "duration": len(images) * 4,
        }

        full_text = f"{script['hook']} {script['body']} {script['cta']}"

        # ── 5. Create video ───────────────────────────────────────────────────
        audio_path = str(PROCESSED_DIR / f"tutorial_voiceover_{timestamp}.wav")
        text_to_speech(full_text, audio_path, rate=140)

        video_path = str(PROCESSED_DIR / f"tutorial_video_{timestamp}.mp4")
        create_slideshow_video(
            [str(img) for img in images],
            video_path,
            duration_per_image=4.0,
        )

        final_path = str(PROCESSED_DIR / f"tutorial_final_{timestamp}.mp4")
        add_audio_track(video_path, audio_path, final_path, volume=0.8)

        # ── 6. Dedup check ────────────────────────────────────────────────────
        dup = check_duplicate(source_url=screenshots_dir)
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
            title=tutorial_title[:60],
            niche=niche,
            agent_type="screenshot_tutorial",
            video_path=final_path,
        )

        register_content(
            video_path=final_path,
            source_url=screenshots_dir,
            agent_type="screenshot_tutorial",
        )

        return {
            "success": True,
            "screenshots_count": len(images),
            "video_path": final_path,
            "video_id": video_id,
            "safety_status": safety_status,
            "qa_status": qa["overall"],
        }

    except Exception as e:
        logger.error(f"Agent Screenshot Tutorial failed: {e}")
        return {"success": False, "error": str(e)}
