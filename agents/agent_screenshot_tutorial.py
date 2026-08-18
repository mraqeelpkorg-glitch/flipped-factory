"""
Agent 12: Screenshot Tutorial — Screenshots → Video tutorial
Converts screenshot-based content into video tutorials.
"""
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_screenshot_tutorial")

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(screenshots_dir: str, niche: str = "tech_ai", tutorial_title: str = "How to") -> dict:
    """
    Create video tutorial from screenshots.
    
    Steps:
    1. Load screenshots
    2. Generate tutorial script
    3. Create transitions between slides
    4. Add voiceover
    5. Export
    """
    from PIL import Image
    from engines.content_creator import get_template_script
    from engines.video_builder import create_slideshow_video
    from tools.tts_engine import text_to_speech
    from tools.video_editor import add_audio_track
    from engines.revenue_tracker import log_video
    
    logger.info(f"Agent: Screenshot Tutorial | Dir: {screenshots_dir}")
    
    # 1. Load images
    img_dir = Path(screenshots_dir)
    images = []
    for ext in ["*.png", "*.jpg", "*.jpeg", "*.gif"]:
        images.extend(sorted(img_dir.glob(ext)))
    
    if not images:
        return {"success": False, "error": "No screenshots found"}
    
    # 2. Generate script
    script = get_template_script(niche)
    script["hook"] = tutorial_title
    script["duration"] = len(images) * 4  # 4 seconds per slide
    
    # 3. TTS
    timestamp = datetime.now().strftime("%H%M%S")
    audio_path = f"{PROCESSED_DIR}/tutorial_voiceover_{timestamp}.wav"
    text_to_speech(f"{script['hook']} {script['body']} {script['cta']}", audio_path, rate=140)
    
    # 4. Create slideshow
    video_path = f"{PROCESSED_DIR}/tutorial_video_{timestamp}.mp4"
    create_slideshow_video(
        [str(img) for img in images],
        video_path,
        duration_per_image=4.0
    )
    
    # 5. Add audio
    final_path = f"{PROCESSED_DIR}/tutorial_final_{timestamp}.mp4"
    add_audio_track(video_path, audio_path, final_path, volume=0.8)
    
    video_id = log_video(
        title=tutorial_title[:60],
        niche=niche,
        agent_type="screenshot_tutorial",
        video_path=final_path
    )
    
    return {
        "success": True,
        "screenshots_count": len(images),
        "video_path": final_path,
        "video_id": video_id,
    }
