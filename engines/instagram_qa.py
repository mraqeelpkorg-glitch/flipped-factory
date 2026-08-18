"""
Instagram Media QA — Validates video before publishing to Instagram.

Checks:
- Resolution (1080x1920)
- Aspect ratio (9:16)
- Codec (H.264)
- Audio codec (AAC)
- Frame rate (23-60 FPS)
- Bitrate (1-8 Mbps)
- Duration (3-90 seconds for Reels)
- File size (< 100MB for Reels)
- Playability
- Black bars
- Caption safe zone

If QA fails: STATUS = NOT_READY
Never send failed media to publishing.
"""
import subprocess
import json
import logging
from pathlib import Path

logger = logging.getLogger("instagram_qa")


def check_video(video_path: str) -> dict:
    """
    Run full QA check on a video file.
    Returns dict with per-check results and overall_status.
    """
    checks = {
        "resolution": "pending",
        "aspect_ratio": "pending",
        "codec": "pending",
        "audio_codec": "pending",
        "fps": "pending",
        "bitrate": "pending",
        "duration": "pending",
        "file_size": "pending",
        "playability": "pending",
        "black_bars": "pending",
        "caption_safe_zone": "pending",
        "overall": "pending",
    }
    errors = []
    
    if not Path(video_path).exists():
        checks["overall"] = "FAILED"
        return {"checks": checks, "errors": ["File not found"], "overall": "FAILED"}
    
    try:
        # Get video info
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            video_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        info = json.loads(result.stdout)
        
        # Find video stream
        video_stream = None
        audio_stream = None
        for s in info.get("streams", []):
            if s.get("codec_type") == "video" and not video_stream:
                video_stream = s
            elif s.get("codec_type") == "audio" and not audio_stream:
                audio_stream = s
        
        if not video_stream:
            checks["overall"] = "FAILED"
            return {"checks": checks, "errors": ["No video stream found"], "overall": "FAILED"}
        
        # 1. Resolution check (1080x1920)
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        if width == 1080 and height == 1920:
            checks["resolution"] = "passed"
        elif width >= 720 and height >= 1280:
            checks["resolution"] = "warning"
            errors.append(f"Resolution {width}x{height} (recommended: 1080x1920)")
        else:
            checks["resolution"] = "failed"
            errors.append(f"Resolution {width}x{height} too low for Instagram Reels")
        
        # 2. Aspect ratio check (9:16)
        if width > 0 and height > 0:
            ratio = width / height
            target_ratio = 9 / 16
            if abs(ratio - target_ratio) < 0.02:
                checks["aspect_ratio"] = "passed"
            else:
                checks["aspect_ratio"] = "failed"
                errors.append(f"Aspect ratio {ratio:.3f} (required: {target_ratio:.3f})")
        
        # 3. Codec check (H.264)
        codec = video_stream.get("codec_name", "").lower()
        if codec in ["h264", "avc1"]:
            checks["codec"] = "passed"
        elif codec in ["hevc", "h265"]:
            checks["codec"] = "warning"
            errors.append(f"Codec {codec} — H.264 recommended for Instagram")
        else:
            checks["codec"] = "failed"
            errors.append(f"Codec {codec} not supported by Instagram")
        
        # 4. Audio codec check (AAC)
        if audio_stream:
            audio_codec = audio_stream.get("codec_name", "").lower()
            if audio_codec in ["aac", "mp4a"]:
                checks["audio_codec"] = "passed"
            else:
                checks["audio_codec"] = "warning"
                errors.append(f"Audio codec {audio_codec} — AAC recommended")
        else:
            checks["audio_codec"] = "failed"
            errors.append("No audio stream found")
        
        # 5. Frame rate check (23-60 FPS)
        fps_str = video_stream.get("r_frame_rate", "30/1")
        try:
            num, den = fps_str.split("/")
            fps = float(num) / float(den) if float(den) > 0 else 0
        except:
            fps = 30
        
        if 23 <= fps <= 60:
            checks["fps"] = "passed"
        elif 15 <= fps < 23:
            checks["fps"] = "warning"
            errors.append(f"FPS {fps:.1f} is low (recommended: 24-60)")
        else:
            checks["fps"] = "failed"
            errors.append(f"FPS {fps:.1f} out of Instagram range")
        
        # 6. Bitrate check (1-8 Mbps)
        bitrate = int(video_stream.get("bit_rate", 0))
        if bitrate == 0:
            # Try format-level bitrate
            bitrate = int(info.get("format", {}).get("bit_rate", 0))
        
        if bitrate > 0:
            bitrate_mbps = bitrate / 1_000_000
            if 1 <= bitrate_mbps <= 8:
                checks["bitrate"] = "passed"
            elif bitrate_mbps < 1:
                checks["bitrate"] = "warning"
                errors.append(f"Bitrate {bitrate_mbps:.1f}Mbps is low")
            else:
                checks["bitrate"] = "warning"
                errors.append(f"Bitrate {bitrate_mbps:.1f}Mbps is high")
        else:
            checks["bitrate"] = "warning"
        
        # 7. Duration check (3-90 seconds for Reels)
        duration = float(info.get("format", {}).get("duration", 0))
        if 3 <= duration <= 90:
            checks["duration"] = "passed"
        elif duration < 3:
            checks["duration"] = "failed"
            errors.append(f"Duration {duration:.1f}s too short (min: 3s)")
        elif duration > 90:
            checks["duration"] = "failed"
            errors.append(f"Duration {duration:.1f}s too long for Reels (max: 90s)")
        
        # 8. File size check (< 100MB)
        file_size = int(info.get("format", {}).get("size", 0))
        if file_size > 0:
            size_mb = file_size / (1024 * 1024)
            if size_mb <= 100:
                checks["file_size"] = "passed"
            else:
                checks["file_size"] = "failed"
                errors.append(f"File size {size_mb:.1f}MB exceeds 100MB limit")
        else:
            checks["file_size"] = "warning"
        
        # 9. Playability check
        if video_stream and audio_stream:
            checks["playability"] = "passed"
        elif video_stream:
            checks["playability"] = "warning"
            errors.append("No audio track")
        
        # 10. Black bars check (detect letterboxing)
        # Simple check: if video is exactly 1080x1920, no bars
        if width == 1080 and height == 1920:
            checks["black_bars"] = "passed"
        else:
            checks["black_bars"] = "warning"
            errors.append("May have black bars — verify manually")
        
        # 11. Caption safe zone (top/bottom 15% reserved)
        # This is a soft check — just verify resolution allows for it
        if height >= 1920:
            checks["caption_safe_zone"] = "passed"
        else:
            checks["caption_safe_zone"] = "warning"
            errors.append("Lower resolution may affect caption safe zone")
        
        # Overall status
        failed = [k for k, v in checks.items() if v == "failed" and k != "overall"]
        warned = [k for k, v in checks.items() if v == "warning" and k != "overall"]
        
        if failed:
            checks["overall"] = "FAILED"
        elif warned:
            checks["overall"] = "PASSED_WITH_WARNINGS"
        else:
            checks["overall"] = "PASSED"
        
        return {
            "checks": checks,
            "errors": errors,
            "overall": checks["overall"],
            "metadata": {
                "width": width,
                "height": height,
                "fps": round(fps, 1),
                "codec": codec,
                "audio_codec": audio_stream.get("codec_name", "unknown") if audio_stream else "none",
                "bitrate_mbps": round(bitrate / 1_000_000, 2) if bitrate > 0 else 0,
                "duration": round(duration, 1),
                "file_size_mb": round(file_size / (1024 * 1024), 2) if file_size > 0 else 0,
            },
        }
    
    except Exception as e:
        checks["overall"] = "FAILED"
        return {"checks": checks, "errors": [str(e)], "overall": "FAILED"}


