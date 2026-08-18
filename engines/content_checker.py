"""
Content Quality & Copyright Checker

Checks:
1. COPYRIGHT — Is this content safe to use? (Music, logos, watermarks)
2. QUALITY — Resolution, audio clarity, visual quality
3. AUTHORITY — Is this educational/informational vs entertainment
4. TRANSFORMATIVE — Are we adding enough value (TTS, crop, captions)
5. RISK SCORE — Overall risk rating (low/medium/high)

Purpose: Protect the channel from copyright strikes and ensure quality.
"""
import subprocess
import json
import logging
import re
from pathlib import Path

logger = logging.getLogger("content_checker")

# ─── Copyright Risk Keywords (in titles/descriptions) ────────────────────────
HIGH_RISK_KEYWORDS = [
    "official music video", "music video", "full song", "concert",
    "live performance", "movie trailer", "film clip", "tv show",
    "copyright", "all rights reserved", "do not use",
    "nba", "nfl", "ufc", "wwe", "fifa",
    "disney", "marvel", "netflix", "hbo", "paramount",
    "playstation", "xbox", "nintendo",
]

MEDIUM_RISK_KEYWORDS = [
    "reaction", "review", "compilation", "best of",
    "funny moments", "highlights", "montage",
    "interview", "talk show", "podcast",
]

SAFE_KEYWORDS = [
    "educational", "tutorial", "how to", "explained",
    "documentary", "lecture", "lesson", "learn",
    "science", "history", "technology", "coding",
    "motivation", "self improvement", "productivity",
    "business", "entrepreneur", "startup",
    "health", "fitness", "nutrition", "wellness",
    "finance", "investing", "crypto", "bitcoin",
    "ai", "artificial intelligence", "machine learning",
]


def check_copyright(title: str, description: str = "", channel: str = "") -> dict:
    """
    Check copyright risk based on metadata.
    Returns {risk_level, score, reasons, safe_to_use}.
    """
    text = f"{title} {description} {channel}".lower()
    
    high_risk = []
    medium_risk = []
    safe_signs = []
    
    for kw in HIGH_RISK_KEYWORDS:
        if kw in text:
            high_risk.append(kw)
    
    for kw in MEDIUM_RISK_KEYWORDS:
        if kw in text:
            medium_risk.append(kw)
    
    for kw in SAFE_KEYWORDS:
        if kw in text:
            safe_signs.append(kw)
    
    # Calculate risk score (0-100, higher = more risky)
    score = 0
    score += len(high_risk) * 25
    score += len(medium_risk) * 10
    score -= len(safe_signs) * 10
    score = max(0, min(100, score))
    
    # Determine risk level
    if score >= 50:
        risk_level = "HIGH"
    elif score >= 25:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    safe_to_use = risk_level == "LOW"
    
    reasons = []
    if high_risk:
        reasons.append(f"HIGH RISK: {', '.join(high_risk)}")
    if medium_risk:
        reasons.append(f"MEDIUM RISK: {', '.join(medium_risk)}")
    if safe_signs:
        reasons.append(f"SAFE SIGNS: {', '.join(safe_signs)}")
    
    return {
        "risk_level": risk_level,
        "score": score,
        "safe_to_use": safe_to_use,
        "reasons": reasons,
        "high_risk": high_risk,
        "medium_risk": medium_risk,
        "safe_signs": safe_signs,
    }


