"""
TTS Engine — Text-to-Speech using macOS `say` command.
Natural voice quality, free, local, offline.
"""
import logging
import subprocess
import os
import json
from pathlib import Path

logger = logging.getLogger("tts_engine")

# Available voices (macOS)
VOICES = {
    "en": "Daniel",        # English (British) - natural male
    "en-us": "Samantha",   # English (US) - natural female
    "es": "Monica",        # Spanish
    "fr": "Thomas",        # French
    "de": "Anna",          # German
    "hi": "Lekha",         # Hindi
    "pt": "Luciana",       # Portuguese
    "ar": "Maged",         # Arabic
    "ja": "Kyoko",         # Japanese
    "zh": "Meijia",        # Chinese
}


def text_to_speech(
    text: str,
    output_path: str,
    voice: str = "Daniel",
    rate: int = 200,
    volume: float = 1.0,
) -> bool:
    """
    Convert text to speech using macOS `say` command.
    Much more natural than pyttsx3.
    
    Args:
        text: Text to speak
        output_path: Output file path (.aiff, .wav, .mp3)
        voice: Voice name (default: Daniel - British English)
        rate: Words per minute (default: 200)
        volume: 0.0 to 1.0
    """
    if not text.strip():
        logger.warning("Empty text, skipping TTS")
        return False
    
    # Determine output format from extension
    ext = Path(output_path).suffix.lower()
    
    try:
        # macOS say command generates AIFF natively, convert if needed
        if ext in (".mp3", ".wav"):
            # Generate AIFF first, then convert
            aiff_path = output_path.rsplit(".", 1)[0] + ".aiff"
            
            cmd_say = [
                "say",
                "-v", voice,
                "-r", str(rate),
                "-o", aiff_path,
                text,
            ]
            result = subprocess.run(cmd_say, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                logger.error(f"say failed: {result.stderr}")
                return False
            
            # Convert to desired format using FFmpeg
            cmd_ffmpeg = [
                "ffmpeg", "-i", aiff_path,
                "-acodec", "libmp3lame" if ext == ".mp3" else "pcm_s16le",
                "-ar", "44100", "-ac", "1",
                "-y", output_path,
            ]
            result = subprocess.run(cmd_ffmpeg, capture_output=True, text=True, timeout=30)
            
            # Clean up AIFF
            if os.path.exists(aiff_path):
                os.remove(aiff_path)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg conversion failed: {result.stderr}")
                return False
        else:
            # Direct AIFF output
            cmd = [
                "say",
                "-v", voice,
                "-r", str(rate),
                "-o", output_path,
                text,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                logger.error(f"say failed: {result.stderr}")
                return False
        
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            logger.info(f"TTS saved: {output_path} ({size/1024:.1f} KB)")
            return True
        
        return False
    except subprocess.TimeoutExpired:
        logger.error("TTS timed out")
        return False
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        return False


def text_to_speech_multi(text: str, output_dir: str, language: str = "en") -> dict:
    """Generate TTS for multiple languages."""
    results = {}
    voice = VOICES.get(language, VOICES["en"])
    output_path = os.path.join(output_dir, f"voiceover_{language}.mp3")
    success = text_to_speech(text, output_path, voice=voice)
    if success:
        results[language] = output_path
    return results


def get_available_voices() -> list[dict]:
    """List available macOS voices."""
    try:
        result = subprocess.run(
            ["say", "-v", "?"],
            capture_output=True, text=True, timeout=10
        )
        voices = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    voices.append({
                        "name": parts[0],
                        "language": parts[1] if len(parts) > 1 else "",
                    })
        return voices
    except Exception:
        return []


def batch_tts(texts: list[dict], output_dir: str) -> list[dict]:
    """Generate TTS for multiple texts."""
    results = []
    for item in texts:
        text = item.get("text", "")
        lang = item.get("language", "en")
        item_id = item.get("id", "unknown")
        voice = VOICES.get(lang, VOICES["en"])
        output_path = os.path.join(output_dir, f"voiceover_{item_id}_{lang}.mp3")
        success = text_to_speech(text, output_path, voice=voice)
        results.append({
            "id": item_id,
            "language": lang,
            "success": success,
            "path": output_path if success else None,
        })
    return results
