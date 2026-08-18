"""
Agent 5: Dub Flip — Multi-language video versions
Translates script to target languages, generates TTS in each.
"""
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_dub_flip")

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(video_path: str, niche: str = "health_fitness", languages: list = None) -> dict:
    """
    Create multi-language versions of a video.
    
    Steps:
    1. Transcribe original video
    2. Translate to target languages (AI)
    3. Generate TTS in each language
    4. Create videos with new audio
    """
    if languages is None:
        languages = ["en", "es", "hi", "pt"]
    
    from tools.transcriber import transcribe_video
    from engines.content_creator import translate_script
    from tools.tts_engine import text_to_speech
    from engines.video_builder import create_text_video
    from tools.video_editor import add_audio_track
    from engines.revenue_tracker import log_video
    
    logger.info(f"Agent: Dub Flip | Languages: {languages}")
    
    # 1. Transcribe original
    trans = transcribe_video(video_path)
    if not trans.get("success"):
        return {"success": False, "error": "Transcription failed"}
    
    # 2. Create versions for each language
    results = []
    timestamp = datetime.now().strftime("%H%M%S")
    
    for lang in languages:
        # Translate
        script = {
            "hook": trans["segments"][0]["text"] if trans["segments"] else "Check this out!",
            "body": trans["text"][:200],
            "cta": "Follow for more!",
            "duration": 60,
        }
        
        if lang != "en":
            script = translate_script(script, lang)
        
        # TTS
        audio_path = f"{PROCESSED_DIR}/dub_{lang}_{timestamp}.wav"
        text_to_speech(
            f"{script.get('hook', '')} {script.get('body', '')} {script.get('cta', '')}",
            audio_path,
            rate=150
        )
        
        # Create video
        video_out = f"{PROCESSED_DIR}/dub_video_{lang}_{timestamp}.mp4"
        create_text_video(script, video_out)
        
        # Add audio
        final_path = f"{PROCESSED_DIR}/dub_final_{lang}_{timestamp}.mp4"
        add_audio_track(video_out, audio_path, final_path, volume=0.8)
        
        video_id = log_video(
            title=f"Dubbed ({lang})",
            niche=niche,
            agent_type="dub_flip",
            video_path=final_path,
            language=lang
        )
        
        results.append({
            "language": lang,
            "video_path": final_path,
            "video_id": video_id,
        })
    
    return {
        "success": True,
        "versions_created": len(results),
        "results": results,
    }
