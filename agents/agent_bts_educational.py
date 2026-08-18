"""
Agent 8: BTS to Educational — Behind-the-scenes → Tutorial
Converts raw BTS footage into educational content.
Full production lifecycle: rights gate → safety gate → dedup → QA → analytics.
"""
import logging
import os
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_bts_educational")

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(bts_video_path: str, niche: str = "tech_ai", tutorial_topic = None) -> dict:
    """
    Convert BTS footage to educational tutorial.

    Steps:
    1. Input validation + rights gate (BTS footage must be authorized)
    2. Safety gate
    3. Transcribe + generate tutorial script
    4. Create video
    5. Dedup check → QA check → analytics
    """
    try:
        from tools.transcriber import transcribe_video
        from engines.content_creator import generate_script_with_ai, get_template_script
        from engines.video_builder import create_text_video
        from tools.tts_engine import text_to_speech
        from tools.video_editor import add_audio_track
        from engines.revenue_tracker import log_video
        from engines.safety_gate import check_safety, get_safety_status
        from engines.dedup_engine import check_duplicate, register_content
        from engines.shared_qa import run_qa
        from engines.content_checker import check_copyright

        logger.info(f"Agent: BTS to Educational | File: {bts_video_path}")

        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")

        # ── 1. Input validation ──────────────────────────────────────────────
        if not bts_video_path or not os.path.exists(bts_video_path):
            return {"success": False, "error": "bts_video_path does not exist"}

        # ── 2. Rights gate ────────────────────────────────────────────────────
        rights = check_copyright(
            title=f"BTS Educational source: {bts_video_path}",
            description="Converting BTS footage to educational tutorial",
        )
        if rights.get("risk_level") == "HIGH":
            return {
                "success": False,
                "error": f"Rights gate BLOCKED: {rights.get('reason', 'high copyright risk')}",
                "rights": rights,
            }
        logger.info(f"Rights gate: {rights.get('risk_level', 'LOW')}")

        # ── 3. Transcribe + generate script ──────────────────────────────────
        topic = tutorial_topic or "How to create content like this"
        trans = transcribe_video(bts_video_path)

        if trans.get("success"):
            script = generate_script_with_ai(topic, niche, duration=45)
        else:
            script = get_template_script(niche)

        full_text = f"{script.get('hook', '')} {script.get('body', '')} {script.get('cta', '')}"

        # ── 4. Safety gate ────────────────────────────────────────────────────
        safety = check_safety(full_text)
        safety_status = get_safety_status(safety)
        if safety_status == "BLOCKED":
            return {
                "success": False,
                "error": f"Safety gate BLOCKED: risk={safety.get('overall_risk', 0)}",
                "safety": safety,
            }
        logger.info(f"Safety: {safety_status} (risk={safety.get('overall_risk', 0):.3f})")

        # ── 5. Create video ───────────────────────────────────────────────────
        audio_path = str(PROCESSED_DIR / f"bts_voiceover_{timestamp}.wav")
        text_to_speech(full_text, audio_path, rate=150)

        video_path = str(PROCESSED_DIR / f"bts_video_{timestamp}.mp4")
        create_text_video(script, video_path)

        final_path = str(PROCESSED_DIR / f"bts_final_{timestamp}.mp4")
        add_audio_track(video_path, audio_path, final_path, volume=0.8)

        # ── 6. Dedup check ────────────────────────────────────────────────────
        dup = check_duplicate(source_url=bts_video_path)
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
            title=script.get("hook", "Tutorial")[:60],
            niche=niche,
            agent_type="bts_educational",
            video_path=final_path,
        )

        register_content(
            video_path=final_path,
            source_url=bts_video_path,
            agent_type="bts_educational",
        )

        return {
            "success": True,
            "topic": topic,
            "video_path": final_path,
            "video_id": video_id,
            "safety_status": safety_status,
            "qa_status": qa["overall"],
        }

    except Exception as e:
        logger.error(f"Agent BTS Educational failed: {e}")
        return {"success": False, "error": str(e)}
