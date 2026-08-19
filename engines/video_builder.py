"""
Video Builder Pro — Creates professional Instagram Reel videos.
Uses Pillow for frame generation + FFmpeg for final video encoding.
ALL FREE. Vertical 9:16 format.
"""
import random
import math
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("video_builder")

# ─── Constants ────────────────────────────────────────────────────────────────
WIDTH = 1080
HEIGHT = 1920
FPS = 30

# Instagram Safe Zones (from INSTAGRAM_SOURCE_OF_TRUTH.md)
# Top 10% = username/profile (avoid)
# Bottom 15% = captions/buttons (avoid)
# Safe zone: 10-75% vertical
SAFE_ZONE_TOP = int(HEIGHT * 0.10)      # 192px from top
SAFE_ZONE_BOTTOM = int(HEIGHT * 0.85)   # 1632px from top
SAFE_ZONE_HEIGHT = SAFE_ZONE_BOTTOM - SAFE_ZONE_TOP  # 1440px usable

# Text placement limits (with padding)
TEXT_TOP_LIMIT = SAFE_ZONE_TOP + 50      # 242px from top
TEXT_BOTTOM_LIMIT = SAFE_ZONE_BOTTOM - 100  # 1532px from top

THEMES = {
    "purple_pink":   {"g1": (124, 58, 237),  "g2": (236, 72, 153),  "accent": (167, 139, 250)},
    "cyan_blue":     {"g1": (6, 182, 212),   "g2": (59, 130, 246),  "accent": (103, 232, 249)},
    "amber_red":     {"g1": (245, 158, 11),  "g2": (239, 68, 68),   "accent": (251, 191, 36)},
    "green_teal":    {"g1": (16, 185, 129),  "g2": (20, 184, 166),  "accent": (52, 211, 153)},
    "violet_cyan":   {"g1": (139, 92, 246),  "g2": (6, 182, 212),   "accent": (196, 181, 253)},
    "rose_orange":   {"g1": (244, 63, 94),   "g2": (251, 146, 60),  "accent": (253, 164, 175)},
}

EMOJI_MAP = {
    "health_fitness": ["💪", "🔥", "⚡", "🏋️", "🏃", "💥", "🎯", "❤️"],
    "finance_crypto": ["💰", "📈", "🪙", "💎", "🚀", "💸", "📊", "🏦"],
    "tech_ai":        ["🤖", "💻", "🧠", "⚙️", "🔬", "📱", "✨", "🛠️"],
    "ecommerce":      ["🛍️", "🛒", "💳", "📦", "🏷️", "🏪", "🎁", "🔔"],
    "education":      ["📚", "🎓", "📖", "🧠", "💡", "✏️", "📝", "🏫"],
    "motivation":     ["🔥", "💪", "⭐", "🏆", "🎯", "💥", "🦁", "👑"],
    "food_nutrition": ["🥗", "🥑", "🍎", "🥦", "🍳", "🌶️", "🥤", "🍋"],
    "travel":         ["✈️", "🌍", "🗺️", "🏖️", "🏔️", "🌅", "🎒", "🚂"],
    "beauty_skincare": ["✨", "💄", "🌸", "💅", "🧴", "👰", "🌺", "💎"],
    "productivity":   ["⚡", "📋", "🎯", "⏰", "📊", "🚀", "✅", "💼"],
}


# ─── Frame Builders ───────────────────────────────────────────────────────────
def _gradient_bg(w, h, c1, c2):
    """Create gradient background."""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        r = y / h
        color = tuple(int(c1[i] * (1 - r) + c2[i] * r) for i in range(3))
        draw.line([(0, y), (w, y)], fill=color)
    return img


def _draw_circle(draw, cx, cy, radius, color, alpha=60):
    """Draw a semi-transparent circle."""
    for r in range(radius, 0, -2):
        a = int(alpha * (r / radius))
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            fill=(*color, a),
        )


