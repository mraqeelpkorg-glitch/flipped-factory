"""
Podcast Video Renderer — Renders podcast clips into Instagram-ready videos.

Templates:
1. SPEAKER_FOCUS — Full-screen speaker with captions at bottom
2. SPLIT_SCREEN — Speaker on top, captions on bottom
3. DYNAMIC_SPEAKER — Auto-zoom on speaker, dynamic captions

All output: 1080x1920, 9:16, H.264, AAC

Uses MoviePy + Pillow for text overlays (no FFmpeg drawtext needed).
"""
import subprocess
import os
import json
import logging
import tempfile
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("podcast_renderer")

BASE_DIR = Path(__file__).parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "videos" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

TEMPLATES = {
    "SPEAKER_FOCUS": {
        "name": "Speaker Focus",
        "description": "Full-screen speaker with captions at bottom",
        "caption_position": "bottom",
        "font_size": 48,
    },
    "SPLIT_SCREEN": {
        "name": "Split Screen",
        "description": "Speaker on top half, captions on bottom half",
        "caption_position": "bottom",
        "font_size": 42,
    },
    "DYNAMIC_SPEAKER": {
        "name": "Dynamic Speaker",
        "description": "Auto-zoom on speaker with dynamic captions",
        "caption_position": "center",
        "font_size": 52,
    },
}

# Caption styling
CAPTION_STYLES = {
    "default": {
        "font_color": "white",
        "font_size": 48,
        "bg_color": (0, 0, 0, 160),  # RGBA
        "border_color": "black",
        "border_width": 2,
        "position": "bottom",
    },
    "bold": {
        "font_color": "white",
        "font_size": 56,
        "bg_color": (0, 0, 0, 200),
        "border_color": "yellow",
        "border_width": 3,
        "position": "bottom",
    },
    "minimal": {
        "font_color": "white",
        "font_size": 40,
        "bg_color": None,
        "border_color": "black",
        "border_width": 2,
        "position": "bottom",
    },
    "highlight": {
        "font_color": "yellow",
        "font_size": 48,
        "bg_color": (0, 0, 0, 180),
        "border_color": "white",
        "border_width": 2,
        "position": "bottom",
    },
}


