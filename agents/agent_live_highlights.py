"""
Agent 11: Live Highlights — Live stream → Highlight clips
Extracts best moments from live streams.
Full production lifecycle: rights gate → safety gate → dedup → QA → analytics.
"""
import logging
import os
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_live_highlights")

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(live_video_path: str, niche: str = "motivation", max_clips: int = 5) -> dict:
    """
    Extract highlights from live stream recording.

    Steps:
    1. Input validation + rights gate (livestream must be authorized)
    2. Safety gate
    3. Transcribe + find best moments
    4. Extract clips
    5. Dedup check → QA check → analytics
    """
    try:
        from tools.transcriber import transcribe_video
        from tools.video_editor import trim_video, crop_to_vertical
        from engines.revenue_tracker import log_video
        from engines.safety_gate import check_safety, get_safety_status
        from engines.dedup_engine import check_duplicate, register_content
        from engines.shared_qa import run_qa
        from engines.content_checker import check_copyright

        logger.info(f"Agent: Live Highlights | File: {live_video_path}")

        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")

        # ── 1. Input validation ──────────────────────────────────────────────
        if not live_video_path or not os.path.exists(live_video_path):
            return {"success": False, "error": "live_video_path does not exist"}

        # ── 2. Rights gate ────────────────────────────────────────────────────
        rights = check_copyright(
            title=f"Live Highlights source: {live_video_path}",
            description="Extracting highlights from livestream",
        )
        if rights.get("risk_level") == "HIGH":
            return {
                "success": False,
                "error": f"Rights gate BLOCKED: {rights.get('reason', 'high copyright risk')}",
                "rights": rights,
            }
        logger.info(f"Rights gate: {rights.get('risk_level', 'LOW')}")

        # ── 3. Transcribe (optional — fall back to silence detection) ─────────
        trans = transcribe_video(live_video_path)
        segments = trans.get("segments", [])
        transcript_text = trans.get("text", "")
        
        if not trans.get("success") or not segments:
            # Fallback: extract a segment using FFmpeg silence/noise detection
            logger.info("Transcription unavailable — using time-based extraction")
            import subprocess, json as _json
            try:
                r = subprocess.run(
                    ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", live_video_path],
                    capture_output=True, text=True, timeout=15,
                )
                duration = float(_json.loads(r.stdout).get("format", {}).get("duration", 30))
                # Take the middle third as a "highlight"
                start_t = duration * 0.33
                end_t = min(start_t + 30, duration * 0.67)
                segments = [{"start": start_t, "end": end_t, "text": "Live highlight segment"}]
            except Exception as e:
                logger.warning(f"Duration probe failed: {e}")
                segments = [{"start": 0, "end": 30, "text": "Live highlight segment"}]

        # ── 4. Safety gate on transcript ──────────────────────────────────────
        safety = check_safety(transcript_text)
        safety_status = get_safety_status(safety)
        if safety_status == "BLOCKED":
            return {
                "success": False,
                "error": f"Safety gate BLOCKED: risk={safety.get('overall_risk', 0)}",
                "safety": safety,
            }
        logger.info(f"Safety: {safety_status} (risk={safety.get('overall_risk', 0):.3f})")

        # ── 5. Find best moments + extract clips ─────────────────────────────
        scored = sorted(segments, key=lambda s: len(s["text"].split()), reverse=True)

        clips_created = []
        errors = []

        for i, seg in enumerate(scored[:max_clips]):
            try:
                clip_name = f"live_highlight_{i+1}_{timestamp}.mp4"
                clip_path = str(PROCESSED_DIR / clip_name)

                start = seg["start"]
                end = min(seg["end"], start + 60)

                # Dedup check per segment
                dup = check_duplicate(
                    source_url=live_video_path,
                    segment_start=start,
                    segment_end=end,
                )
                if dup.get("is_duplicate"):
                    logger.warning(f"Segment duplicate: {start}-{end}")
                    errors.append({"segment": f"{start}-{end}", "error": "duplicate"})
                    continue

                success = trim_video(live_video_path, clip_path, start, end)
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
                    title=f"Live Highlight: {seg['text'][:50]}",
                    niche=niche,
                    agent_type="live_highlights",
                    video_path=vertical_path,
                )

                register_content(
                    video_path=vertical_path,
                    source_url=live_video_path,
                    segment_start=start,
                    segment_end=end,
                    agent_type="live_highlights",
                )

                clips_created.append({
                    "path": vertical_path,
                    "text": seg["text"],
                    "video_id": video_id,
                    "safety_status": safety_status,
                    "qa_status": qa["overall"],
                })

            except Exception as e:
                logger.error(f"Error creating clip {i}: {e}")
                errors.append({"segment": f"{seg['start']}-{seg['end']}", "error": str(e)})

        return {
            "success": len(clips_created) > 0,
            "clips_count": len(clips_created),
            "clips": clips_created,
            "errors": errors,
            "source_safety": safety_status,
        }

    except Exception as e:
        logger.error(f"Agent Live Highlights failed: {e}")
        return {"success": False, "error": str(e)}
