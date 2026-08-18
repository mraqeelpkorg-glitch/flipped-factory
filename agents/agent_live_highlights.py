"""
Agent 11: Live Highlights — Live stream → Highlight clips
Extracts best moments from live streams.
"""
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_live_highlights")

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(live_video_path: str, niche: str = "motivation", max_clips: int = 5) -> dict:
    """
    Extract highlights from live stream recording.
    
    Steps:
    1. Transcribe live stream
    2. Find best moments (engagement peaks)
    3. Extract clips
    4. Add captions
    """
    from tools.transcriber import transcribe_video
    from tools.video_editor import trim_video, crop_to_vertical
    from engines.revenue_tracker import log_video
    
    logger.info(f"Agent: Live Highlights | File: {live_video_path}")
    
    # 1. Transcribe
    trans = transcribe_video(live_video_path)
    if not trans.get("success"):
        return {"success": False, "error": "Transcription failed"}
    
    segments = trans.get("segments", [])
    
    # 2. Find best moments (longest/most content)
    scored = sorted(segments, key=lambda s: len(s["text"].split()), reverse=True)
    
    # 3. Extract clips
    clips_created = []
    timestamp = datetime.now().strftime("%H%M%S")
    
    for i, seg in enumerate(scored[:max_clips]):
        clip_name = f"live_highlight_{i+1}_{timestamp}.mp4"
        clip_path = str(PROCESSED_DIR / clip_name)
        
        start = seg["start"]
        end = min(seg["end"], start + 60)
        
        success = trim_video(live_video_path, clip_path, start, end)
        if success:
            vertical_path = str(PROCESSED_DIR / f"vertical_{clip_name}")
            crop_to_vertical(clip_path, vertical_path)
            
            video_id = log_video(
                title=f"Live Highlight: {seg['text'][:50]}",
                niche=niche,
                agent_type="live_highlights",
                video_path=vertical_path
            )
            
            clips_created.append({
                "path": vertical_path,
                "text": seg["text"],
                "video_id": video_id,
            })
    
    return {
        "success": True,
        "clips_count": len(clips_created),
        "clips": clips_created,
    }
