"""
Agent 2: Podcast Clipper — Podcast → Instagram Reels
Takes podcast audio/video, extracts best moments.
"""
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_podcast_clipper")

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(podcast_path: str, niche: str = "education", max_clips: int = 5) -> dict:
    """
    Extract best moments from podcast for Instagram Reels.
    
    Steps:
    1. Transcribe full podcast (Whisper)
    2. Identify engaging segments (most words = most content)
    3. Trim each segment
    4. Crop to vertical
    5. Add captions
    """
    from tools.transcriber import transcribe_video, segments_to_srt
    from tools.video_editor import crop_to_vertical, trim_video
    from engines.revenue_tracker import log_video
    
    logger.info(f"Agent: Podcast Clipper | File: {podcast_path}")
    
    # 1. Transcribe
    trans_result = transcribe_video(podcast_path)
    if not trans_result.get("success"):
        return {"success": False, "error": f"Transcription failed: {trans_result.get('error')}"}
    
    segments = trans_result.get("segments", [])
    
    # 2. Score segments by content density
    scored = []
    for seg in segments:
        words = len(seg["text"].split())
        duration = seg["end"] - seg["start"]
        score = words / max(duration, 1)
        scored.append({**seg, "score": score, "word_count": words})
    
    scored.sort(key=lambda s: s["score"], reverse=True)
    
    # 3. Create clips from top segments
    clips_created = []
    for i, seg in enumerate(scored[:max_clips]):
        clip_name = f"podcast_clip_{i+1}_{datetime.now().strftime('%H%M%S')}.mp4"
        clip_path = str(PROCESSED_DIR / clip_name)
        
        # Trim to 30-60 seconds max
        start = seg["start"]
        end = min(seg["end"], start + 60)
        
        success = trim_video(podcast_path, clip_path, start, end)
        if success:
            # Crop to vertical
            vertical_path = str(PROCESSED_DIR / f"vertical_{clip_name}")
            crop_to_vertical(clip_path, vertical_path)
            
            video_id = log_video(
                title=f"Podcast Clip: {seg['text'][:50]}...",
                niche=niche,
                agent_type="podcast_clipper",
                video_path=vertical_path
            )
            
            clips_created.append({
                "path": vertical_path,
                "text": seg["text"],
                "duration": end - start,
                "score": round(seg["score"], 2),
                "video_id": video_id,
            })
    
    # Save SRT
    srt = segments_to_srt(segments)
    srt_path = PROCESSED_DIR / f"podcast_full_{datetime.now().strftime('%H%M%S')}.srt"
    srt_path.write_text(srt, encoding="utf-8")
    
    return {
        "success": True,
        "total_segments": len(segments),
        "clips_count": len(clips_created),
        "clips": clips_created,
        "srt_path": str(srt_path),
    }
