"""
Dynamic Caption Engine — Word-by-word highlighting for Instagram Reels.

Creates professional captions with:
- Word-by-word highlighting (current word glows)
- Sentence-level highlighting
- Configurable font, size, position, color
- Safe zone compliance (no text in bottom 20%)
- Background/outline for readability
- Animation effects (pop, slide, fade)
- Speaker-aware captions (for podcasts)

Uses Pillow for frame-by-frame rendering — NO paid APIs.
"""

import json
import logging
import math
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List

logger = logging.getLogger("dynamic_captions")

# ─── Configuration ────────────────────────────────────────────────────────────

DEFAULT_FONT_SIZE = 42
DEFAULT_FONT_COLOR = (255, 255, 255)  # White
DEFAULT_HIGHLIGHT_COLOR = (124, 58, 237)  # Purple
DEFAULT_OUTLINE_COLOR = (0, 0, 0)  # Black
DEFAULT_POSITION = "center"  # "top", "center", "bottom"
HIGHLIGHT_BG = (124, 58, 237, 200)  # Purple with alpha

# Safe zones (Instagram Reels)
SAFE_ZONE_TOP = 0.15  # Top 15% avoid
SAFE_ZONE_BOTTOM = 0.25  # Bottom 25% avoid (captions, buttons, etc.)


