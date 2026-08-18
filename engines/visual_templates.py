"""
Visual Template System — Configurable visual styles for Instagram Reels.

Templates define:
- Color schemes (background, text, accent, highlight)
- Layout (text position, size, spacing)
- Effects (gradients, overlays, borders, shadows)
- Animations (transitions, reveals)
- Branding (watermark position, logo, intro/outro)

Templates are reusable across all agents.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict

logger = logging.getLogger("visual_templates")

DATA_DIR = Path(__file__).parent.parent / "data"
TEMPLATES_DIR = DATA_DIR / "templates"
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# ─── Built-in Templates ──────────────────────────────────────────────────────

BUILTIN_TEMPLATES = {
    "dark_modern": {
        "name": "Dark Modern",
        "description": "Dark background with purple/pink accents — professional tech look",
        "category": "modern",
        "colors": {
            "background": "#0a0a0f",
            "background_gradient": ["#0a0a0f", "#111118"],
            "text_primary": "#fafafa",
            "text_secondary": "#a1a1aa",
            "accent_primary": "#7c3aed",
            "accent_secondary": "#ec4899",
            "highlight": "#7c3aed",
            "border": "#1e1e2a",
        },
        "layout": {
            "text_align": "center",
            "text_position": "center",
            "text_max_width": 0.85,
            "padding_x": 60,
            "padding_y": 40,
            "line_spacing": 1.4,
        },
        "typography": {
            "title_font_size": 56,
            "body_font_size": 38,
            "caption_font_size": 32,
            "font_weight": "bold",
            "text_shadow": True,
            "shadow_color": "#000000",
            "shadow_offset": 2,
        },
        "effects": {
            "background_overlay": True,
            "overlay_opacity": 0.4,
            "vignette": True,
            "vignette_strength": 0.3,
            "noise_texture": False,
        },
        "branding": {
            "watermark_position": "bottom_right",
            "watermark_opacity": 0.5,
            "watermark_size": 24,
        },
    },
    
    "bright_energy": {
        "name": "Bright Energy",
        "description": "Bright gradient background — fitness, motivation, lifestyle",
        "category": "energetic",
        "colors": {
            "background": "#ff6b35",
            "background_gradient": ["#ff6b35", "#f7931e"],
            "text_primary": "#ffffff",
            "text_secondary": "#fff5e6",
            "accent_primary": "#ffffff",
            "accent_secondary": "#ff6b35",
            "highlight": "#ffffff",
            "border": "#ff8c5a",
        },
        "layout": {
            "text_align": "center",
            "text_position": "center",
            "text_max_width": 0.80,
            "padding_x": 50,
            "padding_y": 50,
            "line_spacing": 1.3,
        },
        "typography": {
            "title_font_size": 60,
            "body_font_size": 42,
            "caption_font_size": 36,
            "font_weight": "bold",
            "text_shadow": True,
            "shadow_color": "#00000080",
            "shadow_offset": 3,
        },
        "effects": {
            "background_overlay": False,
            "vignette": False,
        },
        "branding": {
            "watermark_position": "bottom_right",
            "watermark_opacity": 0.6,
            "watermark_size": 22,
        },
    },
    
    "clean_minimal": {
        "name": "Clean Minimal",
        "description": "White background with subtle accents — education, business",
        "category": "minimal",
        "colors": {
            "background": "#ffffff",
            "background_gradient": ["#f8f9fa", "#ffffff"],
            "text_primary": "#1a1a2e",
            "text_secondary": "#6c757d",
            "accent_primary": "#2563eb",
            "accent_secondary": "#3b82f6",
            "highlight": "#dbeafe",
            "border": "#e5e7eb",
        },
        "layout": {
            "text_align": "left",
            "text_position": "center",
            "text_max_width": 0.80,
            "padding_x": 60,
            "padding_y": 40,
            "line_spacing": 1.5,
        },
        "typography": {
            "title_font_size": 52,
            "body_font_size": 36,
            "caption_font_size": 30,
            "font_weight": "semi_bold",
            "text_shadow": False,
        },
        "effects": {
            "background_overlay": False,
            "vignette": False,
            "noise_texture": False,
        },
        "branding": {
            "watermark_position": "bottom_right",
            "watermark_opacity": 0.3,
            "watermark_size": 20,
        },
    },
    
    "neon_glow": {
        "name": "Neon Glow",
        "description": "Dark background with neon glow effects — gaming, tech, music",
        "category": "modern",
        "colors": {
            "background": "#0d0221",
            "background_gradient": ["#0d0221", "#150734"],
            "text_primary": "#e0e0ff",
            "text_secondary": "#8888cc",
            "accent_primary": "#00ff88",
            "accent_secondary": "#ff00ff",
            "highlight": "#00ff88",
            "border": "#2a1f5e",
        },
        "layout": {
            "text_align": "center",
            "text_position": "center",
            "text_max_width": 0.85,
            "padding_x": 50,
            "padding_y": 40,
            "line_spacing": 1.4,
        },
        "typography": {
            "title_font_size": 54,
            "body_font_size": 40,
            "caption_font_size": 34,
            "font_weight": "bold",
            "text_shadow": True,
            "shadow_color": "#00ff8840",
            "shadow_offset": 4,
        },
        "effects": {
            "background_overlay": True,
            "overlay_opacity": 0.3,
            "glow_effect": True,
            "glow_color": "#00ff88",
            "glow_radius": 20,
        },
        "branding": {
            "watermark_position": "bottom_right",
            "watermark_opacity": 0.5,
            "watermark_size": 22,
        },
    },
    
    "warm_lifestyle": {
        "name": "Warm Lifestyle",
        "description": "Warm tones — food, travel, beauty, wellness",
        "category": "warm",
        "colors": {
            "background": "#fdf6ec",
            "background_gradient": ["#fdf6ec", "#f5e6d0"],
            "text_primary": "#3d2b1f",
            "text_secondary": "#8b7355",
            "accent_primary": "#d4a574",
            "accent_secondary": "#e8c9a0",
            "highlight": "#fef3c7",
            "border": "#e8d5c0",
        },
        "layout": {
            "text_align": "center",
            "text_position": "center",
            "text_max_width": 0.80,
            "padding_x": 50,
            "padding_y": 50,
            "line_spacing": 1.5,
        },
        "typography": {
            "title_font_size": 50,
            "body_font_size": 36,
            "caption_font_size": 30,
            "font_weight": "medium",
            "text_shadow": False,
        },
        "effects": {
            "background_overlay": False,
            "vignette": True,
            "vignette_strength": 0.15,
        },
        "branding": {
            "watermark_position": "bottom_right",
            "watermark_opacity": 0.4,
            "watermark_size": 20,
        },
    },
    
    "bold_statements": {
        "name": "Bold Statements",
        "description": "High contrast, big text — motivation, quotes, impact",
        "category": "bold",
        "colors": {
            "background": "#000000",
            "background_gradient": ["#000000", "#1a1a1a"],
            "text_primary": "#ffffff",
            "text_secondary": "#cccccc",
            "accent_primary": "#ff0000",
            "accent_secondary": "#ff4444",
            "highlight": "#ff0000",
            "border": "#333333",
        },
        "layout": {
            "text_align": "center",
            "text_position": "center",
            "text_max_width": 0.90,
            "padding_x": 40,
            "padding_y": 40,
            "line_spacing": 1.2,
        },
        "typography": {
            "title_font_size": 64,
            "body_font_size": 48,
            "caption_font_size": 40,
            "font_weight": "extra_bold",
            "text_shadow": True,
            "shadow_color": "#ff000060",
            "shadow_offset": 3,
        },
        "effects": {
            "background_overlay": False,
            "vignette": True,
            "vignette_strength": 0.4,
        },
        "branding": {
            "watermark_position": "bottom_right",
            "watermark_opacity": 0.5,
            "watermark_size": 24,
        },
    },
}


class VisualTemplateSystem:
    """
    Manage and apply visual templates to videos.
    
    Usage:
        ts = VisualTemplateSystem()
        
        # Get built-in template
        template = ts.get_template("dark_modern")
        
        # Create custom template
        ts.save_template("my_brand", {...})
        
        # List all templates
        all_templates = ts.list_templates()
        
        # Apply template to video
        result = ts.apply_template("dark_modern", video_path, output_path)
    """
    
    def __init__(self):
        self._ensure_dirs()
        self._init_builtin_templates()
    
    def _ensure_dirs(self):
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    
    def _init_builtin_templates(self):
        """Save built-in templates if not already present."""
        for key, template in BUILTIN_TEMPLATES.items():
            filepath = TEMPLATES_DIR / f"{key}.json"
            if not filepath.exists():
                filepath.write_text(json.dumps(template, indent=2))
    
    # ─── CRUD ─────────────────────────────────────────────────────────────────
    
    def get_template(self, name: str) -> dict:
        """Get a template by name."""
        filepath = TEMPLATES_DIR / f"{name}.json"
        if filepath.exists():
            return json.loads(filepath.read_text())
        return {"error": f"Template '{name}' not found"}
    
    def save_template(self, name: str, template: dict) -> dict:
        """Save a custom template."""
        template["name"] = template.get("name", name)
        template["category"] = template.get("category", "custom")
        template["created_at"] = datetime.now().isoformat()
        
        filepath = TEMPLATES_DIR / f"{name}.json"
        filepath.write_text(json.dumps(template, indent=2))
        
        logger.info(f"Template saved: {name}")
        return {"success": True, "name": name}
    
    def delete_template(self, name: str) -> dict:
        """Delete a custom template (cannot delete built-ins)."""
        if name in BUILTIN_TEMPLATES:
            return {"error": "Cannot delete built-in template"}
        
        filepath = TEMPLATES_DIR / f"{name}.json"
        if filepath.exists():
            filepath.unlink()
            return {"success": True}
        return {"error": "Template not found"}
    
    def list_templates(self) -> list:
        """List all available templates."""
        templates = []
        for filepath in TEMPLATES_DIR.glob("*.json"):
            data = json.loads(filepath.read_text())
            templates.append({
                "name": filepath.stem,
                "display_name": data.get("name", filepath.stem),
                "category": data.get("category", "custom"),
                "description": data.get("description", ""),
                "is_builtin": filepath.stem in BUILTIN_TEMPLATES,
            })
        return sorted(templates, key=lambda t: (not t["is_builtin"], t["name"]))
    
    def get_templates_by_category(self, category: str) -> list:
        """Get templates filtered by category."""
        all_templates = self.list_templates()
        return [t for t in all_templates if t["category"] == category]
    
    # ─── Apply Template ───────────────────────────────────────────────────────
    
    def apply_template(self, template_name: str, video_path: str, output_path: str,
                       text: str = "", title: str = "") -> dict:
        """
        Apply a visual template to a video.
        
        Adds:
        - Background overlay (if configured)
        - Title text
        - Body text
        - Watermark/branding
        
        Uses FFmpeg + Pillow for rendering.
        """
        from PIL import Image, ImageDraw, ImageFont
        
        template = self.get_template(template_name)
        if "error" in template:
            return template
        
        # Get video info
        import subprocess
        probe = subprocess.run([
            "ffprobe", "-v", "quiet", "-show_entries", "stream=width,height",
            "-of", "csv=p=0", "-select_streams", "v:0", video_path
        ], capture_output=True, text=True)
        
        dims = probe.stdout.strip().split(",")
        width = int(dims[0]) if dims else 1080
        height = int(dims[1]) if len(dims) > 1 else 1920
        
        colors = template.get("colors", {})
        layout = template.get("layout", {})
        typo = template.get("typography", {})
        effects = template.get("effects", {})
        branding = template.get("branding", {})
        
        # Create overlay frame
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Background overlay
        if effects.get("background_overlay"):
            opacity = int(effects.get("overlay_opacity", 0.3) * 255)
            draw.rectangle([0, 0, width, height], fill=(0, 0, 0, opacity))
        
        # Vignette effect
        if effects.get("vignette"):
            strength = effects.get("vignette_strength", 0.3)
            for i in range(int(min(width, height) * 0.4)):
                alpha = int(strength * 255 * (1 - i / (min(width, height) * 0.4)))
                draw.rectangle([i, i, width - i, height - i], outline=(0, 0, 0, alpha))
        
        # Title text
        if title:
            font_size = typo.get("title_font_size", 56)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            except Exception:
                font = ImageFont.load_default()
            
            # Word wrap title
            max_width = int(width * layout.get("text_max_width", 0.85))
            lines = self._wrap_text(title, font, max_width, draw)
            
            # Position
            line_height = font_size * layout.get("line_spacing", 1.4)
            total_height = len(lines) * line_height
            
            if layout.get("text_position") == "top":
                start_y = int(height * 0.15)
            elif layout.get("text_position") == "bottom":
                start_y = int(height * 0.85 - total_height)
            else:
                start_y = int((height - total_height) / 2)
            
            text_color = self._hex_to_rgb(colors.get("text_primary", "#ffffff"))
            shadow_color = self._hex_to_rgb(colors.get("accent_primary", "#7c3aed"))
            
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                
                if layout.get("text_align") == "left":
                    x = layout.get("padding_x", 60)
                elif layout.get("text_align") == "right":
                    x = width - text_width - layout.get("padding_x", 60)
                else:
                    x = (width - text_width) // 2
                
                y = start_y + i * line_height
                
                # Text shadow
                if typo.get("text_shadow"):
                    offset = typo.get("shadow_offset", 2)
                    draw.text((x + offset, y + offset), line, font=font, fill=(*shadow_color, 100))
                
                draw.text((x, y), line, font=font, fill=(*text_color, 255))
        
        # Body text
        if text and text != title:
            font_size = typo.get("body_font_size", 38)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            except Exception:
                font = ImageFont.load_default()
            
            max_width = int(width * layout.get("text_max_width", 0.85))
            lines = self._wrap_text(text, font, max_width, draw)
            
            line_height = font_size * layout.get("line_spacing", 1.4)
            total_height = len(lines) * line_height
            start_y = int((height - total_height) / 2 + (typo.get("title_font_size", 56) * 1.5 if title else 0))
            
            text_color = self._hex_to_rgb(colors.get("text_primary", "#ffffff"))
            
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x = (width - text_width) // 2
                y = start_y + i * line_height
                draw.text((x, y), line, font=font, fill=(*text_color, 255))
        
        # Watermark
        watermark = branding.get("watermark_text", "")
        if watermark:
            wm_size = branding.get("watermark_size", 22)
            try:
                wm_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", wm_size)
            except Exception:
                wm_font = ImageFont.load_default()
            
            wm_color = self._hex_to_rgb(colors.get("text_secondary", "#a1a1aa"))
            wm_opacity = int(branding.get("watermark_opacity", 0.5) * 255)
            
            bbox = draw.textbbox((0, 0), watermark, font=wm_font)
            wm_width = bbox[2] - bbox[0]
            
            pos = branding.get("watermark_position", "bottom_right")
            if pos == "bottom_right":
                x = width - wm_width - 20
                y = height - wm_size - 20
            elif pos == "bottom_left":
                x = 20
                y = height - wm_size - 20
            elif pos == "top_right":
                x = width - wm_width - 20
                y = 20
            else:
                x = (width - wm_width) // 2
                y = height - wm_size - 20
            
            draw.text((x, y), watermark, font=wm_font, fill=(*wm_color, wm_opacity))
        
        # Save overlay
        overlay_path = Path(output_path).parent / "template_overlay.png"
        overlay.save(str(overlay_path))
        
        # Overlay on video using FFmpeg
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", str(overlay_path),
            "-filter_complex", "[0:v][1:v]overlay=0:0:shortest=1",
            "-c:v", "libx264", "-crf", "23",
            "-c:a", "copy",
            output_path
        ]
        
        subprocess.run(ffmpeg_cmd, capture_output=True, timeout=120)
        
        # Cleanup
        overlay_path.unlink(missing_ok=True)
        
        logger.info(f"Template '{template_name}' applied to {output_path}")
        return {
            "success": True,
            "template": template_name,
            "output_path": output_path,
        }
    
    # ─── Utilities ────────────────────────────────────────────────────────────
    
    def _wrap_text(self, text: str, font, max_width: int, draw) -> list:
        """Word-wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] > max_width and current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                current_line.append(word)
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return lines
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 6:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        elif len(hex_color) == 8:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4, 6))
        return (255, 255, 255)


# ─── Convenience ──────────────────────────────────────────────────────────────

def get_template(name: str) -> dict:
    ts = VisualTemplateSystem()
    return ts.get_template(name)

def list_templates() -> list:
    ts = VisualTemplateSystem()
    return ts.list_templates()

def apply_template(template_name: str, video_path: str, output_path: str, **kwargs) -> dict:
    ts = VisualTemplateSystem()
    return ts.apply_template(template_name, video_path, output_path, **kwargs)

def save_custom_template(name: str, template: dict) -> dict:
    ts = VisualTemplateSystem()
    return ts.save_template(name, template)
