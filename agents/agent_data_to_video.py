"""
Agent 6: Data to Video — Research/data → Infographic video
Creates animated infographic videos from data/stats.
"""
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_data_to_video")

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(data_source: str, niche: str = "tech_ai", stats: list = None) -> dict:
    """
    Create infographic video from data/stats.
    
    Steps:
    1. Parse data (text or JSON)
    2. Extract key stats
    3. Generate voiceover for each stat
    4. Create animated slides
    5. Combine into video
    """
    from engines.content_creator import get_template_script
    from engines.video_builder import create_text_video
    from tools.tts_engine import text_to_speech
    from tools.video_editor import add_audio_track
    from engines.revenue_tracker import log_video
    
    logger.info(f"Agent: Data to Video | Source: {data_source[:50]}")
    
    # Default stats if none provided
    if not stats:
        stats = [
            "85% of marketers use short-form video",
            "93% of businesses see video as important",
            "Short-form video gets 2.5x more engagement",
            "Video makes up 82% of internet traffic",
        ]
    
    # Create script from stats
    hook = f"Did you know? {stats[0]}"
    body = " ".join([f"Number {i+2}: {s}." for i, s in enumerate(stats[1:3])])
    cta = "Follow for more data insights!"
    
    script = {
        "hook": hook,
        "body": body,
        "cta": cta,
        "duration": 45,
    }
    
    # Generate TTS
    timestamp = datetime.now().strftime("%H%M%S")
    audio_path = f"{PROCESSED_DIR}/data_voiceover_{timestamp}.wav"
    text_to_speech(f"{hook} {body} {cta}", audio_path, rate=140)
    
    # Create video
    video_path = f"{PROCESSED_DIR}/data_video_{timestamp}.mp4"
    create_text_video(script, video_path)
    
    # Add audio
    final_path = f"{PROCESSED_DIR}/data_final_{timestamp}.mp4"
    add_audio_track(video_path, audio_path, final_path, volume=0.8)
    
    video_id = log_video(
        title=hook[:60],
        niche=niche,
        agent_type="data_to_video",
        video_path=final_path
    )
    
    return {
        "success": True,
        "stats_used": len(stats),
        "video_path": final_path,
        "video_id": video_id,
    }
