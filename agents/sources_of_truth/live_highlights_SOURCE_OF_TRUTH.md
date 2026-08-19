# LIVE HIGHLIGHTS — SOURCE OF TRUTH
## Agent #11: Live Stream → Highlight Clips
**Document:** `agents/sources_of_truth/live_highlights_SOURCE_OF_TRUTH.md`
**Version:** 1.0
**Last Updated:** 2026-08-19
**Auto-Update:** Daily at 00:00 UTC
**Purpose:** Complete reference for Live Highlights agent.

---

# 1. WHAT IS LIVE HIGHLIGHTS?

Live Highlights takes a live stream recording and **extracts best moments** as clips by:
1. Taking live video path
2. Transcribing video
3. Finding best moments (silence detection)
4. Extracting clips
5. Cropping to vertical 9:16

**Output:** Multiple vertical highlight clips, ready for Instagram Reels.

---

# 2. WORKFLOW

```
LIVE VIDEO
    ↓
┌─────────────────────────────────────────┐
│ 1. INPUT VALIDATION                     │
│    - File exists?                       │
│    - Valid format?                      │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 2. RIGHTS GATE                          │
│    - Livestream authorized?             │
│    - Block if HIGH risk                 │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 3. SAFETY GATE                          │
│    - Check content                      │
│    - Block if violations                │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 4. TRANSCRIBE                           │
│    - FFmpeg silence detection           │
│    - Find natural break points          │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 5. FIND BEST MOMENTS                    │
│    - Segment analysis                   │
│    - Select top clips                   │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 6. EXTRACT CLIPS                        │
│    - Trim to segments                   │
│    - Crop to vertical 9:16              │
│    - Ensure 15-60 seconds               │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 7. QA CHECK                             │
│    - Resolution: 1080x1920              │
│    - Duration: 15-60 seconds            │
│    - Instagram compliance               │
└─────────────────────────────────────────┘
    ↓
OUTPUT: Multiple highlight clips
```

---

# 3. QUALITY STANDARDS

## Video Requirements
| Parameter | Requirement |
|-----------|-------------|
| Resolution | 1080 x 1920 px |
| Aspect Ratio | 9:16 (vertical) |
| Duration | 15-60 seconds |
| Clips | 3-5 per stream |
| Format | MP4 |

---

# 4. BEST PRACTICES

## Before Extraction
1. **Check Rights** — Stream must be authorized
2. **Verify Quality** — Good enough for clips
3. **Rights Gate** — Check for copyright

## During Extraction
1. **Natural Breaks** — Don't cut mid-sentence
2. **Best Moments** — High energy, key points
3. **Vertical Crop** — 9:16 aspect ratio

## After Extraction
1. **QA Check** — All standards met
2. **Register Content** — For dedup

---

# 5. COMMON ISSUES

| Issue | Cause | Solution |
|-------|-------|----------|
| Bad cuts | Wrong breakpoints | Improve silence detection |
| Too many clips | Overwhelming | Limit to 3-5 |
| Poor quality | Source quality | Choose better source |

---

# 6. PERFORMANCE METRICS

| Metric | Target | Current |
|--------|--------|---------|
| Extraction time | < 60s | ~45s |
| Clips per stream | 3-5 | 3 |
| QA pass rate | ≥ 95% | ~90% |

---

# 7. EXAMPLE USAGE

```bash
curl -X POST http://localhost:8003/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "live_highlights",
    "live_video_path": "data/videos/raw/stream.mp4",
    "niche": "motivation",
    "max_clips": 3
  }'
```

---

**Last verified:** August 19, 2026