def get_video_info(video_path: str) -> dict:
    """Get video metadata."""
    try:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            video_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        info = json.loads(result.stdout)

        video_stream = None
        for s in info.get("streams", []):
            if s.get("codec_type") == "video":
                video_stream = s
                break

        if not video_stream:
            return {"width": 0, "height": 0, "duration": 0, "fps": 30}

        fps_str = video_stream.get("r_frame_rate", "30/1")
        try:
            num, den = fps_str.split("/")
            fps = float(num) / float(den) if float(den) > 0 else 30
        except Exception:
            fps = 30

        return {
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "duration": float(info.get("format", {}).get("duration", 0)),
            "fps": fps,
            "codec": video_stream.get("codec_name", "unknown"),
        }
    except Exception as e:
        logger.error(f"Failed to get video info: {e}")
        return {"width": 0, "height": 0, "duration": 0, "fps": 30}


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    """Get a font, falling back gracefully."""
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _create_caption_overlay(
    width: int,
    height: int,
    text: str,
    style: dict,
    template_config: dict,
    brand_name: str = "",
) -> Image.Image:
    """
    Create a transparent PNG overlay with caption text and optional brand.

    Returns RGBA Image of size (width, height).
    """
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_size = style.get("font_size", 48)
    font = _get_font(font_size)
    border_width = style.get("border_width", 2)
    bg_color = style.get("bg_color")

    # Word-wrap text
    max_chars_per_line = 30
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        if len(test_line) > max_chars_per_line and current_line:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)

    # Measure text block
    line_heights = []
    line_widths = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_widths.append(bbox[2] - bbox[0])
        line_heights.append(bbox[3] - bbox[1])

    total_text_height = sum(line_heights) + (len(lines) - 1) * 8
    max_text_width = max(line_widths) if line_widths else 0

    # Position
    padding = 16
    position = template_config.get("caption_position", "bottom")

    if position == "center":
        y_start = (height - total_text_height) // 2 + int(height * 0.15)
    else:  # bottom
        y_start = height - total_text_height - 160

    # Draw background box
    if bg_color:
        box_x1 = max(0, (width - max_text_width) // 2 - padding)
        box_y1 = max(0, y_start - padding)
        box_x2 = min(width, (width + max_text_width) // 2 + padding)
        box_y2 = min(height, y_start + total_text_height + padding)
        draw.rounded_rectangle(
            [box_x1, box_y1, box_x2, box_y2],
            radius=8,
            fill=bg_color,
        )

    # Draw text with border
    x_center = width // 2
    y = y_start
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = x_center - tw // 2

        # Border (outline)
        if border_width > 0:
            bc = style.get("border_color", "black")
            for dx in range(-border_width, border_width + 1):
                for dy in range(-border_width, border_width + 1):
                    if dx * dx + dy * dy <= border_width * border_width:
                        draw.text((x + dx, y + dy), line, font=font, fill=bc)

        # Main text
        fc = style.get("font_color", "white")
        draw.text((x, y), line, font=font, fill=fc)
        y += line_heights[i] + 8

    # Brand watermark
    if brand_name:
        brand_font = _get_font(24)
        draw.text((20, height - 50), brand_name, font=brand_font, fill=(255, 255, 255, 180))

    return img


def render_clip(
    source_path: str,
    start: float,
    end: float,
    template: str = "SPEAKER_FOCUS",
    caption_text: str = "",
    caption_style: str = "default",
    output_path: str = None,
    brand_name: str = "",
    brand_color: str = "#a78bfa",
) -> dict:
    """
    Render a podcast clip using FFmpeg for crop/scale + Pillow for text overlay.

    Two-pass approach:
    1. FFmpeg: crop source to 9:16 vertical, encode to temp file
    2. Pillow: render text overlay as transparent PNG
    3. FFmpeg: overlay PNG on video

    Returns:
        {success, path, duration, file_size}
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(PROCESSED_DIR / f"clip_{template.lower()}_{timestamp}.mp4")

    template_config = TEMPLATES.get(template, TEMPLATES["SPEAKER_FOCUS"])
    style = CAPTION_STYLES.get(caption_style, CAPTION_STYLES["default"])

    duration = end - start
    tmp_dir = tempfile.mkdtemp(prefix="podcast_render_")
    temp_video = os.path.join(tmp_dir, "cropped.mp4")
    temp_overlay = os.path.join(tmp_dir, "overlay.png")

    try:
        logger.info(f"Rendering {template} clip: {start:.1f}s - {end:.1f}s")

        # ── PASS 1: FFmpeg crop + scale ──────────────────────────────
        if template == "SPLIT_SCREEN":
            crop_filter = "crop=iw:ih/2:0:0,scale=1080:960,pad=1080:1920:0:0:black"
        else:
            crop_filter = "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920"

        cmd_crop = [
            "ffmpeg",
            "-ss", str(start),
            "-i", source_path,
            "-t", str(duration),
            "-vf", crop_filter,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-y", temp_video,
        ]

        result = subprocess.run(cmd_crop, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            logger.error(f"FFmpeg crop failed: {result.stderr[:300]}")
            return {"success": False, "error": f"Crop failed: {result.stderr[:200]}"}

        if not os.path.exists(temp_video):
            return {"success": False, "error": "Cropped video not created"}

        # ── PASS 2: Pillow text overlay ──────────────────────────────
        if caption_text:
            overlay = _create_caption_overlay(
                1080, 1920, caption_text, style, template_config, brand_name
            )
            overlay.save(temp_overlay, "PNG")

            # ── PASS 3: FFmpeg overlay ───────────────────────────────
            cmd_overlay = [
                "ffmpeg",
                "-i", temp_video,
                "-i", temp_overlay,
                "-filter_complex", "[0:v][1:v]overlay=0:0[v]",
                "-map", "[v]",
                "-map", "0:a?",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "copy",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                "-y", output_path,
            ]
            result = subprocess.run(cmd_overlay, capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                logger.warning(f"Overlay failed, using cropped video: {result.stderr[:200]}")
                # Fall back to cropped video without text
                import shutil
                shutil.move(temp_video, output_path)
            else:
                # Clean up temp video after successful overlay
                if os.path.exists(temp_video):
                    os.remove(temp_video)
        else:
            # No caption — just move cropped video to output
            import shutil
            shutil.move(temp_video, output_path)

        if not os.path.exists(output_path):
            return {"success": False, "error": "Output file not created"}

        file_size = os.path.getsize(output_path)
        info = get_video_info(output_path)

        logger.info(f"Rendered: {output_path} ({file_size/1024:.1f}KB, {info['duration']:.1f}s)")

        return {
            "success": True,
            "path": output_path,
            "duration": info["duration"],
            "file_size": file_size,
            "width": info["width"],
            "height": info["height"],
            "template": template,
        }

    except Exception as e:
        logger.error(f"Render failed: {e}")
        return {"success": False, "error": str(e)}
    finally:
        # Cleanup temp files
        import shutil
        for f in [temp_video, temp_overlay]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass
        try:
            os.rmdir(tmp_dir)
        except Exception:
            pass


def render_with_audio(
    source_path: str,
    audio_path: str,
    start: float,
    end: float,
    template: str = "SPEAKER_FOCUS",
    caption_text: str = "",
    caption_style: str = "default",
    output_path: str = None,
    brand_name: str = "",
) -> dict:
    """
    Render clip with custom audio track (e.g., TTS voiceover).
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(PROCESSED_DIR / f"clip_audio_{timestamp}.mp4")

    # First render video only
    video_only = output_path.replace(".mp4", "_video.mp4")
    render_result = render_clip(
        source_path, start, end, template, caption_text, caption_style, video_only, brand_name
    )

    if not render_result["success"]:
        return render_result

    # Then merge with audio
    try:
        cmd_merge = [
            "ffmpeg",
            "-i", video_only,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            "-y", output_path,
        ]
        result = subprocess.run(cmd_merge, capture_output=True, text=True, timeout=60)

        # Cleanup video-only file
        if os.path.exists(video_only):
            os.remove(video_only)

        if not os.path.exists(output_path):
            return {"success": False, "error": "Audio merge failed"}

        info = get_video_info(output_path)
        file_size = os.path.getsize(output_path)

        return {
            "success": True,
            "path": output_path,
            "duration": info["duration"],
            "file_size": file_size,
            "width": info["width"],
            "height": info["height"],
            "template": template,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def get_available_templates() -> list:
    """Get list of available templates with their configs."""
    return [
        {"id": k, "name": v["name"], "description": v["description"]}
        for k, v in TEMPLATES.items()
    ]


def get_available_caption_styles() -> list:
    """Get list of available caption styles."""
    return [
        {"id": k, "name": k.title(), "font_size": v["font_size"], "position": v["position"]}
        for k, v in CAPTION_STYLES.items()
    ]
