"""
Caption Generator — Animated text overlays for videos.
FREE: Uses Pillow + MoviePy
"""
import random
import logging
from pathlib import Path

logger = logging.getLogger("caption_generator")

# ─── Caption Styles ───────────────────────────────────────────────────────────
STYLES = {
    "bold_white": {
        "font_size": 52,
        "color": "white",
        "shadow": True,
        "bg_color": None,
        "position": "center",
    },
    "neon_glow": {
        "font_size": 48,
        "color": "#00ff88",
        "shadow": True,
        "bg_color": None,
        "position": "center",
    },
    "typewriter": {
        "font_size": 44,
        "color": "white",
        "shadow": False,
        "bg_color": (0, 0, 0, 180),
        "position": "center",
    },
    "top_bar": {
        "font_size": 40,
        "color": "white",
        "shadow": False,
        "bg_color": (124, 58, 237, 200),
        "position": "top",
    },
    "bottom_bar": {
        "font_size": 40,
        "color": "white",
        "shadow": False,
        "bg_color": (0, 0, 0, 200),
        "position": "bottom",
    },
}


# ─── SRT Generation ───────────────────────────────────────────────────────────
def text_to_srt(text: str, duration: float, words_per_chunk: int = 6) -> str:
    """Convert text to SRT subtitle format."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), words_per_chunk):
        chunks.append(" ".join(words[i:i + words_per_chunk]))
    
    chunk_duration = duration / max(len(chunks), 1)
    srt_lines = []
    
    for i, chunk in enumerate(chunks):
        start = i * chunk_duration
        end = (i + 1) * chunk_duration
        srt_lines.append(f"{i + 1}")
        srt_lines.append(f"{format_time(start)} --> {format_time(end)}")
        srt_lines.append(chunk)
        srt_lines.append("")
    
    return "\n".join(srt_lines)


def format_time(seconds: float) -> str:
    """Format seconds to SRT time format."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# ─── Word-level Timestamps ────────────────────────────────────────────────────
def generate_word_timestamps(text: str, duration: float) -> list[dict]:
    """Generate word-level timestamps for animated captions."""
    words = text.split()
    if not words:
        return []
    
    time_per_word = duration / len(words)
    timestamps = []
    
    for i, word in enumerate(words):
        timestamps.append({
            "word": word,
            "start": round(i * time_per_word, 3),
            "end": round((i + 1) * time_per_word, 3),
        })
    
    return timestamps


# ─── Caption Image Generation ─────────────────────────────────────────────────
def create_caption_image(
    text: str,
    width: int = 1080,
    font_size: int = 48,
    color: str = "white",
    bg_color: tuple = None,
    shadow: bool = True,
    max_chars_per_line: int = 30,
) -> "Image":
    """Create a caption image with text."""
    from PIL import Image, ImageDraw, ImageFont
    
    # Load font
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
        test = f"{current_line} {word}".strip()
        bbox = font.getbbox(test)
        if bbox[2] <= width - 100:
            current_line = test
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    # Calculate dimensions
    line_height = font_size + 12
    total_height = len(lines) * line_height + 40
    
    if bg_color:
        img = Image.new("RGBA", (width, total_height), bg_color)
    else:
        img = Image.new("RGBA", (width, total_height), (0, 0, 0, 0))
    
    draw = ImageDraw.Draw(img)
    
    y = 20
    for line in lines:
        bbox = font.getbbox(line)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        
        if shadow:
            draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 200))
        draw.text((x, y), line, font=font, fill=color)
        y += line_height
    
    return img


# ─── Animated Caption Overlay ─────────────────────────────────────────────────
def create_animated_captions(
    text: str,
    duration: float,
    width: int = 1080,
    height: int = 1920,
    style: str = "bold_white",
) -> list:
    """
    Create animated caption clips for each word/phrase.
    Returns list of (image, start_time, end_time) tuples.
    """
    from PIL import Image
    
    style_config = STYLES.get(style, STYLES["bold_white"])
    timestamps = generate_word_timestamps(text, duration)
    
    captions = []
    words_per_display = 5  # Show 5 words at a time
    
    for i in range(0, len(timestamps), words_per_display):
        chunk = timestamps[i:i + words_per_display]
        chunk_text = " ".join([w["word"] for w in chunk])
        
        start_time = chunk[0]["start"]
        end_time = chunk[-1]["end"]
        
        img = create_caption_image(
            chunk_text,
            width=width,
            font_size=style_config["font_size"],
            color=style_config["color"],
            bg_color=style_config["bg_color"],
            shadow=style_config["shadow"],
        )
        
        captions.append({
            "image": img,
            "start": start_time,
            "end": end_time,
            "position": style_config["position"],
        })
    
    return captions


# ─── Save Captions ────────────────────────────────────────────────────────────
def save_srt(srt_content: str, output_path: str):
    """Save SRT content to file."""
    Path(output_path).write_text(srt_content, encoding="utf-8")
    logger.info(f"SRT saved: {output_path}")


def save_word_timestamps(timestamps: list, output_path: str):
    """Save word timestamps as JSON."""
    import json
    Path(output_path).write_text(json.dumps(timestamps, indent=2))
    logger.info(f"Timestamps saved: {output_path}")
