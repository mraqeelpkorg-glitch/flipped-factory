"""
Agent 1: YouTube Clipper — YouTube → Instagram Reels
Downloads YouTube video, extracts best clips, crops to vertical.
Full production lifecycle: rights gate → safety gate → dedup → QA → analytics.
"""
import logging
import os
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_youtube_clipper")

RAW_DIR = Path(__file__).parent.parent / "data" / "videos" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(youtube_url: str, niche: str = "health_fitness", max_clips: int = 3) -> dict:
    """
    Download YouTube video and create Instagram-ready vertical clips.

    Steps:
    1. Input validation + rights gate (check YouTube source metadata)
    2. Download video
    3. Safety gate on transcript
    4. Transcribe + find best segments
    5. Create clips with dedup + QA
    6. Analytics
    """
    try:
        from tools.downloader import download_video
        from tools.transcriber import transcribe_video
        from tools.video_editor import crop_to_vertical, trim_video
        from engines.revenue_tracker import log_video
        from engines.safety_gate import check_safety, get_safety_status
        from engines.dedup_engine import check_duplicate, register_content
        from engines.shared_qa import run_qa
        from engines.content_checker import check_copyright

        logger.info(f"Agent: YouTube Clipper | URL: {youtube_url}")

        RAW_DIR.mkdir(parents=True, exist_ok=True)
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")

        # ── 1. Input validation ──────────────────────────────────────────────
        if not youtube_url or not youtube_url.startswith("http"):
            return {"success": False, "error": "youtube_url must be a valid URL"}

        # ── 2. Rights gate (BEFORE downloading) ───────────────────────────────
        rights = check_copyright(
            title=f"YouTube source: {youtube_url}",
            description="Clipping YouTube content for Instagram Reels",
        )
        if rights.get("risk_level") == "HIGH":
            return {
                "success": False,
                "error": f"Rights gate BLOCKED: {rights.get('reason', 'high copyright risk')}",
                "rights": rights,
            }
        logger.info(f"Rights gate: {rights.get('risk_level', 'LOW')}")

        # ── 3. Download video ─────────────────────────────────────────────────
        dl_result = download_video(youtube_url)
        if not dl_result.get("success"):
            return {"success": False, "error": f"Download failed: {dl_result.get('error')}"}

        video_path = dl_result["path"]
        title = dl_result.get("title", "YouTube Clip")

        # ── 4. Transcribe ─────────────────────────────────────────────────────
        trans_result = transcribe_video(video_path)

        # ── 5. Safety gate on transcript ──────────────────────────────────────
        if trans_result.get("success"):
            transcript_text = trans_result.get("text", "")
            safety = check_safety(transcript_text)
            safety_status = get_safety_status(safety)
            if safety_status == "BLOCKED":
                return {
                    "success": False,
                    "error": f"Safety gate BLOCKED: risk={safety.get('overall_risk', 0)}",
                    "safety": safety,
                }
            logger.info(f"Safety: {safety_status} (risk={safety.get('overall_risk', 0):.3f})")
        else:
            safety_status = "APPROVED"

        # ── 6. Create clips ───────────────────────────────────────────────────
        clips_created = []
        errors = []

        if trans_result.get("success") and trans_result.get("segments"):
            segments = trans_result["segments"]
            scored_segments = sorted(segments, key=lambda s: len(s["text"].split()), reverse=True)

            for i, seg in enumerate(scored_segments[:max_clips]):
                try:
                    start = seg["start"]
                    end = min(seg["end"], start + 60)

                    # Dedup check per segment
                    dup = check_duplicate(
                        source_url=youtube_url,
                        segment_start=start,
                        segment_end=end,
                    )
                    if dup.get("is_duplicate"):
                        logger.warning(f"Segment duplicate: {start}-{end}")
                        errors.append({"segment": f"{start}-{end}", "error": "duplicate"})
                        continue

                    clip_name = f"yt_clip_{i+1}_{timestamp}.mp4"
                    clip_path = str(PROCESSED_DIR / clip_name)

                    success = trim_video(video_path, clip_path, start, end)
                    if not success:
                        errors.append({"segment": f"{start}-{end}", "error": "trim_failed"})
                        continue

                    vertical_path = str(PROCESSED_DIR / f"vertical_{clip_name}")
                    crop_to_vertical(clip_path, vertical_path)

                    # QA check
                    qa = run_qa(vertical_path)
                    if qa["overall"] == "FAILED":
                        errors.append({"segment": f"{start}-{end}", "error": f"qa_failed: {qa['errors']}"})
                        continue

                    video_id = log_video(
                        title=f"{title} - Clip {i+1}",
                        niche=niche,
                        agent_type="youtube_clipper",
                        video_path=vertical_path,
                    )

                    register_content(
                        video_path=vertical_path,
                        source_url=youtube_url,
                        segment_start=start,
                        segment_end=end,
                        transcript=seg["text"],
                        agent_type="youtube_clipper",
                    )

                    clips_created.append({
                        "path": vertical_path,
                        "text": seg["text"],
                        "duration": end - start,
                        "video_id": video_id,
                        "safety_status": safety_status,
                        "qa_status": qa["overall"],
                    })

                except Exception as e:
                    logger.error(f"Error creating clip {i}: {e}")
                    errors.append({"segment": f"{seg['start']}-{seg['end']}", "error": str(e)})
        else:
            # Fallback: crop the whole video
            clip_name = f"yt_clip_full_{timestamp}.mp4"
            clip_path = str(PROCESSED_DIR / clip_name)
            crop_to_vertical(video_path, clip_path)

            qa = run_qa(clip_path)
            if qa["overall"] == "FAILED":
                return {"success": False, "error": f"QA failed on full clip: {qa['errors']}"}

            video_id = log_video(
                title=f"{title} - Full",
                niche=niche,
                agent_type="youtube_clipper",
                video_path=clip_path,
            )

            register_content(
                video_path=clip_path,
                source_url=youtube_url,
                agent_type="youtube_clipper",
            )

            clips_created.append({
                "path": clip_path,
                "video_id": video_id,
                "safety_status": safety_status,
                "qa_status": qa["overall"],
            })

        return {
            "success": len(clips_created) > 0,
            "source_title": title,
            "clips_count": len(clips_created),
            "clips": clips_created,
            "errors": errors,
            "source_safety": safety_status,
        }

    except Exception as e:
        logger.error(f"Agent YouTube Clipper failed: {e}")
        return {"success": False, "error": str(e)}
