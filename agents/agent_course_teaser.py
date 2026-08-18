"""
Agent 10: Course Teaser — Course content → Free preview clip
Creates teaser clips from course content.
Full production lifecycle: rights gate → safety gate → dedup → QA → analytics.
"""
import logging
import os
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_course_teaser")

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(course_module: str, niche: str = "education", course_name: str = "My Course") -> dict:
    """
    Create free teaser from course content.

    Steps:
    1. Input validation + rights gate (course material must be authorized)
    2. Safety gate on course text
    3. Generate teaser script
    4. Create video
    5. Dedup check → QA check → analytics
    """
    try:
        from engines.content_creator import generate_script_with_ai
        from engines.video_builder import create_text_video
        from tools.tts_engine import text_to_speech
        from tools.video_editor import add_audio_track
        from engines.revenue_tracker import log_video
        from engines.safety_gate import check_safety, get_safety_status
        from engines.dedup_engine import check_duplicate, register_content
        from engines.shared_qa import run_qa
        from engines.content_checker import check_copyright

        logger.info(f"Agent: Course Teaser | Module: {course_module[:50] if course_module else 'empty'}")

        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")

        # ── 1. Input validation ──────────────────────────────────────────────
        if not course_module or not course_module.strip():
            return {"success": False, "error": "course_module must not be empty"}

        if len(course_module.strip()) < 10:
            return {"success": False, "error": "course_module too short (min 10 chars)"}

        # ── 2. Rights gate ────────────────────────────────────────────────────
        rights = check_copyright(
            title=f"Course Teaser: {course_name}",
            description=course_module[:200],
        )
        if rights.get("risk_level") == "HIGH":
            return {
                "success": False,
                "error": f"Rights gate BLOCKED: {rights.get('reason', 'high copyright risk')}",
                "rights": rights,
            }
        logger.info(f"Rights gate: {rights.get('risk_level', 'LOW')}")

        # ── 3. Safety gate ────────────────────────────────────────────────────
        safety = check_safety(course_module)
        safety_status = get_safety_status(safety)
        if safety_status == "BLOCKED":
            return {
                "success": False,
                "error": f"Safety gate BLOCKED: risk={safety.get('overall_risk', 0)}",
                "safety": safety,
            }
        logger.info(f"Safety: {safety_status} (risk={safety.get('overall_risk', 0):.3f})")

        # ── 4. Generate teaser script ─────────────────────────────────────────
        script = generate_script_with_ai(course_module, niche, duration=45)
        script["cta"] = "Full course link in bio! Follow for free tips!"

        full_text = f"{script.get('hook', '')} {script.get('body', '')} {script.get('cta', '')}"

        # Safety check on generated script
        script_safety = check_safety(full_text)
        script_status = get_safety_status(script_safety)
        if script_status == "BLOCKED":
            return {
                "success": False,
                "error": f"Script blocked by safety gate: risk={script_safety.get('overall_risk', 0)}",
            }

        # ── 5. Create video ───────────────────────────────────────────────────
        audio_path = str(PROCESSED_DIR / f"teaser_voiceover_{timestamp}.wav")
        text_to_speech(full_text, audio_path, rate=150)

        video_path = str(PROCESSED_DIR / f"teaser_video_{timestamp}.mp4")
        create_text_video(script, video_path)

        final_path = str(PROCESSED_DIR / f"teaser_final_{timestamp}.mp4")
        add_audio_track(video_path, audio_path, final_path, volume=0.8)

        # ── 6. Dedup check ────────────────────────────────────────────────────
        dup = check_duplicate(source_url=course_name)
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
            title=script.get("hook", "Course Teaser")[:60],
            niche=niche,
            agent_type="course_teaser",
            video_path=final_path,
        )

        # Register content
        register_content(
            video_path=final_path,
            source_url=course_name,
            agent_type="course_teaser",
        )

        return {
            "success": True,
            "course_name": course_name,
            "video_path": final_path,
            "video_id": video_id,
            "safety_status": script_status,
            "qa_status": qa["overall"],
        }

    except Exception as e:
        logger.error(f"Agent Course Teaser failed: {e}")
        return {"success": False, "error": str(e)}
