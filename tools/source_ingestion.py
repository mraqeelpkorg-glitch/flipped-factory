"""
Source Ingestion — Playwright-based headless browser source capture.

Ported from AgenticPlaywright's browser_automation_toolkit.py (848 lines).
Adapted for Flipped Factory video capture use case.

Capabilities:
- Open YouTube/social media videos in headless browser
- Capture video frames at 30fps
- Capture screenshots
- Extract video metadata
- Handle consent dialogs / cookie banners
- Stealth mode (anti-detection)
- Retry on failure
"""
import asyncio
import os
import subprocess
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger("source_ingestion")

BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "data" / "videos" / "raw"
FRAMES_DIR = RAW_DIR / "frames"
RECORDINGS_DIR = RAW_DIR / "recordings"
SOURCES_DIR = BASE_DIR / "outputs" / "sources"

for d in [RAW_DIR, FRAMES_DIR, RECORDINGS_DIR, SOURCES_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEALTH SCRIPT — removes navigator.webdriver flag (from BrowserPool)
# ══════════════════════════════════════════════════════════════════════════════

STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
window.chrome = { runtime: {} };
Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
"""

# ══════════════════════════════════════════════════════════════════════════════
# JS SNIPPETS — adapted from browser_automation_toolkit.py
# ══════════════════════════════════════════════════════════════════════════════

JS_DETECT_CAPTCHA = """
() => {
    const checks = [
        'iframe[src*="recaptcha"]', 'iframe[src*="hcaptcha"]',
        '.g-recaptcha', '.h-captcha', '#captcha',
        '[class*="captcha" i]', '[id*="captcha" i]'
    ];
    for (const sel of checks) {
        try { if (document.querySelector(sel)) return {found: true, type: sel}; } catch(e) {}
    }
    const body = document.body ? document.body.innerText.toLowerCase() : '';
    if (body.includes('captcha') || body.includes('robot') || body.includes('human verification')) {
        return {found: true, type: 'text-detected'};
    }
    return {found: false};
}
"""

JS_CLICK_PLAY = """
() => {
    // Try YouTube play button
    const btn = document.querySelector('button.ytp-large-play-button');
    if (btn) { btn.click(); return {ok: true, method: 'ytp-button'}; }
    // Try any video element
    const vid = document.querySelector('video');
    if (vid) { vid.play(); return {ok: true, method: 'video.play()'}; }
    return {ok: false};
}
"""

JS_GET_VIDEO_INFO = """
() => {
    const vid = document.querySelector('video');
    if (!vid) return {found: false};
    return {
        found: true,
        duration: vid.duration,
        currentTime: vid.currentTime,
        paused: vid.paused,
        videoWidth: vid.videoWidth,
        videoHeight: vid.videoHeight,
        src: vid.src ? vid.src.substring(0, 200) : '',
        title: document.title || '',
        url: window.location.href
    };
}
"""

JS_DISMISS_COOKIES = """
() => {
    // YouTube consent
    const acceptBtns = document.querySelectorAll(
        'button[aria-label*="Accept"], button[aria-label*="agree"], ' +
        'button[aria-label*="Agree"], tp-yt-paper-button#button.style-primary'
    );
    for (const btn of acceptBtns) {
        if (btn.offsetParent !== null) { btn.click(); return {ok: true}; }
    }
    return {ok: false};
}
"""


class SourceIngestion:
    """
    Playwright-based source ingestion for Flipped Factory.
    
    Handles:
    - YouTube video capture (frames + metadata)
    - Social media content extraction
    - Screenshot capture
    - Video stream recording
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.timestamp = datetime.now().strftime('%H%M%S')
    
    async def ingest_youtube(
        self,
        url: str,
        capture_duration: int = 30,
        capture_frames: bool = True,
    ) -> dict:
        """
        Ingest a YouTube video using headless Playwright.
        
        Returns:
            {
                "success": bool,
                "video_path": str,        # Downloaded/captured video
                "frames_dir": str,        # Directory of captured frames
                "metadata": dict,         # Title, duration, resolution, etc.
                "source_hash": str,       # Content hash for dedup
                "thumbnail_path": str,    # Screenshot thumbnail
            }
        """
        from playwright.async_api import async_playwright
        
        logger.info(f"Ingesting YouTube: {url}")
        job_id = f"ingest_{self.timestamp}"
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
                    '--disable-dev-shm-usage',
                    '--autoplay-policy=no-user-gesture-required',
                ],
            )
            
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="en-US",
                timezone_id="America/New_York",
            )
            
            # Inject stealth
            await context.add_init_script(STEALTH_SCRIPT)
            
            page = await context.new_page()
            
            try:
                # Navigate
                logger.info("Opening YouTube page...")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)
                
                # Dismiss cookie consent
                await page.evaluate(JS_DISMISS_COOKIES)
                await asyncio.sleep(1)
                
                # Check for CAPTCHA
                captcha = await page.evaluate(JS_DETECT_CAPTCHA)
                if captcha.get("found"):
                    logger.warning(f"CAPTCHA detected: {captcha.get('type')}")
                    return {
                        "success": False,
                        "error": f"CAPTCHA detected: {captcha.get('type')}",
                        "requires_human": True,
                    }
                
                # Get video info
                video_info = await page.evaluate(JS_GET_VIDEO_INFO)
                logger.info(f"Video info: {json.dumps(video_info, indent=2)}")
                
                # Click play
                play_result = await page.evaluate(JS_CLICK_PLAY)
                logger.info(f"Play result: {play_result}")
                await asyncio.sleep(3)
                
                # Re-check video info after play
                video_info = await page.evaluate(JS_GET_VIDEO_INFO)
                
                # Capture thumbnail
                thumbnail_path = str(SOURCES_DIR / f"thumb_{job_id}.png")
                await page.screenshot(path=thumbnail_path, type="png")
                logger.info(f"Thumbnail saved: {thumbnail_path}")
                
                # Capture frames
                frames_captured = 0
                frames_path = ""
                
                if capture_frames:
                    frames_path = str(FRAMES_DIR / job_id)
                    os.makedirs(frames_path, exist_ok=True)
                    
                    logger.info(f"Capturing {capture_duration * 30} frames...")
                    
                    for i in range(capture_duration * 30):
                        frame_file = os.path.join(frames_path, f"frame_{i:04d}.png")
                        
                        # Try to capture video element directly
                        try:
                            video_el = page.locator('video')
                            if await video_el.is_visible():
                                await video_el.screenshot(path=frame_file)
                            else:
                                await page.screenshot(path=frame_file, type="png")
                        except:
                            await page.screenshot(path=frame_file, type="png")
                        
                        frames_captured += 1
                        if frames_captured % 150 == 0:
                            logger.info(f"  Captured {frames_captured} frames...")
                        
                        await asyncio.sleep(1/30)  # 30 FPS
                    
                    logger.info(f"Captured {frames_captured} frames")
                
                # Create video from frames using FFmpeg
                video_path = str(RAW_DIR / f"captured_{job_id}.mp4")
                
                if frames_path and frames_captured > 0:
                    cmd = [
                        "ffmpeg", "-y",
                        "-framerate", "30",
                        "-i", os.path.join(frames_path, "frame_%04d.png"),
                        "-c:v", "libx264",
                        "-pix_fmt", "yuv420p",
                        "-vf", "scale=1080:1920",
                        video_path,
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        logger.error(f"FFmpeg error: {result.stderr[:200]}")
                        video_path = ""
                    else:
                        # Try to extract audio from YouTube (audio-only download often works)
                        audio_path = str(RAW_DIR / f"audio_{job_id}.m4a")
                        try:
                            cmd_audio = [
                                "yt-dlp",
                                "-x", "--audio-format", "m4a",
                                "--no-playlist",
                                "-o", audio_path,
                                url,
                            ]
                            r_audio = subprocess.run(cmd_audio, capture_output=True, text=True, timeout=30)
                            if r_audio.returncode == 0 and os.path.exists(audio_path):
                                # Mux audio into the captured video
                                video_with_audio = str(RAW_DIR / f"captured_{job_id}_audio.mp4")
                                cmd_mux = [
                                    "ffmpeg", "-y",
                                    "-i", video_path,
                                    "-i", audio_path,
                                    "-c:v", "copy", "-c:a", "aac",
                                    "-shortest",
                                    "-movflags", "+faststart",
                                    video_with_audio,
                                ]
                                r_mux = subprocess.run(cmd_mux, capture_output=True, text=True, timeout=60)
                                if r_mux.returncode == 0 and os.path.exists(video_with_audio):
                                    os.replace(video_with_audio, video_path)
                                    logger.info(f"Audio extracted and muxed: {audio_path}")
                                else:
                                    logger.warning(f"Audio mux failed: {r_mux.stderr[:100]}")
                                # Cleanup audio file
                                if os.path.exists(audio_path):
                                    os.remove(audio_path)
                            else:
                                logger.warning("Audio extraction failed (yt-dlp), proceeding without audio")
                        except Exception as e:
                            logger.warning(f"Audio extraction error: {e}")
                else:
                    video_path = ""
                
                # Calculate source hash
                source_hash = ""
                if video_path and os.path.exists(video_path):
                    with open(video_path, "rb") as f:
                        source_hash = hashlib.md5(f.read()).hexdigest()
                
                # Save metadata
                metadata = {
                    "url": url,
                    "title": video_info.get("title", ""),
                    "duration": video_info.get("duration", 0),
                    "video_width": video_info.get("videoWidth", 0),
                    "video_height": video_info.get("videoHeight", 0),
                    "capture_duration": capture_duration,
                    "frames_captured": frames_captured,
                    "captured_at": datetime.now().isoformat(),
                    "source_hash": source_hash,
                }
                
                metadata_path = str(SOURCES_DIR / f"meta_{job_id}.json")
                with open(metadata_path, "w") as f:
                    json.dump(metadata, f, indent=2)
                
                return {
                    "success": True,
                    "video_path": video_path,
                    "frames_dir": frames_path,
                    "frames_count": frames_captured,
                    "metadata": metadata,
                    "metadata_path": metadata_path,
                    "source_hash": source_hash,
                    "thumbnail_path": thumbnail_path,
                    "job_id": job_id,
                }
            
            except Exception as e:
                logger.error(f"Ingestion error: {e}")
                return {"success": False, "error": str(e)}
            
            finally:
                await browser.close()
    
    async def ingest_url(self, url: str) -> dict:
        """
        Generic URL ingestion — detects platform and routes.
        """
        url_lower = url.lower()
        
        if "youtube.com" in url_lower or "youtu.be" in url_lower:
            return await self.ingest_youtube(url)
        elif "tiktok.com" in url_lower:
            return await self.ingest_youtube(url)  # Same approach
        elif "instagram.com" in url_lower:
            return await self.ingest_youtube(url)  # Same approach
        elif "twitter.com" in url_lower or "x.com" in url_lower:
            return await self.ingest_youtube(url)  # Same approach
        else:
            # Generic: try to capture whatever is on the page
            return await self.ingest_youtube(url)
    
    def ingest_local_video(self, video_path: str) -> dict:
        """
        Ingest a local video file.
        """
        if not os.path.exists(video_path):
            return {"success": False, "error": f"File not found: {video_path}"}
        
        # Get video info via ffprobe
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            video_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        metadata = {}
        if result.returncode == 0:
            metadata = json.loads(result.stdout)
        
        # Calculate hash
        with open(video_path, "rb") as f:
            source_hash = hashlib.md5(f.read()).hexdigest()
        
        # Copy to raw directory
        job_id = f"local_{self.timestamp}"
        dest_path = str(RAW_DIR / f"{job_id}_{Path(video_path).name}")
        
        import shutil
        shutil.copy2(video_path, dest_path)
        
        return {
            "success": True,
            "video_path": dest_path,
            "frames_dir": "",
            "frames_count": 0,
            "metadata": {
                "source": "local",
                "original_path": video_path,
                "probe_data": metadata,
                "source_hash": source_hash,
                "ingested_at": datetime.now().isoformat(),
            },
            "source_hash": source_hash,
            "thumbnail_path": "",
            "job_id": job_id,
        }


# ══════════════════════════════════════════════════════════════════════════════
# SYNC WRAPPER — for use in non-async contexts (agent_runner, etc.)
# ══════════════════════════════════════════════════════════════════════════════

def ingest_source(url_or_path: str, capture_duration: int = 30) -> dict:
    """
    Sync wrapper for source ingestion.
    Use from agent_runner and other non-async code.
    """
    ingestion = SourceIngestion(headless=True)
    
    if os.path.exists(url_or_path):
        return ingestion.ingest_local_video(url_or_path)
    else:
        # Run async in new event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're inside an async context, create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        ingestion.ingest_url(url_or_path)
                    )
                    return future.result(timeout=120)
            else:
                return loop.run_until_complete(ingestion.ingest_url(url_or_path))
        except RuntimeError:
            return asyncio.run(ingestion.ingest_url(url_or_path))


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python source_ingestion.py <youtube_url>")
        sys.exit(1)
    
    result = asyncio.run(SourceIngestion().ingest_youtube(sys.argv[1], capture_duration=5))
    print(json.dumps(result, indent=2))
