"""
Podcast Clipper — Full pipeline for podcast → Instagram Reels.

Flow:
1. PODCAST SELECTION: Auto-search YouTube by niche OR use provided URL
2. DOWNLOAD: yt-dlp with node runtime
3. SEGMENT: FFmpeg silence detection → natural break points
4. CLIP: Trim + crop to vertical 9:16
5. VOICEOVER: macOS say (natural TTS)
6. MERGE: Video + audio → final Reel

No Ollama, no Whisper — all free local tools.
"""
import subprocess
import os
import json
import random
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("podcast_clipper")

BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "data" / "videos" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "videos" / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ─── Podcast Search Queries by Niche ──────────────────────────────────────────
PODCAST_SEARCHES = {
    "health_fitness": [
        "fitness podcast short clip",
        "health tips podcast highlights",
        "workout motivation podcast",
        "nutrition podcast episode",
        "weight loss podcast clip",
    ],
    "finance_crypto": [
        "crypto podcast highlights",
        "investing podcast clip",
        "money tips podcast short",
        "bitcoin podcast episode",
        "financial freedom podcast",
    ],
    "tech_ai": [
        "AI podcast highlights",
        "technology podcast clip",
        "artificial intelligence podcast",
        "coding podcast short",
        "tech trends podcast episode",
    ],
    "education": [
        "educational podcast highlights",
        "learning podcast clip",
        "science podcast short",
        "history podcast episode",
        "knowledge podcast highlights",
    ],
    "motivation": [
        "motivational podcast highlights",
        "success podcast clip",
        "mindset podcast short",
        "personal growth podcast",
        "inspiration podcast episode",
    ],
    "ecommerce": [
        "ecommerce podcast highlights",
        "dropshipping podcast clip",
        "online business podcast",
        "amazon FBA podcast short",
        "shopify podcast episode",
    ],
    "food_nutrition": [
        "cooking podcast highlights",
        "food podcast clip",
        "recipe podcast short",
        "nutrition podcast episode",
        "healthy eating podcast",
    ],
    "travel": [
        "travel podcast highlights",
        "adventure podcast clip",
        "travel tips podcast short",
        "digital nomad podcast",
        "explore podcast episode",
    ],
    "beauty_skincare": [
        "beauty podcast highlights",
        "skincare podcast clip",
        "makeup podcast short",
        "self care podcast episode",
        "glow up podcast",
    ],
    "productivity": [
        "productivity podcast highlights",
        "time management podcast clip",
        "business podcast short",
        "hustle podcast episode",
        "success habits podcast",
    ],
}


