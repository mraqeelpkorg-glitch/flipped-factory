"""
Instagram Reel Creator - Complete Pipeline
Downloads viral YouTube videos and creates Instagram-ready content
"""
import asyncio
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# Directories
BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "data" / "videos" / "raw"
FRAMES_DIR = RAW_DIR / "frames"
PROCESSED_DIR = BASE_DIR / "data" / "videos" / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
FRAMES_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


class InstagramReelCreator:
    """Create Instagram-ready reels from YouTube videos."""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime('%H%M%S')
    
    def create_reel_from_youtube(
        self,
        youtube_url: str,
        target_language: str = 'hi',
        voice_text: str = "",
        duration: int = 15,
        add_text_overlay: bool = True
    ) -> dict:
        """
        Create Instagram reel from YouTube video.
        
        Args:
            youtube_url: YouTube video URL
            target_language: Target language for voiceover
            voice_text: Custom voiceover text
            duration: Target duration (15-60 seconds)
            add_text_overlay: Add text overlay
        
        Returns:
            dict with success status and file path
        """
        print(f"🎬 Creating Instagram Reel")
        print(f"  📹 Source: {youtube_url}")
        print(f"  🌍 Language: {target_language}")
        print(f"  ⏱️ Duration: {duration} seconds")
        
        # Step 1: Download video using yt-dlp
        raw_video_path = self._download_youtube_video(youtube_url)
        if not raw_video_path:
            return {"success": False, "error": "Download failed"}
        
        # Step 2: Process video (trim, crop, optimize)
        processed_video_path = self._process_video(raw_video_path, duration)
        if not processed_video_path:
            return {"success": False, "error": "Processing failed"}
        
        # Step 3: Add TTS audio
        if voice_text:
            video_with_audio = self._add_tts_audio(processed_video_path, voice_text, target_language)
        else:
            video_with_audio = processed_video_path
        
        # Step 4: Add text overlay
        if add_text_overlay and voice_text:
            final_video = self._add_text_overlay(video_with_audio, voice_text)
        else:
            final_video = video_with_audio
        
        # Step 5: Final optimization for Instagram
        instagram_video = self._optimize_for_instagram(final_video)
        
        return {
            "success": True,
            "path": str(instagram_video),
            "duration": duration,
            "language": target_language
        }
    
    def _download_youtube_video(self, url: str) -> Path:
        """Download YouTube video using yt-dlp."""
        print("📥 Downloading YouTube video...")
        
        output_path = RAW_DIR / f"download_{self.timestamp}.mp4"
        
        cmd = [
            "yt-dlp",
            "-f", "best[height<=720]",
            "--merge-output-format", "mp4",
            "-o", str(output_path),
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and output_path.exists():
            print(f"✅ Downloaded: {output_path}")
            return output_path
        else:
            print(f"❌ Download failed: {result.stderr[:200]}")
            return Path("")
    
    def _process_video(self, video_path: Path, duration: int) -> Path:
        """Process video: trim, crop, optimize."""
        print("🔧 Processing video...")
        
        output_path = RAW_DIR / f"processed_{self.timestamp}.mp4"
        
        # Get video info
        cmd_info = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(video_path)]
        result_info = subprocess.run(cmd_info, capture_output=True, text=True)
        
        if result_info.returncode != 0:
            print("❌ Could not get video info")
            return video_path
        
        info = json.loads(result_info.stdout)
        current_duration = float(info.get("format", {}).get("duration", 0))
        
        # Trim to target duration
        if current_duration > duration:
            # Take middle portion
            start_time = (current_duration - duration) / 2
            cmd_trim = [
                "ffmpeg", "-y",
                "-ss", str(start_time),
                "-i", str(video_path),
                "-t", str(duration),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-vf", "scale=1080:1920",
                "-c:a", "aac",
                str(output_path)
            ]
        else:
            # Keep as is
            cmd_trim = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-vf", "scale=1080:1920",
                "-c:a", "aac",
                str(output_path)
            ]
        
        result = subprocess.run(cmd_trim, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Video processed: {output_path}")
            return output_path
        else:
            print(f"❌ Processing failed: {result.stderr[:200]}")
            return video_path
    
    def _add_tts_audio(self, video_path: Path, text: str, language: str) -> Path:
        """Add TTS audio to video."""
        print(f"🔊 Adding {language} audio...")
        
        # Import TTS engine
        import sys
        sys.path.insert(0, str(BASE_DIR))
        from tools.tts_engine import text_to_speech
        
        # Generate audio
        audio_path = RAW_DIR / f"audio_{self.timestamp}.mp3"
        success = text_to_speech(text, str(audio_path), language=language, use_edge_tts=True)
        
        if not success:
            print("❌ Audio generation failed")
            return video_path
        
        # Merge video and audio
        output_path = PROCESSED_DIR / f"video_audio_{self.timestamp}.mp4"
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Audio added: {output_path}")
            return output_path
        else:
            print(f"❌ Audio merge failed: {result.stderr[:200]}")
            return video_path
    
    def _add_text_overlay(self, video_path: Path, text: str) -> Path:
        """Add text overlay to video using Pillow."""
        print("📝 Adding text overlay...")
        
        # Create text overlay image
        overlay_path = RAW_DIR / f"overlay_{self.timestamp}.png"
        
        # Create image with text
        img = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Try to load font
        try:
            font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 80)
        except:
            font = ImageFont.load_default()
        
        # Add text with background
        # Text box
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Position text at bottom
        x = (1080 - text_width) // 2
        y = 1920 - text_height - 200
        
        # Draw background rectangle
        padding = 20
        draw.rectangle(
            [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
            fill=(0, 0, 0, 180)
        )
        
        # Draw text
        draw.text((x, y), text, fill='white', font=font)
        
        # Save overlay
        img.save(overlay_path)
        
        # Apply overlay to video
        output_path = PROCESSED_DIR / f"video_overlay_{self.timestamp}.mp4"
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(overlay_path),
            "-filter_complex", "[0:v][1:v]overlay=0:0:shortest=1",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Text overlay added: {output_path}")
            return output_path
        else:
            print(f"❌ Overlay failed: {result.stderr[:200]}")
            return video_path
    
    def _optimize_for_instagram(self, video_path: Path) -> Path:
        """Optimize video for Instagram."""
        print("📱 Optimizing for Instagram...")
        
        output_path = PROCESSED_DIR / f"instagram_reel_{self.timestamp}.mp4"
        
        # Instagram requirements:
        # - Duration: 15-60 seconds
        # - Resolution: 1080x1920 (9:16)
        # - Format: MP4
        # - Codec: H.264
        # - Audio: AAC
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1080:1920",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-t", "60",  # Max 60 seconds
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Instagram optimized: {output_path}")
            return output_path
        else:
            print(f"❌ Optimization failed: {result.stderr[:200]}")
            return video_path


# Example usage
if __name__ == "__main__":
    creator = InstagramReelCreator()
    
    # Test with a health/fitness video
    result = creator.create_reel_from_youtube(
        youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        target_language="hi",
        voice_text="Zyada energy chahiye? Yeh 5 subah ki exercises aapke din ko behtar bana degi!",
        duration=15,
        add_text_overlay=True
    )
    
    print(f"\n📊 RESULT: {result}")
    
    if result["success"]:
        # Open video
        subprocess.run(["open", result["path"]])
        print(f"\n🎬 Video playing!")
