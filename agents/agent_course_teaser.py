"""
Agent 10: Course Teaser — Course content → Free preview clip
Creates teaser clips from course content.
"""
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_course_teaser")

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(course_module: str, niche: str = "education", course_name: str = "My Course") -> dict:
    """
    Create free teaser from course content.
    
    Steps:
    1. Parse course module text
    2. Extract key insight
    3. Generate teaser script
    4. Create engaging video
    5. Add "Full course" CTA
    """
    from engines.content_creator import generate_script_with_ai
    from engines.video_builder import create_text_video
    from tools.tts_engine import text_to_speech
    from tools.video_editor import add_audio_track
    from engines.revenue_tracker import log_video
    
    logger.info(f"Agent: Course Teaser | Module: {course_module[:50]}")
    
    # Generate teaser script
    script = generate_script_with_ai(course_module, niche, duration=45)
    
    # Override CTA with course-specific
    script["cta"] = f"Full course link in bio! Follow for free tips!"
    
    # Create video
    timestamp = datetime.now().strftime("%H%M%S")
    audio_path = f"{PROCESSED_DIR}/teaser_voiceover_{timestamp}.wav"
    text_to_speech(f"{script['hook']} {script['body']} {script['cta']}", audio_path, rate=150)
    
    video_path = f"{PROCESSED_DIR}/teaser_video_{timestamp}.mp4"
    create_text_video(script, video_path)
    
    final_path = f"{PROCESSED_DIR}/teaser_final_{timestamp}.mp4"
    add_audio_track(video_path, audio_path, final_path, volume=0.8)
    
    video_id = log_video(
        title=script.get("hook", "Course Teaser")[:60],
        niche=niche,
        agent_type="course_teaser",
        video_path=final_path
    )
    
    return {
        "success": True,
        "course_name": course_name,
        "video_path": final_path,
        "video_id": video_id,
    }
