"""
TTS Engine — Text-to-Speech using pyttsx3 (FREE, local, offline).
Multi-language support.
"""
import logging
import tempfile
import os
from pathlib import Path

logger = logging.getLogger("tts_engine")

# Voice cache
_voice_engine = None


def get_engine():
    """Get or create TTS engine."""
    global _voice_engine
    if _voice_engine is None:
        try:
            import pyttsx3
            _voice_engine = pyttsx3.init()
            _voice_engine.setProperty("rate", 150)
            _voice_engine.setProperty("volume", 0.9)
            logger.info("TTS engine initialized")
        except Exception as e:
            logger.warning(f"pyttsx3 not available: {e}")
            return None
    return _voice_engine


def text_to_speech(text: str, output_path: str, rate: int = 150, volume: float = 0.9, voice_index: int = 0) -> bool:
    """
    Convert text to speech audio file.
    Returns True if successful.
    """
    engine = get_engine()
    if engine is None:
        logger.warning("TTS engine not available")
        return False
    
    try:
        engine.setProperty("rate", rate)
        engine.setProperty("volume", volume)
        
        # Set voice
        voices = engine.getProperty("voices")
        if voice_index < len(voices):
            engine.setProperty("voice", voices[voice_index].id)
        
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        
        if os.path.exists(output_path):
            logger.info(f"TTS saved: {output_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        return False


def text_to_speech_multi(text: str, output_dir: str, language: str = "en") -> dict:
    """
    Generate TTS for multiple languages.
    Returns {language: audio_path}
    """
    from engines.content_creator import TTS_LANGUAGES
    
    results = {}
    
    # For languages supported by system TTS
    lang_config = TTS_LANGUAGES.get(language, TTS_LANGUAGES["en"])
    
    output_path = os.path.join(output_dir, f"voiceover_{language}.wav")
    
    success = text_to_speech(
        text,
        output_path,
        rate=lang_config["rate"],
        voice_index=lang_config["voice_index"]
    )
    
    if success:
        results[language] = output_path
    
    return results


def get_available_voices() -> list[dict]:
    """List available TTS voices."""
    engine = get_engine()
    if engine is None:
        return []
    
    voices = engine.getProperty("voices")
    return [
        {
            "index": i,
            "name": v.name,
            "id": v.id,
            "languages": v.languages,
        }
        for i, v in enumerate(voices)
    ]


def set_voice(index: int):
    """Set the active voice by index."""
    engine = get_engine()
    if engine is None:
        return
    
    voices = engine.getProperty("voices")
    if index < len(voices):
        engine.setProperty("voice", voices[index].id)
        logger.info(f"Voice set to: {voices[index].name}")


def batch_tts(texts: list[dict], output_dir: str) -> list[dict]:
    """
    Generate TTS for multiple texts.
    texts = [{"id": "1", "text": "...", "language": "en"}, ...]
    Returns list of results.
    """
    results = []
    for item in texts:
        text = item.get("text", "")
        lang = item.get("language", "en")
        item_id = item.get("id", "unknown")
        
        output_path = os.path.join(output_dir, f"voiceover_{item_id}_{lang}.wav")
        success = text_to_speech(text, output_path)
        
        results.append({
            "id": item_id,
            "language": lang,
            "success": success,
            "path": output_path if success else None,
        })
    
    return results
