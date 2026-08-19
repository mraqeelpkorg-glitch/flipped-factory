"""
Video Capture Pipeline - Refined Version
Captures clean video frames from YouTube using headless browser
"""
import asyncio
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

# Directories
BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "data" / "videos" / "raw"
FRAMES_DIR = RAW_DIR / "frames"
PROCESSED_DIR = BASE_DIR / "data" / "videos" / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
FRAMES_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


class VideoCapture:
    """Capture and process videos from YouTube."""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime('%H%M%S')
    
    async def capture_youtube_video(
        self, 
        url: str, 
        duration: int = 15,
        language: str = 'hi',
        voice_text: str = "",
        output_name: str = ""
    ) -> dict:
        """
        Capture video from YouTube and process for Instagram.
        
        Args:
            url: YouTube video URL
            duration: Duration to capture (seconds)
            language: Target language for TTS
            voice_text: Custom voice text (optional)
            output_name: Custom output name (optional)
        
        Returns:
            dict with success status and file path
        """
        if not output_name:
            output_name = f"reel_{self.timestamp}"
        
        print(f"🎬 Starting video capture: {url}")
        print(f"⏱️ Duration: {duration} seconds")
        print(f"🌍 Language: {language}")
        
        # Step 1: Capture video frames
        frames_path = await self._capture_frames(url, duration)
        if not frames_path:
            return {"success": False, "error": "Frame capture failed"}
        
        # Step 2: Create video from frames
        video_path = self._create_video_from_frames(frames_path, duration)
        if not video_path:
            return {"success": False, "error": "Video creation failed"}
        
        # Step 3: Add TTS audio
        if voice_text:
            final_path = self._add_tts_audio(video_path, voice_text, language)
        else:
            final_path = video_path
        
        # Step 4: Optimize for Instagram
        instagram_path = self._optimize_for_instagram(final_path)
        
        return {
            "success": True,
            "path": str(instagram_path),
            "frames": duration * 30,
            "duration": duration,
            "language": language
        }
    
    async def _capture_frames(self, url: str, duration: int) -> Path:
        """Capture video frames using headless browser."""
        print(f"📱 Opening YouTube in headless browser...")
        
        async with async_playwright() as p:
            # Launch browser with video recording
            browser = await p.chromium.launch(
                headless=True,
                args=['--autoplay-policy=no-user-gesture-required']
            )
            
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                record_video_dir=str(RAW_DIR / "recordings"),
                record_video_size={"width": 1920, "height": 1080}
            )
            
            page = await context.new_page()
            
            try:
                # Navigate to YouTube
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2)
                
                # Click play button
                print("▶️ Starting video playback...")
                try:
                    play_button = page.locator('button.ytp-large-play-button')
                    if await play_button.is_visible():
                        await play_button.click()
                        await asyncio.sleep(1)
                except:
                    pass
                
                # Wait for video to load
                await asyncio.sleep(3)
                
                # Capture frames for specified duration
                print(f"📷 Capturing {duration * 30} frames...")
                frames_captured = 0
                
                # Clean frames directory
                for f in FRAMES_DIR.glob("frame_*.png"):
                    f.unlink()
                
                for i in range(duration * 30):
                    # Take screenshot
                    frame_path = FRAMES_DIR / f"frame_{frames_captured:04d}.png"
                    
                    # Try to capture just the video element
                    try:
                        video_element = page.locator('video')
                        if await video_element.is_visible():
                            await video_element.screenshot(path=str(frame_path))
                        else:
                            await page.screenshot(path=str(frame_path), type="png")
                    except:
                        await page.screenshot(path=str(frame_path), type="png")
                    
                    frames_captured += 1
                    
                    if frames_captured % 30 == 0:
                        print(f"  📷 Captured {frames_captured} frames...")
                    
                    await asyncio.sleep(1/30)  # 30 FPS
                
                print(f"✅ Captured {frames_captured} frames")
                return FRAMES_DIR
                
            except Exception as e:
                print(f"❌ Frame capture error: {e}")
                return Path("")
            
            finally:
                await browser.close()
    
    def _create_video_from_frames(self, frames_path: Path, duration: int) -> Path:
        """Create video from captured frames using FFmpeg."""
        print("🎬 Creating video from frames...")
        
        output_path = RAW_DIR / f"raw_video_{self.timestamp}.mp4"
        
        cmd = [
            "ffmpeg", "-y",
            "-framerate", "30",
            "-i", str(frames_path / "frame_%04d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1080:1920",
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Video created: {output_path}")
            return output_path
        else:
            print(f"❌ FFmpeg error: {result.stderr[:200]}")
            return Path("")
    
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
        output_path = PROCESSED_DIR / f"video_with_audio_{self.timestamp}.mp4"
        
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
    
    def _optimize_for_instagram(self, video_path: Path) -> Path:
        """Optimize video for Instagram (15-60 seconds, 1080x1920, etc.)."""
        print("📱 Optimizing for Instagram...")
        
        output_path = PROCESSED_DIR / f"instagram_ready_{self.timestamp}.mp4"
        
        # Get video duration
        cmd_info = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(video_path)]
        result_info = subprocess.run(cmd_info, capture_output=True, text=True)
        
        if result_info.returncode != 0:
            print("❌ Could not get video info")
            return video_path
        
        info = json.loads(result_info.stdout)
        duration = float(info.get("format", {}).get("duration", 0))
        
        # Trim to 15-60 seconds for Instagram Reels
        if duration > 60:
            # Take first 60 seconds
            cmd_trim = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-t", "60",
                "-c:v", "copy",
                "-c:a", "copy",
                str(output_path)
            ]
        elif duration < 15:
            # Pad to 15 seconds (repeat video)
            cmd_trim = [
                "ffmpeg", "-y",
                "-stream_loop", "-1",
                "-i", str(video_path),
                "-t", "15",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-vf", "scale=1080:1920",
                str(output_path)
            ]
        else:
            # Keep as is
            cmd_trim = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-c:v", "copy",
                "-c:a", "copy",
                str(output_path)
            ]
        
        result = subprocess.run(cmd_trim, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Instagram optimized: {output_path}")
            return output_path
        else:
            print(f"❌ Optimization failed: {result.stderr[:200]}")
            return video_path


# Example usage
if __name__ == "__main__":
    capture = VideoCapture()
    result = asyncio.run(capture.capture_youtube_video(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        duration=10,
        language="hi",
        voice_text="Zyada energy chahiye? Yeh 5 subah ki exercises aapke din ko behtar bana degi!"
    ))
    print(f"\n📊 Result: {result}")
