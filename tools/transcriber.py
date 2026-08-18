"""
Transcriber — Speech-to-text using Whisper (FREE, local).
"""
import logging
import json
from pathlib import Path

logger = logging.getLogger("transcriber")

# Whisper model cache
_model = None


def get_whisper_model(model_size: str = "base"):
    """Load Whisper model (cached)."""
    global _model
    if _model is None:
        try:
            import whisper
            logger.info(f"Loading Whisper model: {model_size}")
            _model = whisper.load_model(model_size)
            logger.info("Whisper model loaded")
        except ImportError:
            logger.warning("Whisper not installed. Run: pip install openai-whisper")
            return None
    return _model


def transcribe(audio_path: str, model_size: str = "base", language: str = None) -> dict:
    """
    Transcribe audio file to text.
    Returns {text, segments, language, duration}
    """
    model = get_whisper_model(model_size)
    if model is None:
        return {"success": False, "error": "Whisper not available"}
    
    try:
        options = {}
        if language:
            options["language"] = language
        
        result = model.transcribe(audio_path, **options)
        
        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip(),
            })
        
        return {
            "success": True,
            "text": result["text"],
            "segments": segments,
            "language": result.get("language", "unknown"),
            "word_count": len(result["text"].split()),
        }
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return {"success": False, "error": str(e)}


def transcribe_video(video_path: str, model_size: str = "base") -> dict:
    """Extract audio from video and transcribe."""
    import subprocess
    import tempfile
    import os
    
    # Extract audio to temp file
    audio_path = tempfile.mktemp(suffix=".wav")
    
    try:
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1",
            audio_path, "-y"
        ]
        subprocess.run(cmd, capture_output=True, timeout=60)
        
        if os.path.exists(audio_path):
            result = transcribe(audio_path, model_size)
            os.unlink(audio_path)
            return result
        else:
            return {"success": False, "error": "Failed to extract audio"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def segments_to_srt(segments: list) -> str:
    """Convert segments to SRT subtitle format."""
    srt_lines = []
    for i, seg in enumerate(segments):
        start = seg["start"]
        end = seg["end"]
        text = seg["text"]
        
        srt_lines.append(f"{i + 1}")
        srt_lines.append(f"{format_time(start)} --> {format_time(end)}")
        srt_lines.append(text)
        srt_lines.append("")
    
    return "\n".join(srt_lines)


def format_time(seconds: float) -> str:
    """Format seconds to SRT time."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def save_transcription(result: dict, output_path: str):
    """Save transcription result to JSON."""
    Path(output_path).write_text(json.dumps(result, indent=2, ensure_ascii=False))
    logger.info(f"Transcription saved: {output_path}")


def save_srt(segments: list, output_path: str):
    """Save segments as SRT file."""
    srt_content = segments_to_srt(segments)
    Path(output_path).write_text(srt_content, encoding="utf-8")
    logger.info(f"SRT saved: {output_path}")