def _draw_decorations(draw, w, h, theme):
    """Add geometric decorations."""
    accent = theme["accent"]
    # Top-right circle
    _draw_circle(draw, w - 80, 200, 160, accent, alpha=30)
    # Bottom-left circle
    _draw_circle(draw, 100, h - 300, 200, accent, alpha=25)
    # Small dots
    for _ in range(15):
        x = random.randint(0, w)
        y = random.randint(0, h)
        r = random.randint(3, 8)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(*accent, random.randint(20, 50)))


def _get_font(size, bold=False):
    """Get a font."""
    from PIL import ImageFont
    paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSMono.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _draw_text_with_outline(draw, x, y, text, font, fill="white", outline="black", outline_width=3):
    """Draw text with outline for readability."""
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx * dx + dy * dy <= outline_width * outline_width:
                draw.text((x + dx, y + dy), text, font=font, fill=outline)
    draw.text((x, y), text, font=font, fill=fill)


def _wrap_text(text, font, max_width, draw):
    """Word-wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        tw, _ = _text_size(draw, test, font)
        if tw <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _clamp_to_safe_zone(y, text_height) -> int:
    """Clamp text position to Instagram safe zone (10-85% vertical)."""
    y = int(y)
    text_height = int(text_height)
    # Ensure text doesn't go above safe zone top
    if y < TEXT_TOP_LIMIT:
        y = TEXT_TOP_LIMIT
    # Ensure text doesn't go below safe zone bottom
    if y + text_height > TEXT_BOTTOM_LIMIT:
        y = TEXT_BOTTOM_LIMIT - text_height
    return y


# ─── Section Frames ───────────────────────────────────────────────────────────
def build_hook_frame(hook_text, theme, emojis, frame_num=0, total_frames=30):
    """Build the hook/intro frame with animated entrance."""
    from PIL import Image, ImageDraw
    import numpy as np

    img = _gradient_bg(WIDTH, HEIGHT, theme["g1"], theme["g2"])
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    _draw_decorations(draw, WIDTH, HEIGHT, theme)

    # Big emoji at top (within safe zone)
    emoji_font = _get_font(120)
    emoji = random.choice(emojis)
    ew, eh = _text_size(draw, emoji, emoji_font)
    emoji_y = _clamp_to_safe_zone(350, eh)
    draw.text(((WIDTH - ew) // 2, emoji_y), emoji, font=emoji_font, fill=(255, 255, 255, 255))

    # Hook text — large, bold, centered (within safe zone)
    font_big = _get_font(72, bold=True)
    lines = _wrap_text(hook_text, font_big, 900, draw)
    y = 600
    for line in lines:
        lw, lh = _text_size(draw, line, font_big)
        y = _clamp_to_safe_zone(y, lh)
        _draw_text_with_outline(draw, (WIDTH - lw) // 2, y, line, font_big, outline_width=4)
        y += lh + 16

    # "Swipe up" hint (within safe zone)
    hint_font = _get_font(36)
    hint = "👆 Watch this"
    hw, hh = _text_size(draw, hint, hint_font)
    hint_y = _clamp_to_safe_zone(HEIGHT - 400, hh)
    draw.text(((WIDTH - hw) // 2, hint_y), hint, font=hint_font, fill=(*theme["accent"], 200))

    # Progress bar at bottom (below safe zone - intentional)
    progress = min(1.0, (frame_num + 1) / max(total_frames, 1))
    bar_y = HEIGHT - 80
    draw.rounded_rectangle([60, bar_y, WIDTH - 60, bar_y + 12], radius=6, fill=(255, 255, 255, 40))
    bar_end = 60 + int((WIDTH - 120) * progress)
    draw.rounded_rectangle([60, bar_y, bar_end, bar_y + 12], radius=6, fill=(255, 255, 255, 220))

    img.paste(overlay, (0, 0), overlay)
    return np.array(img)


def build_body_frame(body_text, section_idx, total_sections, theme, emojis, frame_num=0, total_frames=30):
    """Build a body content frame with numbered section."""
    from PIL import Image, ImageDraw
    import numpy as np

    img = _gradient_bg(WIDTH, HEIGHT, theme["g1"], theme["g2"])
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    _draw_decorations(draw, WIDTH, HEIGHT, theme)

    # Section number badge (within safe zone)
    badge_r = 50
    badge_cx, badge_cy = WIDTH // 2, 320
    badge_cy = _clamp_to_safe_zone(badge_cy, badge_r * 2)
    draw.ellipse(
        [badge_cx - badge_r, badge_cy - badge_r, badge_cx + badge_r, badge_cy + badge_r],
        fill=(*theme["accent"], 220),
    )
    num_font = _get_font(48, bold=True)
    num_text = str(section_idx + 1)
    nw, nh = _text_size(draw, num_text, num_font)
    draw.text((badge_cx - nw // 2, badge_cy - nh // 2 - 4), num_text, font=num_font, fill=(255, 255, 255, 255))

    # Emoji (within safe zone)
    emoji_font = _get_font(80)
    emoji = emojis[section_idx % len(emojis)]
    ew, eh = _text_size(draw, emoji, emoji_font)
    emoji_y = _clamp_to_safe_zone(420, eh)
    draw.text(((WIDTH - ew) // 2, emoji_y), emoji, font=emoji_font, fill=(255, 255, 255, 255))

    # Body text (within safe zone)
    font_med = _get_font(52)
    lines = _wrap_text(body_text, font_med, 880, draw)
    y = 580
    for line in lines[:8]:  # Max 8 lines
        lw, lh = _text_size(draw, line, font_med)
        y = _clamp_to_safe_zone(y, lh)
        _draw_text_with_outline(draw, (WIDTH - lw) // 2, y, line, font_med, outline_width=3)
        y += lh + 14

    # Dots indicator (which section we're on)
    dot_y = HEIGHT - 200
    dot_spacing = 40
    total_dots = total_sections
    start_x = (WIDTH - total_dots * dot_spacing) // 2
    for i in range(total_dots):
        dx = start_x + i * dot_spacing
        r = 8 if i == section_idx else 5
        alpha = 255 if i == section_idx else 80
        color = (255, 255, 255, alpha) if i != section_idx else (*theme["accent"], 255)
        draw.ellipse([dx - r, dot_y - r, dx + r, dot_y + r], fill=color)

    # Progress bar
    overall = (section_idx + frame_num / max(total_frames, 1)) / max(total_sections, 1)
    bar_y = HEIGHT - 80
    draw.rounded_rectangle([60, bar_y, WIDTH - 60, bar_y + 12], radius=6, fill=(255, 255, 255, 40))
    bar_end = 60 + int((WIDTH - 120) * min(1.0, overall))
    draw.rounded_rectangle([60, bar_y, bar_end, bar_y + 12], radius=6, fill=(255, 255, 255, 220))

    img.paste(overlay, (0, 0), overlay)
    return np.array(img)


def build_cta_frame(cta_text, theme, emojis, frame_num=0, total_frames=30):
    """Build the call-to-action / outro frame."""
    from PIL import Image, ImageDraw
    import numpy as np

    img = _gradient_bg(WIDTH, HEIGHT, theme["g2"], theme["g1"])  # Reversed gradient
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    _draw_decorations(draw, WIDTH, HEIGHT, theme)

    # Big emoji (within safe zone)
    emoji_font = _get_font(120)
    emoji = "🚀"
    ew, eh = _text_size(draw, emoji, emoji_font)
    emoji_y = _clamp_to_safe_zone(400, eh)
    draw.text(((WIDTH - ew) // 2, emoji_y), emoji, font=emoji_font, fill=(255, 255, 255, 255))

    # CTA text (within safe zone)
    font_big = _get_font(64, bold=True)
    lines = _wrap_text(cta_text, font_big, 880, draw)
    y = 650
    for line in lines:
        lw, lh = _text_size(draw, line, font_big)
        y = _clamp_to_safe_zone(y, lh)
        _draw_text_with_outline(draw, (WIDTH - lw) // 2, y, line, font_big, outline_width=4)
        y += lh + 16

    # Follow button (within safe zone)
    btn_w, btn_h = 400, 80
    btn_x = (WIDTH - btn_w) // 2
    btn_y = _clamp_to_safe_zone(950, btn_h)
    draw.rounded_rectangle(
        [btn_x, btn_y, btn_x + btn_w, btn_y + btn_h],
        radius=40,
        fill=(*theme["accent"], 230),
    )
    btn_font = _get_font(40, bold=True)
    btn_text = "FOLLOW NOW"
    btw, bth = _text_size(draw, btn_text, btn_font)
    draw.text((btn_x + (btn_w - btw) // 2, btn_y + (btn_h - bth) // 2 - 2),
              btn_text, font=btn_font, fill=(255, 255, 255, 255))

    # Social icons row (within safe zone)
    social_emojis = ["❤️", "💬", "📤", "🔖"]
    social_font = _get_font(48)
    sx = (WIDTH - len(social_emojis) * 100) // 2
    social_y = _clamp_to_safe_zone(1100, 48)
    for i, se in enumerate(social_emojis):
        draw.text((sx + i * 100 + 20, social_y), se, font=social_font, fill=(255, 255, 255, 180))

    # Progress bar (full) - below safe zone, intentional
    bar_y = HEIGHT - 80
    draw.rounded_rectangle([60, bar_y, WIDTH - 60, bar_y + 12], radius=6, fill=(255, 255, 255, 220))

    img.paste(overlay, (0, 0), overlay)
    return np.array(img)


# ─── Main Video Creator ──────────────────────────────────────────────────────
def create_text_video(
    script: dict,
    output_path: str,
    niche: str = "health_fitness",
    font_size: int = 48,
    duration_per_section: dict = None,
):
    """
    Create a professional Instagram Reel video using Pillow + FFmpeg.
    
    script = {
        "hook": "Opening hook...",
        "body": "Main content...",
        "cta": "Call to action...",
        "duration": 30,
        "niche": "health_fitness"
    }
    """
    import subprocess
    import io

    niche = script.get("niche", niche)
    theme = random.choice(list(THEMES.values()))
    emojis = EMOJI_MAP.get(niche, EMOJI_MAP["health_fitness"])

    total_duration = script.get("duration", 30)
    if duration_per_section is None:
        duration_per_section = {
            "hook": min(5, total_duration * 0.15),
            "body": total_duration * 0.70,
            "cta": min(5, total_duration * 0.15),
        }

    # Collect all frames in order: hook → body → cta
    all_frames = []

    # ─── Hook Section ─────────────────────────────────────────────────────
    hook_text = script.get("hook", "")
    if hook_text:
        dur = duration_per_section.get("hook", 4)
        frames_needed = int(dur * FPS)
        hook_frames = []
        for f in range(min(frames_needed, FPS * 2)):
            frame = build_hook_frame(hook_text, theme, emojis, f, frames_needed)
            hook_frames.append(frame)
        if hook_frames:
            # Cycle frames for remaining duration
            all_frames.extend(hook_frames)
            remaining = max(0, frames_needed - len(hook_frames))
            all_frames.extend([hook_frames[-1]] * remaining)

    # ─── Body Sections ────────────────────────────────────────────────────
    body_text = script.get("body", "")
    if body_text:
        body_dur = duration_per_section.get("body", 20)
        body_parts = [p.strip() for p in body_text.split("\n") if p.strip()]
        if len(body_parts) < 2:
            import re
            parts = re.split(r'(?=\d+[\.\)])', body_text)
            body_parts = [p.strip() for p in parts if p.strip()]
        if len(body_parts) < 2:
            body_parts = [body_text]

        per_part = body_dur / len(body_parts)
        for idx, part in enumerate(body_parts):
            dur = per_part
            frames_needed = int(dur * FPS)
            body_frames = []
            for f in range(min(frames_needed, FPS * 2)):
                frame = build_body_frame(part, idx, len(body_parts), theme, emojis, f, frames_needed)
                body_frames.append(frame)
            if body_frames:
                all_frames.extend(body_frames)
                remaining = max(0, frames_needed - len(body_frames))
                all_frames.extend([body_frames[-1]] * remaining)

    # ─── CTA Section ──────────────────────────────────────────────────────
    cta_text = script.get("cta", "")
    if cta_text:
        dur = duration_per_section.get("cta", 4)
        frames_needed = int(dur * FPS)
        cta_frames = []
        for f in range(min(frames_needed, FPS * 2)):
            frame = build_cta_frame(cta_text, theme, emojis, f, frames_needed)
            cta_frames.append(frame)
        if cta_frames:
            all_frames.extend(cta_frames)
            remaining = max(0, frames_needed - len(cta_frames))
            all_frames.extend([cta_frames[-1]] * remaining)

    # ─── Assemble & Export via FFmpeg ──────────────────────────────────────
    if not all_frames:
        return False

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "fast",
        "-b:v", "5M",
        "-pix_fmt", "yuv420p",
        "-an",
        str(output_path),
    ]

    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        for frame_img in all_frames:
            proc.stdin.write(frame_img.tobytes())
        proc.stdin.close()
        proc.wait(timeout=30)
        if proc.returncode == 0:
            logger.info(f"Video created: {output_path} ({len(all_frames)} frames, {len(all_frames)/FPS:.1f}s)")
            return True
        else:
            logger.error(f"FFmpeg error: {proc.stderr.read().decode()[:200]}")
            return False
    except Exception as e:
        logger.error(f"Video creation failed: {e}")
        return False


# ─── Slideshow ───────────────────────────────────────────────────────────────
def create_slideshow_video(
    images: list,
    output_path: str,
    duration_per_image: float = 3.0,
    transition: str = "fade",
):
    """Create a slideshow video from a list of images using Pillow + FFmpeg."""
    import subprocess
    from PIL import Image as PILImage

    frames = []
    for img_path in images:
        try:
            if isinstance(img_path, str):
                img = PILImage.open(img_path).resize((WIDTH, HEIGHT))
            else:
                img = img_path.resize((WIDTH, HEIGHT))
            # Convert to RGB if needed
            if img.mode != "RGB":
                img = img.convert("RGB")
            # Duplicate frame for duration
            n_frames = int(duration_per_image * FPS)
            frames.extend([img] * n_frames)
        except Exception as e:
            logger.warning(f"Failed to load image: {e}")

    if not frames:
        return False

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264", "-preset", "fast", "-b:v", "5M",
        "-pix_fmt", "yuv420p", "-an", str(output_path),
    ]

    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        for frame_img in frames:
            proc.stdin.write(frame_img.tobytes())
        proc.stdin.close()
        proc.wait(timeout=60)
        return proc.returncode == 0
    except Exception as e:
        logger.error(f"Slideshow creation failed: {e}")
        return False


# ─── Audio Overlay ────────────────────────────────────────────────────────────
def add_audio_to_video(video_path: str, audio_path: str, output_path: str):
    """Add audio track to a video using FFmpeg."""
    import subprocess

    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            "-movflags", "+faststart",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Failed to add audio: {e}")
        return False


# ─── Utility ──────────────────────────────────────────────────────────────────
def get_video_info(video_path: str) -> dict:
    """Get video metadata using ffprobe."""
    import subprocess
    import json

    try:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            video_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            return {"error": f"ffprobe failed: {result.stderr[:200]}"}
        
        info = json.loads(result.stdout)
        fmt = info.get("format", {})
        return {
            "duration": float(fmt.get("duration", 0)),
            "fps": 30,  # default, parse from stream if needed
            "size": [1080, 1920],  # default
            "filename": Path(video_path).name,
        }
    except Exception as e:
        return {"error": str(e)}