# ─── Step 1: Podcast Selection ────────────────────────────────────────────────
def search_podcasts(niche: str, max_results: int = 5) -> list:
    """
    Search YouTube for podcasts in a given niche.
    Returns list of {url, title, duration, channel}.
    """
    queries = PODCAST_SEARCHES.get(niche, PODCAST_SEARCHES["education"])
    query = random.choice(queries)
    
    try:
        cmd = [
            "yt-dlp",
            "--js-runtimes", "node",
            "--flat-playlist",
            "--dump-json",
            "--no-download",
            f"ytsearch{max_results}:{query}",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            logger.warning(f"Search failed: {result.stderr[:200]}")
            return []
        
        podcasts = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            try:
                info = json.loads(line)
                duration = info.get("duration", 0) or 0
                
                # Filter: 5 min to 2 hours (good podcast length)
                if 300 <= duration <= 7200:
                    podcasts.append({
                        "url": f"https://www.youtube.com/watch?v={info.get('id', '')}",
                        "title": info.get("title", "Unknown"),
                        "duration": duration,
                        "channel": info.get("channel", info.get("uploader", "Unknown")),
                        "view_count": info.get("view_count", 0) or 0,
                    })
            except json.JSONDecodeError:
                continue
        
        # Sort by views (most popular first)
        podcasts.sort(key=lambda p: p["view_count"], reverse=True)
        
        logger.info(f"Found {len(podcasts)} podcasts for niche: {niche}")
        return podcasts[:max_results]
    
    except Exception as e:
        logger.error(f"Podcast search failed: {e}")
        return []


def select_best_podcast(niche: str) -> dict:
    """
    Automatically select the best podcast for clipping.
    Strategy: search by niche → pick most viewed with good duration.
    """
    podcasts = search_podcasts(niche, max_results=5)
    
    if not podcasts:
        # Fallback: search general
        podcasts = search_podcasts("education", max_results=5)
    
    if not podcasts:
        return {"success": False, "error": "No podcasts found"}
    
    # Pick the most viewed one
    best = podcasts[0]
    
    logger.info(f"Selected: {best['title'][:60]} ({best['duration']}s, {best['channel']})")
    return {
        "success": True,
        "podcast": best,
        "alternatives": podcasts[1:],
    }


# ─── Step 2: Download ─────────────────────────────────────────────────────────
def download_podcast(url: str, output_dir: str = None) -> dict:
    """Download podcast from YouTube URL using yt-dlp with browser cookies."""
    if output_dir is None:
        output_dir = str(RAW_DIR)
    
    try:
        # Get info
        cmd_info = [
            "yt-dlp", "--js-runtimes", "node",
            "--cookies-from-browser", "chrome",
            "--dump-json", "--no-download", url,
        ]
        result = subprocess.run(cmd_info, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return {"success": False, "error": f"Info failed: {result.stderr[:200]}"}
        
        info = json.loads(result.stdout)
        title = info.get("title", "podcast")[:50]
        safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)
        duration = info.get("duration", 0)
        
        # Download with cookies (required for YouTube 403 bypass)
        output_template = os.path.join(output_dir, f"{safe_title}.%(ext)s")
        cmd_dl = [
            "yt-dlp",
            "--js-runtimes", "node",
            "--remote-components", "ejs:github",
            "--cookies-from-browser", "chrome",
            "--merge-output-format", "mp4",
            "-o", output_template,
            url,
        ]
        result = subprocess.run(cmd_dl, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            return {"success": False, "error": f"Download failed: {result.stderr[:300]}"}
        
        # Find downloaded file (may end in .mp4, .webm, .mkv)
        downloaded = None
        for f in os.listdir(output_dir):
            if safe_title in f and any(f.endswith(ext) for ext in [".mp4", ".webm", ".mkv"]):
                downloaded = os.path.join(output_dir, f)
                break
        
        if not downloaded:
            # Try any recent video file
            for ext in [".mp4", ".webm", ".mkv"]:
                vids = [f for f in os.listdir(output_dir) if f.endswith(ext) and "test" not in f]
                if vids:
                    downloaded = os.path.join(output_dir, sorted(vids)[-1])
                    break
        
        if downloaded:
            # If not .mp4, convert with FFmpeg
            if not downloaded.endswith(".mp4"):
                mp4_path = downloaded.rsplit(".", 1)[0] + ".mp4"
                cmd_conv = [
                    "ffmpeg", "-i", downloaded,
                    "-c:v", "libx264", "-c:a", "aac",
                    "-y", mp4_path,
                ]
                subprocess.run(cmd_conv, capture_output=True, text=True, timeout=120)
                if os.path.exists(mp4_path):
                    try: os.remove(downloaded)
                    except: pass
                    downloaded = mp4_path
            
            logger.info(f"Downloaded: {downloaded}")
            return {
                "success": True,
                "path": downloaded,
                "title": title,
                "duration": duration,
            }
        
        return {"success": False, "error": "Download failed — no file found"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── Step 3: Segment Detection ────────────────────────────────────────────────
def detect_segments(video_path: str, min_segment: float = 15.0, max_segment: float = 60.0) -> list:
    """Detect natural break points using FFmpeg silence detection."""
    try:
        # Get duration
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", video_path],
            capture_output=True, text=True, timeout=10
        )
        total_duration = float(probe.stdout.strip())
        
        # Detect silence
        cmd = [
            "ffmpeg", "-i", video_path,
            "-af", "silencedetect=noise=-30dB:d=1.0",
            "-f", "null", "-"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        # Parse silences (robust parsing)
        import re
        silences = []
        for line in result.stderr.split("\n"):
            try:
                if "silence_start" in line:
                    match = re.search(r'silence_start:\s*([\d.]+)', line)
                    if match:
                        start = float(match.group(1))
                        silences.append({"start": start})
                elif "silence_end" in line and silences:
                    match = re.search(r'silence_end:\s*([\d.]+)', line)
                    if match:
                        end = float(match.group(1))
                        silences[-1]["end"] = end
            except (ValueError, IndexError):
                continue
        
        # Build segments
        segments = []
        prev_end = 0.0
        
        for s in silences:
            seg_start = prev_end
            seg_end = s.get("start", prev_end + min_segment)
            
            if seg_end - seg_start >= min_segment:
                if seg_end - seg_start > max_segment:
                    seg_end = seg_start + max_segment
                segments.append({
                    "start": round(seg_start, 2),
                    "end": round(seg_end, 2),
                    "duration": round(seg_end - seg_start, 2),
                })
            
            prev_end = s.get("end", seg_end)
        
        # Final segment
        if total_duration - prev_end >= min_segment:
            end = min(prev_end + max_segment, total_duration)
            segments.append({
                "start": round(prev_end, 2),
                "end": round(end, 2),
                "duration": round(end - prev_end, 2),
            })
        
        # Fallback: split evenly
        if not segments:
            num = max(1, int(total_duration / 30))
            seg_len = total_duration / num
            for i in range(num):
                s = i * seg_len
                e = min((i + 1) * seg_len, total_duration)
                if e - s >= min_segment:
                    segments.append({
                        "start": round(s, 2),
                        "end": round(e, 2),
                        "duration": round(e - s, 2),
                    })
        
        logger.info(f"Found {len(segments)} segments from {total_duration:.0f}s")
        return segments
    
    except Exception as e:
        logger.error(f"Segment detection failed: {e}")
        return [{"start": 0, "end": 30, "duration": 30}]


# ─── Step 4: Create Clip ──────────────────────────────────────────────────────
def create_clip(
    source_path: str,
    segment: dict,
    clip_index: int,
    niche: str = "education",
    podcast_title: str = "",
    output_dir: str = None,
) -> dict:
    """Create a single podcast clip with TTS voiceover."""
    if output_dir is None:
        output_dir = str(PROCESSED_DIR)
    
    timestamp = datetime.now().strftime("%H%M%S")
    
    # Step A: Trim + crop to vertical in one pass
    cropped_path = os.path.join(output_dir, f"clip_{clip_index}_{timestamp}.mp4")
    cmd = [
        "ffmpeg", "-i", source_path,
        "-ss", str(segment["start"]),
        "-t", str(segment["duration"]),
        "-vf", "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920",
        "-c:v", "libx264", "-an",
        "-y", cropped_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0 or not os.path.exists(cropped_path):
        return {"success": False, "error": "Trim/crop failed"}
    
    # Step B: Generate TTS voiceover
    tts_path = os.path.join(output_dir, f"tts_{clip_index}_{timestamp}.mp3")
    from tools.tts_engine import text_to_speech
    
    caption = generate_caption(podcast_title, segment, clip_index)
    text_to_speech(caption, tts_path, voice="Daniel", rate=180)
    
    # Step C: Merge video + audio
    final_path = os.path.join(output_dir, f"podcast_clip_{clip_index}_{timestamp}.mp4")
    
    if os.path.exists(tts_path):
        # Check TTS duration vs video duration
        tts_probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", tts_path],
            capture_output=True, text=True, timeout=10
        )
        tts_dur = float(tts_probe.stdout.strip()) if tts_probe.stdout.strip() else 0
        vid_dur = segment["duration"]
        
        # Speed adjust if needed
        if tts_dur > 0 and vid_dur > 0:
            speed = tts_dur / vid_dur
            if 0.5 < speed < 2.0:
                adj_tts = os.path.join(output_dir, f"tts_adj_{clip_index}_{timestamp}.mp3")
                subprocess.run(
                    ["ffmpeg", "-i", tts_path, "-filter:a", f"atempo={speed}", "-y", adj_tts],
                    capture_output=True, timeout=30
                )
                if os.path.exists(adj_tts):
                    tts_path = adj_tts
        
        # Final merge
        cmd_merge = [
            "ffmpeg", "-i", cropped_path, "-i", tts_path,
            "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
            "-shortest", "-y", final_path,
        ]
        subprocess.run(cmd_merge, capture_output=True, text=True, timeout=60)
    
    # Cleanup
    for f in [cropped_path]:
        if os.path.exists(f) and f != final_path:
            try: os.remove(f)
            except: pass
    
    if os.path.exists(final_path):
        size = os.path.getsize(final_path)
        return {
            "success": True,
            "path": final_path,
            "duration": segment["duration"],
            "size": size,
            "caption": caption,
        }
    
    return {"success": False, "error": "Merge failed"}


def generate_caption(podcast_title: str, segment: dict, index: int) -> str:
    """Generate a natural TTS caption for a clip."""
    duration = segment.get("duration", 30)
    
    if podcast_title:
        short_title = podcast_title[:40]
        if duration <= 15:
            return f"From {short_title}. Key moment number {index}."
        elif duration <= 30:
            return f"From {short_title}. Important insight number {index}. Listen carefully."
        else:
            return f"From {short_title}. Best moment number {index}. Enjoy this clip."
    
    if duration <= 15:
        return f"Key moment number {index} from this podcast episode."
    elif duration <= 30:
        return f"Important insight number {index}. Here is what you need to know."
    else:
        return f"Best moment number {index} from this podcast. Enjoy."


# ─── Content Quality Check ─────────────────────────────────────────────────────
def check_content(video_path: str, title: str = "", channel: str = "",
                  original_duration: float = 0, clip_duration: float = 0) -> dict:
    """
    Run content quality and copyright check before publishing.
    Returns {passed, report, recommendation}.
    """
    from engines.content_checker import full_check
    
    report = full_check(
        video_path=video_path,
        title=title,
        channel=channel,
        original_duration=original_duration,
        clip_duration=clip_duration,
        has_tts=True,
        has_crop=True,
    )
    
    passed = report["recommendation"] != "DO NOT PUBLISH"
    
    return {
        "passed": passed,
        "report": report,
        "recommendation": report["recommendation"],
        "score": report["overall_score"],
    }


# ─── Main Pipeline ────────────────────────────────────────────────────────────
def run(
    source: str = None,
    niche: str = "education",
    max_clips: int = 3,
    min_segment: float = 15.0,
    max_segment: float = 60.0,
    auto_select: bool = True,
    skip_check: bool = False,
) -> dict:
    """
    Full podcast clipper pipeline.
    
    Args:
        source: YouTube URL or local file path. If None + auto_select, searches YouTube.
        niche: Content niche for podcast search
        max_clips: Maximum clips to create (default: 3)
        min_segment: Minimum clip duration
        max_segment: Maximum clip duration
        auto_select: If True and no source, auto-search YouTube for best podcast
        skip_check: If True, skip content quality check (for testing only)
    """
    logger.info(f"Podcast Clipper | Niche: {niche} | Max clips: {max_clips}")
    
    # Step 1: Get source
    podcast_title = ""
    
    if source is None and auto_select:
        # Auto-select podcast from YouTube
        selection = select_best_podcast(niche)
        if not selection["success"]:
            return {"success": False, "error": selection["error"]}
        source = selection["podcast"]["url"]
        podcast_title = selection["podcast"]["title"]
        logger.info(f"Auto-selected: {podcast_title}")
    
    if source and source.startswith("http"):
        dl = download_podcast(source)
        if not dl["success"]:
            return {"success": False, "error": dl["error"]}
        source_path = dl["path"]
        podcast_title = podcast_title or dl.get("title", "")
    elif source:
        source_path = source
        if not os.path.exists(source_path):
            return {"success": False, "error": f"File not found: {source_path}"}
    else:
        return {"success": False, "error": "No source provided and auto-select failed"}
    
    # Step 2: Detect segments
    segments = detect_segments(source_path, min_segment, max_segment)
    segments = segments[:max_clips]
    
    # Step 2.5: Safety gate on title + segments
    from engines.safety_gate import check_safety, get_safety_status
    safety_text = podcast_title + " " + " ".join(s.get("text", "") for s in segments)
    safety = check_safety(safety_text)
    safety_status = get_safety_status(safety)
    if safety_status == "BLOCKED":
        return {
            "success": False,
            "error": f"Safety gate BLOCKED: risk={safety.get('overall_risk', 0)}",
            "safety": safety,
        }
    logger.info(f"Safety: {safety_status} (risk={safety.get('overall_risk', 0):.3f})")
    
    # Step 3: Pre-check content before creating clips
    content_report = None
    if not skip_check:
        logger.info("Running content quality & copyright check...")
        content_report = check_content(
            video_path=source_path,
            title=podcast_title,
            channel="",
            original_duration=sum(s["duration"] for s in segments),
            clip_duration=min(s["duration"] for s in segments) if segments else 0,
        )
        
        if not content_report["passed"]:
            return {
                "success": False,
                "error": f"Content check FAILED: {content_report['recommendation']}",
                "content_report": content_report["report"],
            }
        
        logger.info(f"Content check PASSED (Score: {content_report['score']}/100)")
    
    # Step 4: Create clips with dedup + QA + analytics
    from engines.dedup_engine import check_duplicate, register_content
    from engines.shared_qa import run_qa
    from engines.revenue_tracker import log_video
    
    clips = []
    errors = []
    for i, seg in enumerate(segments):
        # Dedup check per segment
        dup = check_duplicate(
            source_url=source,
            segment_start=seg["start"],
            segment_end=seg["start"] + seg["duration"],
        )
        if dup.get("is_duplicate"):
            logger.warning(f"Segment duplicate: {seg['start']}-{seg['start'] + seg['duration']}")
            errors.append({"segment": f"{seg['start']}-{seg['start'] + seg['duration']}", "error": "duplicate"})
            continue
        
        result = create_clip(source_path, seg, i + 1, niche, podcast_title)
        if result["success"]:
            # QA check
            qa = run_qa(result["path"])
            if qa["overall"] == "FAILED":
                errors.append({"segment": i+1, "error": f"qa_failed: {qa['errors']}"})
                continue
            
            # Analytics
            video_id = log_video(
                title=result.get("caption", f"Podcast Clip {i+1}")[:60],
                niche=niche,
                agent_type="podcast_clipper",
                video_path=result["path"],
            )
            
            # Register for dedup
            register_content(
                video_path=result["path"],
                source_url=source,
                segment_start=seg["start"],
                segment_end=seg["start"] + seg["duration"],
                agent_type="podcast_clipper",
            )
            
            result["video_id"] = video_id
            result["qa_status"] = qa["overall"]
            result["safety_status"] = safety_status
            clips.append(result)
    
    return {
        "success": True,
        "source": source_path,
        "podcast_title": podcast_title,
        "niche": niche,
        "total_segments": len(segments),
        "clips_created": len(clips),
        "clips": clips,
        "errors": errors,
        "content_check": content_report["report"] if content_report else None,
        "source_safety": safety_status,
    }
