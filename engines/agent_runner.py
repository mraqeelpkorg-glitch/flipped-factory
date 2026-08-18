"""
Agent Runner — Wraps ALL 12 agents with production lifecycle.

Every agent gets: job tracking, checkpoint, dedup, QA, safety, scheduling.
No agent changes needed — runner wraps existing run() functions.
"""
import logging
import time
from pathlib import Path

logger = logging.getLogger("agent_runner")

AGENT_MODULES = {
    "youtube_clipper": "agents.agent_youtube_clipper",
    "podcast_clipper": "agents.agent_podcast_clipper",
    "blog_to_video": "agents.agent_blog_to_video",
    "remix_flip": "agents.agent_remix_flip",
    "dub_flip": "agents.agent_dub_flip",
    "data_to_video": "agents.agent_data_to_video",
    "product_compilation": "agents.agent_product_compilation",
    "bts_educational": "agents.agent_bts_educational",
    "trending_niche": "agents.agent_trending_niche",
    "course_teaser": "agents.agent_course_teaser",
    "live_highlights": "agents.agent_live_highlights",
    "screenshot_tutorial": "agents.agent_screenshot_tutorial",
}


def run_agent(agent_type: str, auto_publish: bool = False, **kwargs) -> dict:
    """
    Run any agent with full production lifecycle.

    Usage:
        result = run_agent("youtube_clipper", youtube_url="...", niche="tech")
        result = run_agent("podcast_clipper", source="...", max_clips=3)
    """
    from engines.job_manager import (
        create_job, start_job, complete_job, fail_job,
        save_checkpoint, load_checkpoint, start_stage, complete_stage, fail_stage,
        build_output, add_artifact,
    )
    from engines.dedup_engine import check_duplicate, register_content
    from engines.shared_qa import run_qa
    from engines.scheduler import queue_for_publishing

    # 1. Create job
    job_id = create_job(agent_type, input_params=kwargs)
    start_job(job_id)

    try:
        # 2. Load checkpoint for resume
        checkpoint = load_checkpoint(job_id)
        if checkpoint and checkpoint.get("stage") == "completed":
            logger.info(f"Job {job_id} already completed, skipping")
            return build_output(success=True, metadata={"job_id": job_id, "resumed": True})

        # 3. Import agent module
        module_path = AGENT_MODULES.get(agent_type)
        if not module_path:
            raise ValueError(f"Unknown agent type: {agent_type}")

        import importlib
        mod = importlib.import_module(module_path)

        # 4. Run the agent
        start_stage(job_id, "agent_execution", stage_order=1, input_data=kwargs)
        t0 = time.time()

        result = mod.run(**kwargs)

        duration = time.time() - t0
        complete_stage(job_id, "agent_execution", output_data={"duration": duration})

        if not result.get("success"):
            fail_job(job_id, result.get("error", "Agent returned success=False"), can_retry=True)
            return build_output(success=False, error=result.get("error", "Agent failed"), metadata={"job_id": job_id})

        # 5. Dedup check (for video-based agents)
        video_path = result.get("video_path", "")
        clips = result.get("clips", [])

        if video_path:
            _process_content(job_id, agent_type, video_path, "", auto_publish, result)
        elif clips:
            for clip in clips:
                cp = clip if isinstance(clip, dict) else {"video_path": clip}
                _process_content(job_id, agent_type, cp.get("video_path", ""), cp.get("source_url", ""), auto_publish, result)

        # 6. Complete job
        complete_job(job_id, output=result, video_id=result.get("video_id"))
        result["job_id"] = job_id
        return result

    except Exception as e:
        logger.error(f"Job {job_id} exception: {e}")
        fail_job(job_id, str(e), can_retry=False)
        return build_output(success=False, error=str(e), metadata={"job_id": job_id})


def _process_content(job_id, agent_type, video_path, source_url, auto_publish, result):
    """Run QA + dedup + schedule on a single content piece."""
    from engines.dedup_engine import check_duplicate, check_video_hash, register_content
    from engines.shared_qa import run_qa
    from engines.scheduler import queue_for_publishing
    from engines.job_manager import start_stage, complete_stage, fail_stage, add_artifact

    if not video_path or not Path(video_path).exists():
        return

    # Safety check (CRITICAL - must run before dedup and QA)
    from engines.safety_gate import check_safety, get_safety_status
    start_stage(job_id, "safety_check", stage_order=2)
    # Extract text from result for safety checking
    safety_text = result.get("caption", "") or " ".join(result.get("hashtags", [])) or "safe content"
    safety = check_safety(safety_text)
    status = get_safety_status(safety)
    if status == "BLOCKED":
        fail_stage(job_id, "safety_check", f"Safety blocked: overall_risk={safety.get('overall_risk', 0)}")
        logger.warning(f"Safety blocked: {video_path} — risk={safety.get('overall_risk', 0)}")
        return
    complete_stage(job_id, "safety_check", output_data={"status": status, "overall_risk": safety.get("overall_risk", 0)})

    # Dedup
    start_stage(job_id, "dedup_check", stage_order=3)
    dup = check_video_hash(video_path)
    if dup.get("is_duplicate"):
        fail_stage(job_id, "dedup_check", f"Duplicate: {dup.get('reason')}")
        logger.warning(f"Duplicate skipped: {video_path}")
        return
    complete_stage(job_id, "dedup_check", output_data={"duplicate": False})

    # QA
    start_stage(job_id, "qa_check", stage_order=4)
    qa = run_qa(video_path)
    if qa["overall"] == "FAILED":
        fail_stage(job_id, "qa_check", f"QA failed: {qa['errors']}")
        logger.warning(f"QA failed: {video_path}")
        return
    complete_stage(job_id, "qa_check", output_data={"overall": qa["overall"], "errors": qa["errors"]})

    # Register content
    register_content(
        video_path=video_path,
        source_url=source_url,
        agent_type=agent_type,
        job_id=job_id,
    )
    add_artifact(job_id, video_path, "video")

    # Queue for publishing
    start_stage(job_id, "queue_publish", stage_order=5)
    caption = result.get("caption", "")
    hashtags = result.get("hashtags", [])
    queue_for_publishing(
        video_path=video_path,
        caption=caption,
        hashtags=hashtags,
        agent_type=agent_type,
        job_id=job_id,
        auto_approve=auto_publish,
    )
    complete_stage(job_id, "queue_publish")
    logger.info(f"Queued: {video_path} (qa={qa['overall']})")


def get_available_agents() -> list:
    """Get list of available agents."""
    return [
        {"id": k, "module": v}
        for k, v in AGENT_MODULES.items()
    ]
