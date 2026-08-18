"""
Downloader — Download videos/audio from YouTube and other platforms.
FREE: yt-dlp
"""
import logging
import subprocess
import json
from pathlib import Path

logger = logging.getLogger("downloader")

RAW_DIR = Path(__file__).parent.parent / "data" / "videos" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def download_video(url: str, output_dir: str = None, max_duration: int = 300) -> dict:
    """
    Download video from YouTube/TikTok/etc using yt-dlp.
    Returns {success, path, title, duration, format}
    """
    if output_dir is None:
        output_dir = str(RAW_DIR)
    
    output_template = f"{output_dir}/%(id)s.%(ext)s"
    
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--max-filesize", "100M",
        "-f", "best[height<=1080]",
        "--output", output_template,
        "--write-info-json",
        "--no-overwrites",
        url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            # Find downloaded file
            info_file = None
            for f in Path(output_dir).glob("*.info.json"):
                if f.stat().st_mtime > __import__("time").time() - 60:
                    info_file = f
                    break
            
            title = "Unknown"
            video_id = "unknown"
            if info_file:
                info = json.loads(info_file.read_text())
                title = info.get("title", "Unknown")
                video_id = info.get("id", "unknown")
            
            # Find video file
            video_file = None
            for ext in ["mp4", "webm", "mkv", "avi"]:
                candidate = Path(output_dir) / f"{video_id}.{ext}"
                if candidate.exists():
                    video_file = candidate
                    break
            
            if video_file:
                logger.info(f"Downloaded: {title}")
                return {
                    "success": True,
                    "path": str(video_file),
                    "title": title,
                    "video_id": video_id,
                }
        
        logger.warning(f"Download failed: {result.stderr[:200]}")
        return {"success": False, "error": result.stderr[:200]}
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Download timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def download_audio(url: str, output_dir: str = None) -> dict:
    """Download audio only from a video."""
    if output_dir is None:
        output_dir = str(RAW_DIR)
    
    output_template = f"{output_dir}/%(id)s.%(ext)s"
    
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "-f", "bestaudio",
        "--extract-audio",
        "--audio-format", "mp3",
        "--output", output_template,
        url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return {"success": True, "output": result.stdout}
        return {"success": False, "error": result.stderr[:200]}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_video_info(url: str) -> dict:
    """Get video metadata without downloading."""
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-download",
        url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            info = json.loads(result.stdout)
            return {
                "success": True,
                "title": info.get("title"),
                "duration": info.get("duration"),
                "uploader": info.get("uploader"),
                "description": info.get("description", "")[:500],
                "view_count": info.get("view_count"),
            }
    except Exception as e:
        pass
    
    return {"success": False, "error": "Could not fetch info"}


def list_downloaded() -> list[dict]:
    """List all downloaded videos."""
    videos = []
    for f in RAW_DIR.glob("*.mp4"):
        videos.append({
            "filename": f.name,
            "path": str(f),
            "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
        })
    return videos
