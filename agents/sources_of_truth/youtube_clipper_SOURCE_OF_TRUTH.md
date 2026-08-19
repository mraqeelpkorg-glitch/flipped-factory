# YOUTUBE CLIPPER — SOURCE OF TRUTH
## Agent #1: YouTube → Instagram Reels
**Document:** `agents/sources_of_truth/youtube_clipper_SOURCE_OF_TRUTH.md`
**Version:** 1.0
**Last Updated:** 2026-08-19
**Auto-Update:** Daily at 00:00 UTC
**Purpose:** Complete reference for YouTube Clipper agent.

---

# 1. WHAT IS YOUTUBE CLIPPER?

YouTube Clipper takes a YouTube video and creates **Instagram-ready vertical clips** by:
1. Downloading the YouTube video
2. Transcribing the audio
3. Finding the best segments (most words = most engaging)
4. Cropping to vertical 9:16 format
5. Creating multiple clips

**Output:** 1-3 vertical clips ready for Instagram Reels.

---

# 2. WORKFLOW

```
YOUTUBE URL
    ↓
┌─────────────────────────────────────────┐
│ 1. INPUT VALIDATION                     │
│    - Valid URL?                         │
│    - Starts with http?                  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 2. RIGHTS GATE                          │
│    - Check copyright risk               │
│    - Block if HIGH risk                 │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 3. DOWNLOAD VIDEO                       │
│    - yt-dlp with cookies                │
│    - Format: MP4                        │
│    - Quality: Best available            │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 4. TRANSCRIBE                           │
│    - Whisper (if available)             │
│    - FFmpeg silence detection           │
│    - Extract segments                   │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 5. SAFETY CHECK                         │
│    - Check transcript                   │
│    - Block if violations                │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 6. CREATE CLIPS (1-3)                   │
│    - Score segments by word count       │
│    - Trim to best segments              │
│    - Crop to vertical 9:16              │
│    - QA check each clip                 │
│    - Register content                   │
└─────────────────────────────────────────┘
    ↓
OUTPUT: Vertical clips for Instagram
```

---

# 3. QUALITY STANDARDS

## Video Requirements
| Parameter | Requirement |
|-----------|-------------|
| Resolution | 1080 x 1920 px |
| Aspect Ratio | 9:16 (vertical) |
| Duration | 15-60 seconds |
| Codec | H.264 |
| Format | MP4 |

## Clip Selection Rules
1. **Word Count** — More words = more engaging
2. **Duration** — Max 60 seconds per clip
3. **Content** — Must be complete thought
4. **Safety** — No violations in transcript

---

# 4. BEST PRACTICES

## Before Clipping
1. **Check Copyright** — Use rights gate first
2. **Clean Audio** — Better transcription
3. **Short Videos** — 5-15 minutes optimal

## During Clipping
1. **Score Segments** — Word count as proxy
2. **Complete Thoughts** — Don't cut mid-sentence
3. **Vertical Crop** — Center the speaker

## After Clipping
1. **QA Check** — Resolution, duration, audio
2. **Safety Check** — No violations
3. **Register Content** — For dedup

---

# 5. COMMON ISSUES

| Issue | Cause | Solution |
|-------|-------|----------|
| Download fails | YouTube blocking | Use cookies |
| Poor transcription | Noisy audio | Use clearer source |
| Bad crop | Speaker off-center | Manual adjustment |
| Safety block | Violations | Choose different video |

---

# 6. PERFORMANCE METRICS

| Metric | Target | Current |
|--------|--------|---------|
| Clips per video | 2-3 | 2 |
| Clip duration | 15-60s | 30s |
| QA pass rate | ≥ 95% | ~90% |
| Download success | ≥ 90% | ~85% |

---

# 7. EXAMPLE USAGE

```bash
curl -X POST http://localhost:8003/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "youtube_clipper",
    "youtube_url": "https://www.youtube.com/watch?v=example",
    "niche": "tech_ai",
    "max_clips": 3
  }'
```

---

**This document is the permanent source of truth for YouTube Clipper agent.**

**Last verified:** August 19, 2026
