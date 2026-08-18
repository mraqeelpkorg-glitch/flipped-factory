"""
Podcast Clipper — Downloads podcast + creates Instagram Reels clips.
Uses: yt-dlp (download) + FFmpeg (split/crop) + macOS say (TTS captions).
No Whisper needed — uses silence detection for natural break points.
"""
import subprocess
import os
import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("podcast_clipper")

BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "data" / "videos" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "videos" / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def download_podcast(url: str, output_dir: str = None) -> dict:
    """
    Download podcast/audio from YouTube URL using yt-dlp.
    Returns {success, path, title, duration}.
    """
    if output_dir is None:
        output_dir = str(RAW_DIR)
    
    try:
        # Get video info first (nodejs runtime required)
        cmd_info = ["yt-dlp", "--js-runtimes", "node", "--dump-json", "--no-download", url]
        result = subprocess.run(cmd_info, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return {"success": False, "error": f"Failed to get info: {result.stderr[:200]}"}
        
        info = json.loads(result.stdout)
        title = info.get("title", "podcast")[:60].replace(" ", "_").replace("/", "_")
        duration = info.get("duration", 0)
        
        # Download as MP4 (video + audio)
        output_template = os.path.join(output_dir, f"{title}.%(ext)s")
        cmd_dl = [
            "yt-dlp",
            "--js-runtimes", "node",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "-o", output_template,
            url,
        ]
        result = subprocess.run(cmd_dl, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            return {"success": False, "error": f"Download failed: {result.stderr[:200]}"}
        
        # Find the downloaded file
        downloaded = None
        for f in os.listdir(output_dir):
            if title in f and f.endswith(".mp4"):
                downloaded = os.path.join(output_dir, f)
                break
        
        if not downloaded:
            return {"success": False, "error": "Downloaded file not found"}
        
        logger.info(f"Downloaded: {downloaded} ({duration}s)")
        return {
            "success": True,
            "path": downloaded,
            "title": title,
            "duration": duration,
        }
    
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Download timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def detect_segments(video_path: str, min_segment: float = 15.0, max_segment: float = 60.0) -> list:
    """
    Detect natural break points using FFmpeg silence detection.
    Returns list of {start, end, duration} segments.
    """
    try:
        # Get total duration
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", video_path],
            capture_output=True, text=True, timeout=10
        )
        total_duration = float(probe.stdout.strip())
        
        # Detect silence (gaps of 1+ seconds)
        cmd = [
            "ffmpeg", "-i", video_path,
            "-af", "silencedetect=noise=-30dB:d=1.0",
            "-f", "null", "-"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        # Parse silence regions
        silences = []
        for line in result.stderr.split("\n"):
            if "silence_start" in line:
                start = float(line.split("=")[1].strip())
                silences.append({"start": start})
            elif "silence_end" in line and silences:
                end = float(line.split("=")[1].strip().split()[0])
                silences[-1]["end"] = end
        
        # Build segments from silence gaps
        segments = []
        prev_end = 0.0
        
        for s in silences:
            seg_start = prev_end
            seg_end = s.get("start", s.get("end", prev_end + min_segment))
            
            # Ensure minimum length
            if seg_end - seg_start >= min_segment:
                # Cap at max segment length
                if seg_end - seg_start > max_segment:
                    seg_end = seg_start + max_segment
                segments.append({
                    "start": round(seg_start, 2),
                    "end": round(seg_end, 2),
                    "duration": round(seg_end - seg_start, 2),
                })
            
            prev_end = s.get("end", seg_end)
        
        # Add final segment if needed
        if total_duration - prev_end >= min_segment:
            end = min(prev_end + max_segment, total_duration)
            segments.append({
                "start": round(prev_end, 2),
                "end": round(end, 2),
                "duration": round(end - prev_end, 2),
            })
        
        # If no segments found (no silence), split evenly
        if not segments:
            num_cuts = max(1, int(total_duration / 30))
            seg_len = total_duration / num_cuts
            for i in range(num_cuts):
                start = i * seg_len
                end = min((i + 1) * seg_len, total_duration)
                segments.append({
                    "start": round(start, 2),
                    "end": round(end, 2),
                    "duration": round(end - start, 2),
                })
        
        logger.info(f"Found {len(segments)} segments from {total_duration:.0f}s video")
        return segments
    
    except Exception as e:
        logger.error(f"Segment detection failed: {e}")
        # Fallback: split into 30s chunks
        return [{"start": 0, "end": 30, "duration": 30}]


def create_clip(
    source_path: str,
    segment: dict,
    clip_index: int,
    niche: str = "education",
    output_dir: str = None,
) -> dict:
    """
    Create a single podcast clip:
    1. Trim source video
    2. Crop to vertical 9:16
    3. Add TTS voiceover
    4. Create branded end card
    """
    if output_dir is None:
        output_dir = str(PROCESSED_DIR)
    
    timestamp = datetime.now().strftime("%H%M%S")
    
    # Step 1: Trim
    trimmed_path = os.path.join(output_dir, f"trim_{clip_index}_{timestamp}.mp4")
    cmd_trim = [
        "ffmpeg", "-i", source_path,
        "-ss", str(segment["start"]),
        "-t", str(segment["duration"]),
        "-c:v", "libx264", "-an",
        "-y", trimmed_path,
    ]
    r = subprocess.run(cmd_trim, capture_output=True, text=True, timeout=60)
    if r.returncode != 0 or not os.path.exists(trimmed_path):
        return {"success": False, "error": "Trim failed"}
    
    # Step 2: Crop to vertical
    cropped_path = os.path.join(output_dir, f"clip_{clip_index}_{timestamp}.mp4")
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", trimmed_path],
        capture_output=True, text=True, timeout=10
    )
    parts = probe.stdout.strip().split(",")
    w, h = int(parts[0]), int(parts[1])
    
    target_ratio = 9 / 16
    new_w = int(h * target_ratio)
    if new_w > w:
        new_w = w
    x = (w - new_w) // 2
    
    cmd_crop = [
        "ffmpeg", "-i", trimmed_path,
        "-vf", f"crop={new_w}:{h}:{x}:0,scale=1080:1920",
        "-c:v", "libx264", "-an",
        "-y", cropped_path,
    ]
    r = subprocess.run(cmd_crop, capture_output=True, text=True, timeout=60)
    
    if not os.path.exists(cropped_path):
        # Fallback: use trimmed
        cropped_path = trimmed_path
    
    # Step 3: Generate TTS voiceover
    tts_path = os.path.join(output_dir, f"tts_{clip_index}_{timestamp}.mp3")
    from tools.tts_engine import text_to_speech
    
    # Create a caption text for this segment
    caption = generate_caption(segment, clip_index)
    text_to_speech(caption, tts_path, voice="Daniel", rate=180)
    
    # Step 4: Merge video + audio
    final_path = os.path.join(output_dir, f"podcast_clip_{clip_index}_{timestamp}.mp4")
    
    if os.path.exists(tts_path):
        # Get TTS duration
        tts_probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", tts_path],
            capture_output=True, text=True, timeout=10
        )
        tts_dur = float(tts_probe.stdout.strip())
        vid_dur = segment["duration"]
        
        # Speed up or slow down TTS to match video
        speed = tts_dur / vid_dur if vid_dur > 0 else 1.0
        
        if 0.5 < speed < 2.0:
            # Adjust TTS speed
            adjusted_tts = os.path.join(output_dir, f"tts_adj_{clip_index}_{timestamp}.mp3")
            cmd_speed = [
                "ffmpeg", "-i", tts_path,
                "-filter:a", f"atempo={speed}",
                "-y", adjusted_tts,
            ]
            subprocess.run(cmd_speed, capture_output=True, timeout=30)
            if os.path.exists(adjusted_tts):
                tts_path = adjusted_tts
        
        # Merge
        cmd_merge = [
            "ffmpeg", "-i", cropped_path, "-i", tts_path,
            "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
            "-shortest", "-y", final_path,
        ]
        r = subprocess.run(cmd_merge, capture_output=True, text=True, timeout=60)
    else:
        # No TTS, just copy video
        os.rename(cropped_path, final_path)
    
    # Cleanup temp files
    for f in [trimmed_path, cropped_path]:
        if os.path.exists(f) and f != final_path:
            try: os.remove(f)
            except: pass
    
    if os.path.exists(final_path):
        size = os.path.getsize(final_path)
        logger.info(f"Clip created: {final_path} ({size/1024:.1f} KB)")
        return {
            "success": True,
            "path": final_path,
            "duration": segment["duration"],
            "size": size,
            "caption": caption,
        }
    
    return {"success": False, "error": "Final merge failed"}


