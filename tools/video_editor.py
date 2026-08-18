"""
Video Editor — Common video editing utilities.
FREE: MoviePy + FFmpeg
"""
import os
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("video_editor")

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def trim_video(input_path: str, output_path: str, start: float, end: float) -> bool:
    """Trim video between start and end timestamps (seconds)."""
    try:
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(input_path).subclip(start, end)
        clip.write_videofile(output_path, codec="libx264", audio=False, logger=None)
        clip.close()
        return True
    except Exception as e:
        logger.error(f"Trim failed: {e}")
        return False


def crop_to_vertical(input_path: str, output_path: str) -> bool:
    """Crop horizontal video to vertical (9:16) from center using FFmpeg."""
    try:
        # Get video dimensions
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-select_streams", "v:0",
             "-show_entries", "stream=width,height",
             "-of", "csv=p=0", input_path],
            capture_output=True, text=True, timeout=10
        )
        parts = probe.stdout.strip().split(",")
        w, h = int(parts[0]), int(parts[1])
        
        # Calculate crop for 9:16
        target_ratio = 9 / 16
        new_w = int(h * target_ratio)
        if new_w > w:
            new_w = w
        
        x = (w - new_w) // 2
        
        cmd = [
            "ffmpeg", "-i", input_path,
            "-vf", f"crop={new_w}:{h}:{x}:0,scale=1080:1920",
            "-c:v", "libx264", "-an", "-y", output_path
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Crop failed: {e}")
        return False


def resize_video(input_path: str, output_path: str, width: int = 1080, height: int = 1920) -> bool:
    """Resize video to target dimensions."""
    try:
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(input_path).resize((width, height))
        clip.write_videofile(output_path, codec="libx264", audio=False, logger=None)
        clip.close()
        return True
    except Exception as e:
        logger.error(f"Resize failed: {e}")
        return False


def add_text_overlay(input_path: str, output_path: str, text: str, position: str = "center",
                     font_size: int = 48, color: str = "white", bg_color: str = None) -> bool:
    """Add text overlay to video."""
    try:
        from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
        
        video = VideoFileClip(input_path)
        
        txt_clip = TextClip(
            text,
            fontsize=font_size,
            color=color,
            bg_color=bg_color,
            font="Helvetica",
            size=(900, None),
            method="caption",
        )
        
        if position == "center":
            txt_pos = ("center", "center")
        elif position == "top":
            txt_pos = ("center", 100)
        else:
            txt_pos = ("center", video.h - 200)
        
        txt_clip = txt_clip.set_position(txt_pos).set_duration(video.duration)
        
        final = CompositeVideoClip([video, txt_clip])
        final.write_videofile(output_path, codec="libx264", audio=False, logger=None)
        
        final.close()
        video.close()
        txt_clip.close()
        return True
    except Exception as e:
        logger.error(f"Text overlay failed: {e}")
        return False


def extract_audio(input_path: str, output_path: str) -> bool:
    """Extract audio track from video."""
    try:
        cmd = [
            "ffmpeg", "-i", input_path,
            "-vn", "-acodec", "libmp3lame",
            "-q:a", "2",
            output_path, "-y"
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Audio extraction failed: {e}")
        return False


def add_audio_track(video_path: str, audio_path: str, output_path: str, volume: float = 1.0) -> bool:
    """Add audio track to video."""
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip
        
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)
        
        if audio.duration > video.duration:
            audio = audio.subclip(0, video.duration)
        
        audio = audio.volumex(volume)
        final = video.set_audio(audio)
        
        final.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
        final.close()
        video.close()
        audio.close()
        return True
    except Exception as e:
        logger.error(f"Add audio failed: {e}")
        return False


def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds."""
    try:
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(video_path)
        duration = clip.duration
        clip.close()
        return duration
    except Exception:
        return 0.0


def concat_videos(video_paths: list, output_path: str) -> bool:
    """Concatenate multiple videos."""
    try:
        from moviepy.editor import VideoFileClip, concatenate_videoclips
        
        clips = [VideoFileClip(p) for p in video_paths]
        final = concatenate_videoclips(clips, method="compose")
        final.write_videofile(output_path, codec="libx264", audio=False, logger=None)
        
        final.close()
        for c in clips:
            c.close()
        return True
    except Exception as e:
        logger.error(f"Concat failed: {e}")
        return False


def create_test_video(output_path: str, duration: float = 5.0) -> bool:
    """Create a test video for debugging."""
    try:
        from moviepy.editor import ColorClip
        clip = ColorClip(size=(1080, 1920), color=(30, 30, 60)).set_duration(duration)
        clip.write_videofile(output_path, fps=30, codec="libx264", audio=False, logger=None)
        clip.close()
        return True
    except Exception as e:
        logger.error(f"Test video creation failed: {e}")
        return False
