"""
Agent 9: Trending Audio — Trending sound + Niche = Viral content
Uses trending TikTok/Reels audio with niche content.
"""
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_trending_niche")

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(niche: str = "health_fitness", trending_audio_path: str = None, hook: str = None) -> dict:
    """
    Create niche content with trending audio.
    
    Steps:
    1. Get trending topic for niche
    2. Generate niche-specific script
    3. Create visual content
    4. Sync with trending audio
    5. Export
    """
    from engines.content_creator import get_template_script, generate_script_with_ai
    from engines.niche_selector import select_topic, get_hashtags
    from engines.video_builder import create_text_video
    from tools.tts_engine import text_to_speech
    from tools.video_editor import add_audio_track
    from engines.revenue_tracker import log_video
    
    logger.info(f"Agent: Trending Audio | Niche: {niche}")
    
    # 1. Select topic
    topic = select_topic(niche)
    
    # 2. Generate script
    script = generate_script_with_ai(topic, niche, duration=30)
    
    # 3. Create video
    timestamp = datetime.now().strftime("%H%M%S")
    audio_path = f"{PROCESSED_DIR}/trending_voiceover_{timestamp}.wav"
    text_to_speech(f"{script['hook']} {script['body']} {script['cta']}", audio_path, rate=155)
    
    video_path = f"{PROCESSED_DIR}/trending_video_{timestamp}.mp4"
    create_text_video(script, video_path)
    
    # 4. Add audio (voiceover or trending audio)
    final_path = f"{PROCESSED_DIR}/trending_final_{timestamp}.mp4"
    audio_to_use = trending_audio_path or audio_path
    add_audio_track(video_path, audio_to_use, final_path, volume=0.8)
    
    # 5. Get hashtags
    hashtags = get_hashtags(niche)
    
    video_id = log_video(
        title=script.get("hook", "Trending")[:60],
        niche=niche,
        agent_type="trending_niche",
        video_path=final_path
    )
    
    return {
        "success": True,
        "topic": topic,
        "hashtags": hashtags,
        "video_path": final_path,
        "video_id": video_id,
    }