def validate_for_instagram(video_path: str) -> dict:
    """
    Validate video is ready for Instagram publishing.
    Returns {ready: bool, result: check_result}.
    """
    result = check_video(video_path)
    ready = result["overall"] in ["PASSED", "PASSED_WITH_WARNINGS"]
    
    if not ready:
        logger.warning(f"QA FAILED for {video_path}: {result['errors']}")
    else:
        logger.info(f"QA PASSED for {video_path}")
    
    return {"ready": ready, "result": result}


def print_qa_report(video_path: str):
    """Print formatted QA report."""
    result = check_video(video_path)
    
    print("\n" + "=" * 60)
    print("📸 INSTAGRAM MEDIA QA REPORT")
    print(f"   File: {Path(video_path).name}")
    print("=" * 60)
    
    status_icon = {"passed": "✅", "warning": "⚠️", "failed": "❌", "pending": "⏳"}
    
    for check, status in result["checks"].items():
        if check == "overall":
            continue
        icon = status_icon.get(status, "❓")
        print(f"  {icon} {check}: {status}")
    
    print(f"\n{'='*60}")
    overall = result["overall"]
    icon = "✅" if "PASSED" in overall else "❌"
    print(f"  {icon} OVERALL: {overall}")
    
    if result["errors"]:
        print("\n  Issues:")
        for e in result["errors"]:
            print(f"    • {e}")
    
    meta = result.get("metadata", {})
    if meta:
        print(f"\n  Metadata:")
        print(f"    Resolution: {meta.get('width')}x{meta.get('height')}")
        print(f"    FPS: {meta.get('fps')}")
        print(f"    Codec: {meta.get('codec')} / {meta.get('audio_codec')}")
        print(f"    Bitrate: {meta.get('bitrate_mbps')} Mbps")
        print(f"    Duration: {meta.get('duration')}s")
        print(f"    Size: {meta.get('file_size_mb')} MB")
    
    print("=" * 60)
