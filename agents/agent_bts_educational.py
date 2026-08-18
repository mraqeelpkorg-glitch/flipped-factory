"""
Agent 8: BTS to Educational — Behind-the-scenes → Tutorial
Converts raw BTS footage into educational content.
"""
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_bts_educational")

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(bts_video_path: str, niche: str = "tech_ai", tutorial_topic: str = None) -> dict:
    """
    Convert BTS footage to educational tutorial.
    
    Steps:
    1. Transcribe BTS footage
    2. Analyze content (what is being shown?)
    3. Generate tutorial script
    4. Create educational video
    5. Add captions + voiceover
    """
    from tools.transcriber import transcribe_video
    from engines.content_creator import generate_script_with_ai, get_template_script
    from engines.video_builder import create_text_video
    from tools.tts_engine import text_to_speech
    from tools.video_editor import crop_to_vertical, add_audio_track
    from engines.revenue_tracker import log_video
    
    logger.info(f"Agent: BTS to Educational | File: {bts_video_path}")
    
    # 1. Transcribe
    trans = transcribe_video(bts_video_path)
    
    # 2. Generate tutorial script
    topic = tutorial_topic or "How to create content like this"
    
    if trans.get("success"):
        script = generate_script_with_ai(topic, niche, duration=45)
    else:
        script = get_template_script(niche)
    
    # 3. Create video
    timestamp = datetime.now().strftime("%H%M%S")
    audio_path = f"{PROCESSED_DIR}/bts_voiceover_{timestamp}.wav"
    text_to_speech(f"{script['hook']} {script['body']} {script['cta']}", audio_path, rate=150)
    
    video_path = f"{PROCESSED_DIR}/bts_video_{timestamp}.mp4"
    create_text_video(script, video_path)
    
    final_path = f"{PROCESSED_DIR}/bts_final_{timestamp}.mp4"
    add_audio_track(video_path, audio_path, final_path, volume=0.8)
    
    video_id = log_video(
        title=script.get("hook", "Tutorial")[:60],
        niche=niche,
        agent_type="bts_educational",
        video_path=final_path
    )
    
    return {
        "success": True,
        "topic": topic,
        "video_path": final_path,
        "video_id": video_id,
    }
