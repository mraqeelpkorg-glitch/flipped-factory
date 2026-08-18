"""
Agent 4: Remix Flip — Re-edit old content with fresh hook
Takes existing video, adds new hook/intro, remixes.
"""
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_remix_flip")

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(video_path: str, niche: str = "motivation", new_hook: str = None) -> dict:
    """
    Remix an existing video with a fresh hook.
    
    Steps:
    1. Load existing video
    2. Generate new hook (AI or template)
    3. Create hook intro video
    4. Combine: new hook + old content
    5. Add captions
    """
    from engines.content_creator import generate_script_with_ai, get_template_script
    from engines.video_builder import create_text_video
    from tools.video_editor import concat_videos, add_audio_track
    from tools.tts_engine import text_to_speech
    from engines.revenue_tracker import log_video
    
    logger.info(f"Agent: Remix Flip | Video: {video_path}")
    
    # 1. Generate new hook
    if not new_hook:
        script = get_template_script(niche)
        new_hook = script["hook"]
    
    # 2. Create hook intro
    hook_script = {
        "hook": new_hook,
        "body": "",
        "cta": "",
        "duration": 5,
    }
    
    timestamp = datetime.now().strftime("%H%M%S")
    output_dir = str(PROCESSED_DIR)
    hook_video = f"{output_dir}/remix_hook_{timestamp}.mp4"
    create_text_video(hook_script, hook_video)
    
    # 3. Combine
    final_path = f"{output_dir}/remix_final_{timestamp}.mp4"
    concat_videos([hook_video, video_path], final_path)
    
    # 4. Log
    video_id = log_video(
        title=new_hook[:60],
        niche=niche,
        agent_type="remix_flip",
        video_path=final_path
    )
    
    return {
        "success": True,
        "new_hook": new_hook,
        "video_path": final_path,
        "video_id": video_id,
    }
