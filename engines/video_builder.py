"""
Video Builder — Creates videos using MoviePy + Pillow. ALL FREE.
Handles vertical (9:16) format for Instagram Reels.
"""
import random
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("video_builder")

# ─── Constants ────────────────────────────────────────────────────────────────
WIDTH = 1080
HEIGHT = 1920
FPS = 30
BG_COLORS = [
    "#0a0a0f", "#1a1a2e", "#16213e", "#0f3460",
    "#1b1b2f", "#162447", "#1f1f38", "#000000",
]
GRADIENT_COLORS = [
    ("#7c3aed", "#ec4899"),  # Purple to pink
    ("#06b6d4", "#3b82f6"),  # Cyan to blue
    ("#f59e0b", "#ef4444"),  # Amber to red
    ("#10b981", "#3b82f6"),  # Green to blue
    ("#8b5cf6", "#06b6d4"),  # Violet to cyan
]


# ─── Background Generation ────────────────────────────────────────────────────
def create_gradient_background(width=WIDTH, height=HEIGHT):
    """Create a gradient background image."""
    from PIL import Image, ImageDraw
    colors = random.choice(GRADIENT_COLORS)
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    
    # Parse hex colors
    c1 = tuple(int(colors[0].lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    c2 = tuple(int(colors[1].lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    
    for y in range(height):
        ratio = y / height
        r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
        g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
        b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    return img


def create_dark_background(width=WIDTH, height=HEIGHT):
    """Create a solid dark background."""
    from PIL import Image
    color = random.choice(BG_COLORS)
    rgb = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    return Image.new("RGB", (width, height), rgb)


# ─── Text Rendering ───────────────────────────────────────────────────────────
def render_text_block(text: str, max_width: int = 900, font_size: int = 48, color="white"):
    """Render text as an image with word wrapping."""
    from PIL import Image, ImageDraw, ImageFont
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except Exception:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()
    
    # Word wrap
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = font.getbbox(test_line)
        if bbox[2] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    # Calculate image size
    line_height = font_size + 10
    total_height = len(lines) * line_height + 20
    
    img = Image.new("RGBA", (max_width + 40, total_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    y = 10
    for line in lines:
        # Text shadow
        draw.text((22, y + 2), line, font=font, fill=(0, 0, 0, 180))
        # Main text
        draw.text((20, y), line, font=font, fill=color)
        y += line_height
    
    return img


# ─── Video Creation ───────────────────────────────────────────────────────────
def create_text_video(
    script: dict,
    output_path: str,
    bg_type: str = "gradient",
    font_size: int = 48,
    duration_per_section: dict = None,
):
    """
    Create a vertical video with animated text sections.
    
    script = {
        "hook": "Opening line...",
        "body": "Main content...",
        "cta": "Call to action...",
        "duration": 30
    }
    """
    from moviepy.editor import (
        ColorClip, ImageClip, CompositeVideoClip, concatenate_videoclips
    )
    from PIL import Image
    import io
    
    if duration_per_section is None:
        total = script.get("duration", 30)
        duration_per_section = {
            "hook": min(5, total * 0.15),
            "body": total * 0.7,
            "cta": min(5, total * 0.15),
        }
    
    clips = []
    
    for section_key in ["hook", "body", "cta"]:
        text = script.get(section_key, "")
        if not text:
            continue
        
        duration = duration_per_section.get(section_key, 5)
        
        # Create background
        if bg_type == "gradient":
            bg = create_gradient_background()
        else:
            bg = create_dark_background()
        
        # Render text
        font_sz = font_size if section_key == "hook" else font_size - 8
        text_img = render_text_block(text, font_size=font_sz)
        
        # Convert to numpy array
        import numpy as np
        bg_arr = np.array(bg)
        
        # Create background clip
        bg_clip = ColorClip(size=(WIDTH, HEIGHT), color=(0, 0, 0)).set_duration(duration)
        
        # Overlay text in center
        text_arr = np.array(text_img)
        text_clip = ImageClip(text_arr).set_duration(duration)
        text_clip = text_clip.set_position(("center", "center"))
        
        # Compose
        composite = CompositeVideoClip([bg_clip, text_clip], size=(WIDTH, HEIGHT))
        composite = composite.set_duration(duration)
        
        clips.append(composite)
    
    # Concatenate all clips
    if clips:
        final = concatenate_videoclips(clips, method="compose")
        final.write_videofile(
            output_path,
            fps=FPS,
            codec="libx264",
            audio=False,
            preset="medium",
            bitrate="3M",
            logger=None,
        )
        final.close()
        for c in clips:
            c.close()
        logger.info(f"Video created: {output_path}")
        return True
    
    return False


def create_slideshow_video(
    images: list,
    output_path: str,
    duration_per_image: float = 3.0,
    transition: str = "fade",
):
    """Create a slideshow video from a list of images."""
    from moviepy.editor import ImageClip, CompositeVideoClip, concatenate_videoclips
    import numpy as np
    
    clips = []
    for img_path in images:
        try:
            if isinstance(img_path, str):
                from PIL import Image as PILImage
                img = PILImage.open(img_path).resize((WIDTH, HEIGHT))
            else:
                img = img_path.resize((WIDTH, HEIGHT))
            
            arr = np.array(img)
            clip = ImageClip(arr).set_duration(duration_per_image)
            clips.append(clip)
        except Exception as e:
            logger.warning(f"Failed to load image: {e}")
    
    if clips:
        final = concatenate_videoclips(clips, method="compose")
        final.write_videofile(
            output_path,
            fps=FPS,
            codec="libx264",
            audio=False,
            preset="medium",
            bitrate="3M",
            logger=None,
        )
        final.close()
        logger.info(f"Slideshow created: {output_path}")
        return True
    
    return False


# ─── Audio Overlay ────────────────────────────────────────────────────────────
def add_audio_to_video(video_path: str, audio_path: str, output_path: str):
    """Add audio track to a video."""
    from moviepy.editor import VideoFileClip, AudioFileClip
    
    try:
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)
        
        # Trim audio to video length
        if audio.duration > video.duration:
            audio = audio.subclip(0, video.duration)
        
        final = video.set_audio(audio)
        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            logger=None,
        )
        final.close()
        video.close()
        audio.close()
        logger.info(f"Audio added: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to add audio: {e}")
        return False


# ─── Utility ──────────────────────────────────────────────────────────────────
def get_video_info(video_path: str) -> dict:
    """Get video metadata."""
    from moviepy.editor import VideoFileClip
    try:
        clip = VideoFileClip(video_path)
        info = {
            "duration": clip.duration,
            "fps": clip.fps,
            "size": clip.size,
            "filename": Path(video_path).name,
        }
        clip.close()
        return info
    except Exception as e:
        return {"error": str(e)}
