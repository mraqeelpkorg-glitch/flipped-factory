"""
Agent 4: Remix Flip — Re-edit old content with fresh hook
Takes existing video, adds new hook/intro, remixes.
Full production lifecycle: rights gate → safety gate → dedup → QA → analytics.
"""
import logging
import os
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_remix_flip")

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(video_path: str, niche: str = "motivation", new_hook = None) -> dict:
    """
    Remix an existing video with a fresh hook.

    Steps:
    1. Input validation + rights gate (source must be authorized)
    2. Safety gate
    3. Generate new hook
    4. Create hook intro + combine
    5. Dedup check → QA check → analytics
    """
    try:
        from engines.content_creator import get_template_script
        from engines.video_builder import create_text_video
        from tools.video_editor import concat_videos
        from engines.revenue_tracker import log_video
        from engines.safety_gate import check_safety, get_safety_status
        from engines.dedup_engine import check_duplicate, register_content
        from engines.shared_qa import run_qa
        from engines.content_checker import check_copyright

        logger.info(f"Agent: Remix Flip | Video: {video_path}")

        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")

        # ── 1. Input validation ──────────────────────────────────────────────
        if not video_path or not os.path.exists(video_path):
            return {"success": False, "error": "video_path does not exist"}

        # ── 2. Rights gate ────────────────────────────────────────────────────
        rights = check_copyright(
            title=f"Remix Flip source: {video_path}",
            description="Re-editing existing video with new hook",
        )
        if rights.get("risk_level") == "HIGH":
            return {
                "success": False,
                "error": f"Rights gate BLOCKED: {rights.get('reason', 'high copyright risk')}",
                "rights": rights,
            }
        logger.info(f"Rights gate: {rights.get('risk_level', 'LOW')}")

        # ── 3. Safety gate ────────────────────────────────────────────────────
        safety_text = new_hook or "safe content"
        safety = check_safety(safety_text)
        safety_status = get_safety_status(safety)
        if safety_status == "BLOCKED":
            return {
                "success": False,
                "error": f"Safety gate BLOCKED: risk={safety.get('overall_risk', 0)}",
                "safety": safety,
            }
        logger.info(f"Safety: {safety_status} (risk={safety.get('overall_risk', 0):.3f})")

        # ── 4. Generate new hook ──────────────────────────────────────────────
        if not new_hook:
            script = get_template_script(niche)
            new_hook = script.get("hook", "Check this out!")

        hook_script = {
            "hook": new_hook,
            "body": "",
            "cta": "",
            "duration": 5,
        }

        # ── 5. Create hook intro + combine ────────────────────────────────────
        hook_video = str(PROCESSED_DIR / f"remix_hook_{timestamp}.mp4")
        create_text_video(hook_script, hook_video)

        final_path = str(PROCESSED_DIR / f"remix_final_{timestamp}.mp4")
        concat_videos([hook_video, video_path], final_path)

        # ── 6. Dedup check ────────────────────────────────────────────────────
        dup = check_duplicate(source_url=video_path)
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
            title=new_hook[:60],
            niche=niche,
            agent_type="remix_flip",
            video_path=final_path,
        )

        register_content(
            video_path=final_path,
            source_url=video_path,
            agent_type="remix_flip",
        )

        return {
            "success": True,
            "new_hook": new_hook,
            "video_path": final_path,
            "video_id": video_id,
            "safety_status": safety_status,
            "qa_status": qa["overall"],
        }

    except Exception as e:
        logger.error(f"Agent Remix Flip failed: {e}")
        return {"success": False, "error": str(e)}
