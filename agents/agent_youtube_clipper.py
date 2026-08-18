"""
Agent 1: YouTube Clipper — YouTube → Instagram Reels
Downloads YouTube video, extracts best clips, crops to vertical.
"""
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_youtube_clipper")

RAW_DIR = Path(__file__).parent.parent / "data" / "videos" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(youtube_url: str, niche: str = "health_fitness", max_clips: int = 3) -> dict:
    """
    Download YouTube video and create Instagram-ready vertical clips.
    
    Steps:
    1. Download video (yt-dlp)
    2. Transcribe (Whisper)
    3. Find best segments
    4. Crop to vertical 9:16
    5. Add captions
    """
    from tools.downloader import download_video
    from tools.transcriber import transcribe_video, segments_to_srt
    from tools.video_editor import crop_to_vertical, trim_video, add_text_overlay
    from engines.content_creator import get_template_script
    from engines.revenue_tracker import log_video
    
    logger.info(f"Agent: YouTube Clipper | URL: {youtube_url}")
    
    # 1. Download
    dl_result = download_video(youtube_url)
    if not dl_result["success"]:
        return {"success": False, "error": f"Download failed: {dl_result.get('error')}"}
    
    video_path = dl_result["path"]
    title = dl_result.get("title", "YouTube Clip")
    
    # 2. Transcribe
    trans_result = transcribe_video(video_path)
    
    # 3. Create clips
    clips_created = []
    
    if trans_result.get("success") and trans_result.get("segments"):
        segments = trans_result["segments"]
        # Find segments with most words (likely most content)
        scored_segments = sorted(segments, key=lambda s: len(s["text"].split()), reverse=True)
        
        for i, seg in enumerate(scored_segments[:max_clips]):
            clip_name = f"yt_clip_{i+1}_{datetime.now().strftime('%H%M%S')}.mp4"
            clip_path = str(PROCESSED_DIR / clip_name)
            
            # Trim segment
            success = trim_video(video_path, clip_path, seg["start"], min(seg["end"], seg["start"] + 60))
            
            if success:
                # Crop to vertical
                vertical_path = str(PROCESSED_DIR / f"vertical_{clip_name}")
                crop_to_vertical(clip_path, vertical_path)
                
                # Log
                video_id = log_video(
                    title=f"{title} - Clip {i+1}",
                    niche=niche,
                    agent_type="youtube_clipper",
                    video_path=vertical_path
                )
                
                clips_created.append({
                    "path": vertical_path,
                    "text": seg["text"],
                    "duration": seg["end"] - seg["start"],
                    "video_id": video_id,
                })
    else:
        # Fallback: just crop the whole video
        clip_name = f"yt_clip_full_{datetime.now().strftime('%H%M%S')}.mp4"
        clip_path = str(PROCESSED_DIR / clip_name)
        
        crop_to_vertical(video_path, clip_path)
        
        video_id = log_video(
            title=f"{title} - Full",
            niche=niche,
            agent_type="youtube_clipper",
            video_path=clip_path
        )
        
        clips_created.append({"path": clip_path, "video_id": video_id})
    
    return {
        "success": True,
        "source_title": title,
        "clips_count": len(clips_created),
        "clips": clips_created,
    }