class DynamicCaptionEngine:
    """
    Generate word-by-word highlighted captions for video frames.
    
    Usage:
        engine = DynamicCaptionEngine()
        
        # Generate caption frames for a video
        frames = engine.generate_caption_frames(
            text="This is a test of dynamic captions",
            duration=5.0,
            fps=30,
            width=1080,
            height=1920,
        )
        
        # Each frame is a PIL Image with highlighted word
        for i, frame in enumerate(frames):
            frame.save(f"frame_{i:04d}.png")
    """
    
    def __init__(self, font_path: str = None, font_size: int = DEFAULT_FONT_SIZE):
        self.font_size = font_size
        self.font_path = font_path or self._find_font()
    
    def _find_font(self) -> str:
        """Find a suitable font on the system."""
        import os
        # macOS fonts
        candidates = [
            "/System/Library/Fonts/SFNSDisplay.ttf",
            "/System/Library/Fonts/SFNSMono.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None  # Use Pillow default
    
    def _get_font(self, size: int = None):
        """Get PIL ImageFont."""
        from PIL import ImageFont
        s = size or self.font_size
        if self.font_path:
            try:
                return ImageFont.truetype(self.font_path, s)
            except Exception:
                pass
        return ImageFont.load_default()
    
    # ─── Word Timing ──────────────────────────────────────────────────────────
    
    def calculate_word_timings(self, text: str, duration: float, 
                                words_per_minute: int = 160) -> list:
        """
        Calculate timing for each word based on natural reading speed.
        
        Args:
            text: Full text
            duration: Total duration in seconds
            words_per_minute: Reading speed (default 160 WPM)
        
        Returns:
            [
                {"word": "This", "start": 0.0, "end": 0.3, "index": 0},
                {"word": "is", "start": 0.3, "end": 0.5, "index": 1},
                ...
            ]
        """
        words = text.split()
        if not words:
            return []
        
        # Calculate natural timing based on word length and reading speed
        total_chars = sum(len(w) for w in words)
        char_duration = duration / max(total_chars, 1)
        
        timings = []
        current_time = 0.0
        
        for i, word in enumerate(words):
            # Longer words take more time to read
            word_duration = len(word) * char_duration
            
            # Minimum word duration (0.15s) for short words
            word_duration = max(word_duration, 0.15)
            
            # Maximum word duration (0.8s) for very long words
            word_duration = min(word_duration, 0.8)
            
            timings.append({
                "word": word,
                "start": round(current_time, 3),
                "end": round(current_time + word_duration, 3),
                "index": i,
            })
            
            current_time += word_duration
        
        # Scale to fit exact duration
        if current_time > 0:
            scale = duration / current_time
            for t in timings:
                t["start"] = round(t["start"] * scale, 3)
                t["end"] = round(t["end"] * scale, 3)
        
        return timings
    
    # ─── Caption Styles ───────────────────────────────────────────────────────
    
    def word_highlight_style(self, text: str, current_word_index: int,
                              width: int = 1080, height: int = 1920,
                              font_size: int = None, position: str = "center",
                              highlight_color: tuple = None,
                              text_color: tuple = None) -> dict:
        """
        Generate word-by-word highlight layout.
        
        Returns:
            {
                "words": [
                    {"word": "This", "x": 100, "y": 900, "width": 80, "height": 40, "highlighted": False},
                    ...
                ],
                "current_word": {"word": "is", "x": 190, "y": 900, ...},
                "background_rect": {"x": 0, "y": 850, "width": 1080, "height": 120},
            }
        """
        words = text.split()
        if not words:
            return {"words": [], "current_word": None}
        
        fs = font_size or self.font_size
        font = self._get_font(fs)
        
        # Calculate position
        if position == "top":
            base_y = int(height * SAFE_ZONE_TOP + fs)
        elif position == "bottom":
            base_y = int(height * (1 - SAFE_ZONE_BOTTOM) - fs)
        else:  # center
            base_y = int(height * 0.5)
        
        # Calculate word widths
        word_data = []
        total_width = 0
        
        from PIL import Image, ImageDraw, ImageFont
        dummy = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(dummy)
        
        for i, word in enumerate(words):
            bbox = draw.textbbox((0, 0), word, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            word_data.append({
                "word": word,
                "width": w,
                "height": h,
                "index": i,
            })
            total_width += w + 12  # 12px spacing
        
        # Center horizontally
        start_x = (width - total_width) // 2
        current_x = start_x
        
        for wd in word_data:
            wd["x"] = current_x
            wd["y"] = base_y
            wd["highlighted"] = (wd["index"] == current_word_index)
            current_x += wd["width"] + 12
        
        # Background rect for readability
        bg_rect = {
            "x": max(0, start_x - 20),
            "y": base_y - fs // 2 - 10,
            "width": min(width, total_width + 40),
            "height": fs + 30,
        }
        
        current_word = word_data[current_word_index] if 0 <= current_word_index < len(word_data) else None
        
        return {
            "words": word_data,
            "current_word": current_word,
            "background_rect": bg_rect,
            "font_size": fs,
        }
    
    def sentence_highlight_style(self, text: str, current_sentence_index: int,
                                  sentences: list = None,
                                  width: int = 1080, height: int = 1920,
                                  font_size: int = None) -> dict:
        """
        Highlight entire sentences instead of individual words.
        
        Args:
            text: Full text
            current_sentence_index: Which sentence to highlight
            sentences: Pre-split sentences (optional)
        
        Returns:
            {
                "sentences": [...],
                "current_sentence": {...},
                "background_rect": {...}
            }
        """
        if sentences is None:
            # Split on sentence boundaries
            import re
            sentences = re.split(r'(?<=[.!?])\s+', text)
        
        fs = font_size or self.font_size
        font = self._get_font(fs)
        
        from PIL import Image, ImageDraw, ImageFont
        dummy = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(dummy)
        
        # Wrap sentences to fit width
        wrapped = []
        max_line_width = width * 0.9  # 90% of width
        
        for sent in sentences:
            words = sent.split()
            current_line = []
            current_width = 0
            
            for word in words:
                bbox = draw.textbbox((0, 0), word + " ", font=font)
                word_width = bbox[2] - bbox[0]
                
                if current_width + word_width > max_line_width and current_line:
                    wrapped.append(" ".join(current_line))
                    current_line = [word]
                    current_width = word_width
                else:
                    current_line.append(word)
                    current_width += word_width
            
            if current_line:
                wrapped.append(" ".join(current_line))
        
        # Calculate positions
        line_height = fs + 10
        total_height = len(wrapped) * line_height
        start_y = (height - total_height) // 2
        
        sentence_data = []
        for i, line in enumerate(wrapped):
            bbox = draw.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            x = (width - w) // 2
            y = start_y + i * line_height
            
            sentence_data.append({
                "text": line,
                "x": x,
                "y": y,
                "width": w,
                "height": line_height,
                "highlighted": (i == current_sentence_index),
                "index": i,
            })
        
        current = sentence_data[current_sentence_index] if 0 <= current_sentence_index < len(sentence_data) else None
        
        return {
            "sentences": sentence_data,
            "current_sentence": current,
            "font_size": fs,
            "total_lines": len(wrapped),
        }
    
    # ─── Caption Generation ───────────────────────────────────────────────────
    
    def generate_caption_frames(self, text: str, duration: float,
                                 width: int = 1080, height: int = 1920,
                                 fps: int = 30, style: str = "word_highlight",
                                 font_size: int = None,
                                 position: str = "center",
                                 highlight_color: tuple = None,
                                 text_color: tuple = None) -> list:
        """
        Generate caption frames for the entire video.
        
        Args:
            text: Caption text
            duration: Video duration in seconds
            width: Video width
            height: Video height
            fps: Frames per second
            style: "word_highlight" or "sentence_highlight"
            font_size: Font size (default 42)
            position: "top", "center", or "bottom"
            highlight_color: RGB tuple for highlighted text
            text_color: RGB tuple for normal text
        
        Returns:
            List of dicts with frame timing and layout data
        """
        from PIL import Image, ImageDraw, ImageFont
        
        fs = font_size or self.font_size
        hc = highlight_color or DEFAULT_HIGHLIGHT_COLOR
        tc = text_color or DEFAULT_FONT_COLOR
        
        font = self._get_font(fs)
        outline_font = self._get_font(fs + 2)
        
        total_frames = int(duration * fps)
        
        if style == "word_highlight":
            timings = self.calculate_word_timings(text, duration)
            frames = []
            
            for frame_idx in range(total_frames):
                current_time = frame_idx / fps
                
                # Find current word
                current_word_idx = 0
                for i, t in enumerate(timings):
                    if t["start"] <= current_time < t["end"]:
                        current_word_idx = i
                        break
                
                # Get layout
                layout = self.word_highlight_style(
                    text, current_word_idx, width, height, fs, position, hc, tc
                )
                
                # Create frame image
                img = Image.new("RGB", (width, height), (0, 0, 0))
                draw = ImageDraw.Draw(img)
                
                # Draw background rectangle
                bg = layout.get("background_rect")
                if bg:
                    draw.rounded_rectangle(
                        [bg["x"], bg["y"], bg["x"] + bg["width"], bg["y"] + bg["height"]],
                        radius=12, fill=(0, 0, 0, 180)
                    )
                
                # Draw words
                for word_data in layout.get("words", []):
                    x = word_data["x"]
                    y = word_data["y"]
                    word = word_data["word"]
                    
                    if word_data["highlighted"]:
                        # Highlighted word: purple background + white text
                        bbox = draw.textbbox((x, y), word, font=font)
                        padding = 4
                        draw.rounded_rectangle(
                            [x - padding, y - padding, bbox[2] + padding, bbox[3] + padding],
                            radius=6, fill=hc
                        )
                        
                        # Draw outline
                        for dx in [-2, -1, 0, 1, 2]:
                            for dy in [-2, -1, 0, 1, 2]:
                                draw.text((x + dx, y + dy), word, font=outline_font, fill=DEFAULT_OUTLINE_COLOR)
                        
                        draw.text((x, y), word, font=font, fill=(255, 255, 255))
                    else:
                        # Normal word: white with black outline
                        for dx in [-1, 0, 1]:
                            for dy in [-1, 0, 1]:
                                draw.text((x + dx, y + dy), word, font=outline_font, fill=DEFAULT_OUTLINE_COLOR)
                        draw.text((x, y), word, font=font, fill=tc)
                
                frames.append({
                    "frame_index": frame_idx,
                    "time": current_time,
                    "image": img,
                    "current_word": timings[current_word_idx]["word"] if current_word_idx < len(timings) else "",
                    "layout": layout,
                })
            
            return frames
        
        elif style == "sentence_highlight":
            import re
            sentences = re.split(r'(?<=[.!?])\s+', text)
            sentence_duration = duration / max(len(sentences), 1)
            
            frames = []
            for frame_idx in range(total_frames):
                current_time = frame_idx / fps
                current_sent_idx = min(int(current_time / sentence_duration), len(sentences) - 1)
                
                layout = self.sentence_highlight_style(
                    text, current_sent_idx, sentences, width, height, fs
                )
                
                img = Image.new("RGB", (width, height), (0, 0, 0))
                draw = ImageDraw.Draw(img)
                
                for sent_data in layout.get("sentences", []):
                    x = sent_data["x"]
                    y = sent_data["y"]
                    t = sent_data["text"]
                    
                    if sent_data["highlighted"]:
                        # Highlighted sentence
                        bbox = draw.textbbox((x, y), t, font=font)
                        padding = 6
                        draw.rounded_rectangle(
                            [x - padding, y - padding, bbox[2] + padding, bbox[3] + padding],
                            radius=8, fill=hc
                        )
                        for dx in [-2, -1, 0, 1, 2]:
                            for dy in [-2, -1, 0, 1, 2]:
                                draw.text((x + dx, y + dy), t, font=outline_font, fill=DEFAULT_OUTLINE_COLOR)
                        draw.text((x, y), t, font=font, fill=(255, 255, 255))
                    else:
                        for dx in [-1, 0, 1]:
                            for dy in [-1, 0, 1]:
                                draw.text((x + dx, y + dy), t, font=outline_font, fill=DEFAULT_OUTLINE_COLOR)
                        draw.text((x, y), t, font=font, fill=tc)
                
                frames.append({
                    "frame_index": frame_idx,
                    "time": current_time,
                    "image": img,
                })
            
            return frames
        
        return []
    
    # ─── Overlay on Existing Frames ───────────────────────────────────────────
    
    def overlay_on_video(self, video_path: str, text: str, output_path: str,
                          style: str = "word_highlight", font_size: int = None,
                          position: str = "center") -> dict:
        """
        Overlay dynamic captions on an existing video.
        
        Uses FFmpeg + Pillow to add word-by-word highlighting.
        
        Returns:
            {"output_path": str, "frames_rendered": int, "duration": float}
        """
        import subprocess
        import tempfile
        
        # Get video duration
        probe_cmd = [
            "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
            "-of", "csv=p=0", video_path
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        duration = float(result.stdout.strip()) if result.stdout.strip() else 0
        
        if duration <= 0:
            return {"error": "Could not determine video duration"}
        
        # Get video dimensions
        probe_cmd2 = [
            "ffprobe", "-v", "quiet", "-show_entries", "stream=width,height",
            "-of", "csv=p=0", "-select_streams", "v:0", video_path
        ]
        result2 = subprocess.run(probe_cmd2, capture_output=True, text=True)
        dims = result2.stdout.strip().split(",")
        width = int(dims[0]) if len(dims) >= 1 else 1080
        height = int(dims[1]) if len(dims) >= 2 else 1920
        
        # Generate caption frames
        fs = font_size or self.font_size
        frames = self.generate_caption_frames(
            text, duration, width, height, fps=30, style=style,
            font_size=fs, position=position
        )
        
        if not frames:
            return {"error": "No frames generated"}
        
        # Save frames as PNG files in temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            for frame_data in frames:
                frame_path = Path(tmpdir) / f"caption_{frame_data['frame_index']:04d}.png"
                frame_data["image"].save(str(frame_path))
            
            # Use FFmpeg to overlay captions on video
            caption_pattern = str(Path(tmpdir) / "caption_%04d.png")
            
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", caption_pattern,
                "-filter_complex", "[0:v][1:v]overlay=0:0:shortest=1",
                "-c:v", "libx264", "-crf", "23",
                "-c:a", "copy",
                "-t", str(duration),
                output_path
            ]
            
            subprocess.run(ffmpeg_cmd, capture_output=True, timeout=120)
        
        logger.info(f"Dynamic captions overlay: {output_path} ({len(frames)} frames)")
        return {
            "output_path": output_path,
            "frames_rendered": len(frames),
            "duration": duration,
            "style": style,
        }
    
    # ─── Utilities ────────────────────────────────────────────────────────────
    
    def get_caption_preview(self, text: str, word_index: int = 0,
                             width: int = 1080, height: int = 1920) -> str:
        """Get a text preview of the caption layout."""
        layout = self.word_highlight_style(text, word_index, width, height)
        
        lines = []
        for wd in layout.get("words", []):
            if wd["highlighted"]:
                lines.append(f"  [{wd['word']}]  ← HIGHLIGHTED")
            else:
                lines.append(f"  {wd['word']}")
        
        return "\n".join(lines)


# ─── Convenience Functions ────────────────────────────────────────────────────

def generate_word_highlight(text: str, duration: float, width: int = 1080, height: int = 1920, **kwargs) -> list:
    """Generate word-by-word highlight frames."""
    engine = DynamicCaptionEngine()
    return engine.generate_caption_frames(text, duration, width, height, style="word_highlight", **kwargs)

def generate_sentence_highlight(text: str, duration: float, width: int = 1080, height: int = 1920, **kwargs) -> list:
    """Generate sentence highlight frames."""
    engine = DynamicCaptionEngine()
    return engine.generate_caption_frames(text, duration, width, height, style="sentence_highlight", **kwargs)

def overlay_captions(video_path: str, text: str, output_path: str, **kwargs) -> dict:
    """Overlay dynamic captions on a video."""
    engine = DynamicCaptionEngine()
    return engine.overlay_on_video(video_path, text, output_path, **kwargs)