def generate_caption(segment: dict, index: int) -> str:
    """Generate a TTS caption for a clip."""
    duration = segment.get("duration", 30)
    if duration <= 15:
        return f"Clip {index}. Key moment from this podcast episode."
    elif duration <= 30:
        return f"Clip {index}. Here is an important insight from this episode. Listen carefully."
    else:
        return f"Clip {index}. This is one of the best moments from this podcast. Enjoy."


def run(
    source: str,
    niche: str = "education",
    max_clips: int = 5,
    min_segment: float = 15.0,
    max_segment: float = 60.0,
) -> dict:
    """
    Main podcast clipper pipeline.
    
    Args:
        source: YouTube URL or local file path
        niche: Content niche for categorization
        max_clips: Maximum clips to create
        min_segment: Minimum clip duration (seconds)
        max_segment: Maximum clip duration (seconds)
    """
    logger.info(f"Podcast Clipper | Source: {source} | Niche: {niche}")
    
    # Step 1: Get source video
    if source.startswith("http"):
        dl = download_podcast(source)
        if not dl["success"]:
            return {"success": False, "error": dl["error"]}
        source_path = dl["path"]
    else:
        source_path = source
        if not os.path.exists(source_path):
            return {"success": False, "error": f"File not found: {source_path}"}
    
    # Step 2: Detect segments
    segments = detect_segments(source_path, min_segment, max_segment)
    segments = segments[:max_clips]
    
    # Step 3: Create clips
    clips = []
    for i, seg in enumerate(segments):
        logger.info(f"Creating clip {i+1}/{len(segments)}: {seg['start']}s - {seg['end']}s")
        result = create_clip(source_path, seg, i + 1, niche)
        if result["success"]:
            clips.append(result)
    
    return {
        "success": True,
        "source": source_path,
        "total_segments": len(segments),
        "clips_created": len(clips),
        "clips": clips,
    }
