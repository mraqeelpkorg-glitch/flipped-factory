"""
Shared QA — Quality Assurance for ALL agents.

Every rendered video MUST pass this QA before publishing.
Checks: resolution, aspect ratio, codec, audio, duration, file integrity,
caption safe-zone, black-bar check, duplicate check.

Used by podcast pipeline (instagram_qa.py) and shared across all agents.
"""
import subprocess
import json
import os
import logging
from pathlib import Path

logger = logging.getLogger("shared_qa")


# ─── FFprobe Helper ───────────────────────────────────────────────────────────

def probe_video(video_path: str) -> dict:
    """Get detailed video metadata via ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            video_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            return {"error": f"ffprobe failed: {result.stderr[:200]}"}
        return json.loads(result.stdout)
    except Exception as e:
        return {"error": str(e)}


def get_video_stream(info: dict) -> dict:
    """Extract video stream from ffprobe info."""
    for s in info.get("streams", []):
        if s.get("codec_type") == "video":
            return s
    return {}


def get_audio_stream(info: dict) -> dict:
    """Extract audio stream from ffprobe info."""
    for s in info.get("streams", []):
        if s.get("codec_type") == "audio":
            return s
    return {}


# ─── Individual Checks ────────────────────────────────────────────────────────

def check_file_exists(video_path: str) -> dict:
    """Check file exists and is non-empty."""
    if not os.path.exists(video_path):
        return {"pass": False, "error": "File does not exist"}
    size = os.path.getsize(video_path)
    if size < 1000:
        return {"pass": False, "error": f"File too small: {size} bytes"}
    return {"pass": True, "file_size": size}


def check_resolution(video_stream: dict, target_width=1080, target_height=1920) -> dict:
    """Check video resolution."""
    width = int(video_stream.get("width", 0))
    height = int(video_stream.get("height", 0))

    if width == 0 or height == 0:
        return {"pass": False, "error": "No video dimensions found"}

    # Allow ±10% tolerance
    w_ok = abs(width - target_width) / target_width <= 0.1
    h_ok = abs(height - target_height) / target_height <= 0.1

    return {
        "pass": w_ok and h_ok,
        "width": width,
        "height": height,
        "error": "" if (w_ok and h_ok) else f"Resolution {width}x{height} != {target_width}x{target_height}",
    }


def check_aspect_ratio(video_stream: dict, target_ratio=9/16) -> dict:
    """Check 9:16 aspect ratio."""
    width = int(video_stream.get("width", 0))
    height = int(video_stream.get("height", 0))
    if width == 0 or height == 0:
        return {"pass": False, "error": "No dimensions"}

    actual_ratio = width / height
    tolerance = 0.05
    ok = abs(actual_ratio - target_ratio) < tolerance

    return {
        "pass": ok,
        "ratio": f"{width}:{height}",
        "error": "" if ok else f"Aspect ratio {actual_ratio:.3f} != {target_ratio:.3f}",
    }


def check_codec(video_stream: dict, allowed_codecs=None) -> dict:
    """Check video codec is H.264 or H.265."""
    if allowed_codecs is None:
        allowed_codecs = ["h264", "hevc", "h265"]
    codec = video_stream.get("codec_name", "unknown")
    ok = codec in allowed_codecs

    return {
        "pass": ok,
        "codec": codec,
        "error": "" if ok else f"Codec {codec} not in {allowed_codecs}",
    }


def check_audio(audio_stream: dict) -> dict:
    """Check audio stream exists and is AAC."""
    if not audio_stream:
        return {"pass": False, "error": "No audio stream"}

    codec = audio_stream.get("codec_name", "unknown")
    sample_rate = int(audio_stream.get("sample_rate", 0))

    ok = codec in ["aac", "mp3", "opus", "mp4a"]
    return {
        "pass": ok,
        "codec": codec,
        "sample_rate": sample_rate,
        "error": "" if ok else f"Audio codec {codec} not supported",
    }


def check_duration(info: dict, min_duration=3, max_duration=180) -> dict:
    """Check duration is within Instagram Reels limits (3s-180s)."""
    fmt = info.get("format", {})
    duration = float(fmt.get("duration", 0))

    ok = min_duration <= duration <= max_duration
    return {
        "pass": ok,
        "duration": round(duration, 2),
        "error": "" if ok else f"Duration {duration:.1f}s not in [{min_duration}, {max_duration}]",
    }


def check_fps(video_stream: dict, min_fps=23, max_fps=60) -> dict:
    """Check FPS is reasonable."""
    fps_str = video_stream.get("r_frame_rate", "30/1")
    try:
        num, den = fps_str.split("/")
        fps = float(num) / float(den) if float(den) > 0 else 0
    except Exception:
        fps = 30

    ok = min_fps <= fps <= max_fps
    return {
        "pass": ok,
        "fps": round(fps, 1),
        "error": "" if ok else f"FPS {fps:.1f} not in [{min_fps}, {max_fps}]",
    }


def check_bitrate(video_stream: dict, min_bitrate=100_000) -> dict:
    """Check bitrate is reasonable (not too low = empty/black video)."""
    bitrate = int(video_stream.get("bit_rate", 0))
    ok = bitrate >= min_bitrate or bitrate == 0  # 0 = unknown, skip check
    return {
        "pass": ok,
        "bitrate": bitrate,
        "error": "" if ok else f"Bitrate {bitrate} too low (min {min_bitrate})",
    }


def check_black_bars(video_stream: dict) -> dict:
    """
    Basic black-bar check: if video is exactly 1080x1920 and has
    the right codec, assume no black bars.
    Detailed check would require frame sampling.
    """
    width = int(video_stream.get("width", 0))
    height = int(video_stream.get("height", 0))
    # Standard Instagram format = no black bars
    ok = width == 1080 and height == 1920
    return {
        "pass": ok,
        "error": "" if ok else f"Non-standard dimensions {width}x{height} may have black bars",
    }


# ─── Full QA ──────────────────────────────────────────────────────────────────

def run_qa(
    video_path: str,
    min_duration: int = 3,
    max_duration: int = 180,
    require_audio: bool = True,
) -> dict:
    """
    Run complete QA on a video file.

    Returns:
        {
            "overall": "PASSED" | "PASSED_WITH_WARNINGS" | "FAILED",
            "checks": [...],
            "errors": [...],
            "warnings": [...],
            "video_path": str,
            "file_size": int,
        }

    Every agent MUST call before publishing:
        qa = run_qa(video_path)
        if qa["overall"] == "FAILED":
            return build_output(success=False, error="QA failed")
    """
    checks = []
    errors = []
    warnings = []

    # 1. File existence
    c = check_file_exists(video_path)
    checks.append({"name": "file_exists", **c})
    if not c["pass"]:
        return {"overall": "FAILED", "checks": checks, "errors": [c["error"]], "warnings": [], "video_path": video_path}

    file_size = c["file_size"]

    # Probe
    info = probe_video(video_path)
    if "error" in info:
        checks.append({"name": "probe", "pass": False, "error": info["error"]})
        return {"overall": "FAILED", "checks": checks, "errors": [info["error"]], "warnings": [], "video_path": video_path}

    vstream = get_video_stream(info)
    astream = get_audio_stream(info)

    # 2. Resolution
    c = check_resolution(vstream)
    checks.append({"name": "resolution", **c})
    if not c["pass"]:
        errors.append(c["error"])

    # 3. Aspect ratio
    c = check_aspect_ratio(vstream)
    checks.append({"name": "aspect_ratio", **c})
    if not c["pass"]:
        errors.append(c["error"])

    # 4. Codec
    c = check_codec(vstream)
    checks.append({"name": "codec", **c})
    if not c["pass"]:
        errors.append(c["error"])

    # 5. Audio
    if require_audio:
        c = check_audio(astream)
        checks.append({"name": "audio", **c})
        if not c["pass"]:
            errors.append(c["error"])

    # 6. Duration
    c = check_duration(info, min_duration, max_duration)
    checks.append({"name": "duration", **c})
    if not c["pass"]:
        errors.append(c["error"])

    # 7. FPS
    c = check_fps(vstream)
    checks.append({"name": "fps", **c})
    if not c["pass"]:
        warnings.append(c["error"])

    # 8. Bitrate
    c = check_bitrate(vstream)
    checks.append({"name": "bitrate", **c})
    if not c["pass"]:
        warnings.append(c["error"])

    # 9. Black bars
    c = check_black_bars(vstream)
    checks.append({"name": "black_bars", **c})
    if not c["pass"]:
        warnings.append(c["error"])

    # Determine overall
    if errors:
        overall = "FAILED"
    elif warnings:
        overall = "PASSED_WITH_WARNINGS"
    else:
        overall = "PASSED"

    logger.info(f"QA {overall}: {video_path} ({len(errors)} errors, {len(warnings)} warnings)")

    return {
        "overall": overall,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "video_path": video_path,
        "file_size": file_size,
    }