def check_audio_quality(video_path: str) -> dict:
    """
    Check audio quality — detect music, speech clarity, background noise.
    Returns {has_speech, has_music, quality_score, issues}.
    """
    try:
        # Get audio stream info
        cmd = [
            "ffprobe", "-v", "quiet",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_name,sample_rate,channels,bit_rate",
            "-of", "json",
            video_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        audio_info = json.loads(result.stdout)
        
        issues = []
        quality_score = 100
        
        if not audio_info.get("streams"):
            return {
                "has_speech": False,
                "has_music": False,
                "quality_score": 0,
                "issues": ["No audio stream found"],
            }
        
        stream = audio_info["streams"][0]
        
        # Check sample rate (speech needs >= 16000)
        sample_rate = int(stream.get("sample_rate", 0))
        if sample_rate < 16000:
            issues.append(f"Low sample rate: {sample_rate}Hz")
            quality_score -= 30
        
        # Check bitrate
        bitrate = int(stream.get("bit_rate", 0))
        if bitrate > 0 and bitrate < 64000:
            issues.append(f"Low bitrate: {bitrate/1000:.0f}kbps")
            quality_score -= 20
        
        # Check channels
        channels = int(stream.get("channels", 0))
        if channels == 0:
            issues.append("No audio channels")
            quality_score -= 50
        
        # Detect if there's music using volume analysis
        cmd_vol = [
            "ffmpeg", "-i", video_path,
            "-af", "volumedetect",
            "-f", "null", "-"
        ]
        vol_result = subprocess.run(cmd_vol, capture_output=True, text=True, timeout=30)
        
        # Parse volume info
        mean_vol = None
        for line in vol_result.stderr.split("\n"):
            if "mean_volume" in line:
                match = re.search(r'mean_volume:\s*([-\d.]+)', line)
                if match:
                    mean_vol = float(match.group(1))
        
        has_music = False
        has_speech = True  # Assume speech if audio exists
        
        if mean_vol is not None:
            if mean_vol > -10:
                issues.append("Very loud audio (possible music)")
                has_music = True
                quality_score -= 10
            elif mean_vol < -40:
                issues.append("Very quiet audio")
                quality_score -= 20
        
        return {
            "has_speech": has_speech,
            "has_music": has_music,
            "quality_score": max(0, quality_score),
            "mean_volume": mean_vol,
            "issues": issues,
        }
    
    except Exception as e:
        return {
            "has_speech": False,
            "has_music": False,
            "quality_score": 50,
            "issues": [f"Audio check failed: {str(e)}"],
        }


def check_video_quality(video_path: str) -> dict:
    """
    Check video quality — resolution, bitrate, framerate.
    Returns {quality_score, resolution, issues}.
    """
    try:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,bit_rate,codec_name",
            "-of", "json",
            video_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        video_info = json.loads(result.stdout)
        
        issues = []
        quality_score = 100
        
        if not video_info.get("streams"):
            return {
                "quality_score": 0,
                "resolution": "unknown",
                "issues": ["No video stream found"],
            }
        
        stream = video_info["streams"][0]
        width = int(stream.get("width", 0))
        height = int(stream.get("height", 0))
        
        # Resolution check
        if width < 720 or height < 1280:
            issues.append(f"Low resolution: {width}x{height}")
            quality_score -= 30
        elif width < 1080 or height < 1920:
            issues.append(f"Medium resolution: {width}x{height}")
            quality_score -= 10
        
        # Bitrate check
        bitrate = int(stream.get("bit_rate", 0))
        if bitrate > 0 and bitrate < 1000000:
            issues.append(f"Low bitrate: {bitrate/1000000:.1f}Mbps")
            quality_score -= 20
        
        # Frame rate check
        fps_str = stream.get("r_frame_rate", "30/1")
        try:
            num, den = fps_str.split("/")
            fps = float(num) / float(den)
            if fps < 24:
                issues.append(f"Low framerate: {fps:.1f}fps")
                quality_score -= 10
        except:
            pass
        
        resolution = f"{width}x{height}"
        
        return {
            "quality_score": max(0, quality_score),
            "resolution": resolution,
            "width": width,
            "height": height,
            "issues": issues,
        }
    
    except Exception as e:
        return {
            "quality_score": 50,
            "resolution": "unknown",
            "issues": [f"Video check failed: {str(e)}"],
        }


def check_transformative_value(
    original_duration: float,
    clip_duration: float,
    has_tts: bool,
    has_crop: bool,
    has_captions: bool = False,
) -> dict:
    """
    Check if we're adding enough transformative value.
    Fair use requires: commentary, criticism, education, transformation.
    
    Our value adds:
    - TTS voiceover (commentary)
    - Vertical crop (format transformation)
    - Caption overlay (educational value)
    - Short clips (fair use proportion)
    """
    score = 0
    reasons = []
    
    # Duration ratio (shorter = more transformative)
    ratio = clip_duration / original_duration if original_duration > 0 else 1
    if ratio <= 0.1:
        score += 30
        reasons.append(f"Short clip ({ratio*100:.0f}% of original) — fair use proportion")
    elif ratio <= 0.25:
        score += 20
        reasons.append(f"Moderate clip ({ratio*100:.0f}% of original)")
    else:
        score += 5
        reasons.append(f"Long clip ({ratio*100:.0f}% of original) — may be too much")
    
    # TTS voiceover adds commentary
    if has_tts:
        score += 25
        reasons.append("TTS voiceover adds commentary/education value")
    
    # Vertical crop transforms the format
    if has_crop:
        score += 20
        reasons.append("Vertical crop transforms original format")
    
    # Captions add educational value
    if has_captions:
        score += 15
        reasons.append("Captions add educational value")
    
    # Determine transformative level
    if score >= 70:
        level = "HIGH"
    elif score >= 40:
        level = "MODERATE"
    else:
        level = "LOW"
    
    return {
        "score": max(0, min(100, score)),
        "level": level,
        "reasons": reasons,
    }


def check_content_authority(title: str, description: str = "", channel: str = "") -> dict:
    """
    Check if content is authoritative and educational.
    Returns {is_authority, category, confidence}.
    """
    text = f"{title} {description} {channel}".lower()
    
    categories = {
        "educational": ["tutorial", "how to", "explained", "lecture", "lesson", "learn", "course"],
        "scientific": ["science", "research", "study", "experiment", "data", "evidence"],
        "news_analysis": ["analysis", "review", "breakdown", "deep dive", "investigation"],
        "motivational": ["motivation", "success", "mindset", "growth", "self improvement"],
        "business": ["business", "entrepreneur", "startup", "finance", "investing", "marketing"],
        "technology": ["technology", "ai", "coding", "programming", "software", "tech"],
        "health": ["health", "fitness", "nutrition", "wellness", "medical", "doctor"],
    }
    
    scores = {}
    for cat, keywords in categories.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[cat] = score
    
    if not scores:
        return {
            "is_authority": False,
            "category": "unknown",
            "confidence": 0,
            "reason": "No authority indicators found",
        }
    
    best_cat = max(scores, key=scores.get)
    confidence = min(100, scores[best_cat] * 30)
    
    return {
        "is_authority": confidence >= 60,
        "category": best_cat,
        "confidence": confidence,
        "all_categories": scores,
    }


def full_check(
    video_path: str,
    title: str = "",
    description: str = "",
    channel: str = "",
    original_duration: float = 0,
    clip_duration: float = 0,
    has_tts: bool = False,
    has_crop: bool = True,
) -> dict:
    """
    Full content quality and copyright check.
    Returns comprehensive report.
    """
    logger.info(f"Running full check on: {video_path}")
    
    # 1. Copyright check
    copyright_check = check_copyright(title, description, channel)
    
    # 2. Audio quality
    audio_check = check_audio_quality(video_path)
    
    # 3. Video quality
    video_check = check_video_quality(video_path)
    
    # 4. Transformative value
    transform_check = check_transformative_value(
        original_duration, clip_duration, has_tts, has_crop
    )
    
    # 5. Content authority
    authority_check = check_content_authority(title, description, channel)
    
    # 6. Overall risk assessment
    overall_score = 100
    
    # Deductions
    if copyright_check["risk_level"] == "HIGH":
        overall_score -= 50
    elif copyright_check["risk_level"] == "MEDIUM":
        overall_score -= 20
    
    if audio_check["quality_score"] < 50:
        overall_score -= 20
    
    if video_check["quality_score"] < 50:
        overall_score -= 20
    
    if transform_check["score"] < 40:
        overall_score -= 15
    
    # Bonuses
    if authority_check["is_authority"]:
        overall_score += 10
    
    if transform_check["score"] >= 70:
        overall_score += 10
    
    overall_score = max(0, min(100, overall_score))
    
    # Final recommendation
    if overall_score >= 70 and copyright_check["safe_to_use"]:
        recommendation = "SAFE TO PUBLISH"
    elif overall_score >= 50:
        recommendation = "REVIEW NEEDED"
    else:
        recommendation = "DO NOT PUBLISH"
    
    return {
        "overall_score": overall_score,
        "recommendation": recommendation,
        "copyright": copyright_check,
        "audio_quality": audio_check,
        "video_quality": video_check,
        "transformative": transform_check,
        "authority": authority_check,
    }


def print_report(report: dict):
    """Print a formatted check report."""
    print("\n" + "=" * 60)
    print("📋 CONTENT QUALITY & COPYRIGHT CHECK REPORT")
    print("=" * 60)
    
    print(f"\n🎯 OVERALL SCORE: {report['overall_score']}/100")
    print(f"📝 RECOMMENDATION: {report['recommendation']}")
    
    # Copyright
    c = report["copyright"]
    print(f"\n🔒 COPYRIGHT: {c['risk_level']} risk (Score: {c['score']})")
    print(f"   Safe to use: {'✅ YES' if c['safe_to_use'] else '❌ NO'}")
    for r in c["reasons"]:
        print(f"   • {r}")
    
    # Audio
    a = report["audio_quality"]
    print(f"\n🔊 AUDIO QUALITY: {a['quality_score']}/100")
    print(f"   Has speech: {'✅' if a['has_speech'] else '❌'}")
    print(f"   Has music: {'⚠️' if a['has_music'] else '✅'}")
    for i in a["issues"]:
        print(f"   • {i}")
    
    # Video
    v = report["video_quality"]
    print(f"\n🎬 VIDEO QUALITY: {v['quality_score']}/100")
    print(f"   Resolution: {v['resolution']}")
    for i in v["issues"]:
        print(f"   • {i}")
    
    # Transformative
    t = report["transformative"]
    print(f"\n🔄 TRANSFORMATIVE VALUE: {t['score']}/100 ({t['level']})")
    for r in t["reasons"]:
        print(f"   • {r}")
    
    # Authority
    au = report["authority"]
    print(f"\n📚 CONTENT AUTHORITY: {'✅ YES' if au['is_authority'] else '❌ NO'}")
    print(f"   Category: {au['category']} ({au['confidence']}% confidence)")
    
    print("\n" + "=" * 60)
