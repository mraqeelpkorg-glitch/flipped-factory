# PODCAST CLIPPER — SOURCE OF TRUTH
## Agent #2: Podcast → Instagram Reels
**Document:** `agents/sources_of_truth/podcast_clipper_SOURCE_OF_TRUTH.md`
**Version:** 1.0
**Last Updated:** 2026-08-19
**Auto-Update:** Daily at 00:00 UTC
**Purpose:** Complete reference for Podcast Clipper agent.

---

# 1. WHAT IS PODCAST CLIPPER?

Podcast Clipper takes a podcast (or auto-finds one) and creates **Instagram-ready clips** by:
1. Auto-searching YouTube for podcasts by niche
2. Downloading the podcast
3. Segmenting using FFmpeg silence detection
4. Creating vertical 9:16 clips
5. Adding TTS voiceover
6. Merging audio + video

**Output:** Multiple vertical clips with voiceover, ready for Instagram Reels.

---

# 2. WORKFLOW

```
NICHE INPUT (or auto-search)
    ↓
┌─────────────────────────────────────────┐
│ 1. PODCAST SELECTION                    │
│    - Search YouTube by niche            │
│    - Filter: 5min - 2hours              │
│    - Sort by views                      │
│    - Select best match                  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 2. DOWNLOAD                             │
│    - yt-dlp with cookies                │
│    - Format: MP4                        │
│    - Quality: Best available            │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 3. SEGMENT                              │
│    - FFmpeg silence detection           │
│    - Find natural break points          │
│    - Extract best segments              │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 4. CLIP                                 │
│    - Trim to segment                    │
│    - Crop to vertical 9:16              │
│    - Ensure 15-60 seconds               │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 5. VOICEOVER                            │
│    - macOS `say` command                │
│    - Natural TTS voice                  │
│    - Rate: 150 wpm                      │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 6. MERGE                                │
│    - Video + audio                      │
│    - Volume balancing                   │
│    - Final QA check                     │
└─────────────────────────────────────────┘
    ↓
OUTPUT: Vertical clips with voiceover
```

---

# 3. QUALITY STANDARDS

## Video Requirements
| Parameter | Requirement |
|-----------|-------------|
| Resolution | 1080 x 1920 px |
| Aspect Ratio | 9:16 (vertical) |
| Duration | 15-60 seconds |
| Codec | H.264 + AAC |
| Format | MP4 |

## Audio Requirements
| Parameter | Requirement |
|-----------|-------------|
| TTS Voice | macOS system voice |
| Rate | 150 wpm |
| Volume | 0.8 |
| Format | AAC |

---

# 4. NICHE SEARCH QUERIES

## Supported Niches
| Niche | Search Queries |
|-------|----------------|
| Health/Fitness | fitness podcast, health tips, workout motivation |
| Finance/Crypto | crypto podcast, investing tips, money advice |
| Tech/AI | AI podcast, technology trends, coding tips |
| Education | educational podcast, learning, science |
| Motivation | motivational podcast, success mindset |
| E-commerce | ecommerce podcast, dropshipping, online business |
| Food/Nutrition | cooking podcast, nutrition tips, recipes |
| Travel | travel podcast, adventure tips, digital nomad |
| Beauty/Skincare | beauty podcast, skincare tips, makeup |
| Productivity | productivity podcast, time management, business |

---

# 5. BEST PRACTICES

## Before Clipping
1. **Select Good Source** — High views, clear audio
2. **Check Duration** — 5min-2hours optimal
3. **Verify Niche** — Match target audience

## During Clipping
1. **Silence Detection** — Find natural breaks
2. **Complete Thoughts** — Don't cut mid-sentence
3. **Add Voiceover** — Enhance with TTS

## After Clipping
1. **QA Check** — Resolution, duration, audio
2. **Safety Check** — No violations
3. **Register Content** — For dedup

---

# 6. COMMON ISSUES

| Issue | Cause | Solution |
|-------|-------|----------|
| No podcasts found | Niche too specific | Use broader search |
| Poor audio quality | Source quality | Choose better source |
| Bad segmentation | Silence detection | Adjust thresholds |
| TTS sounds robotic | Rate too fast | Slow down rate |

---

# 7. PERFORMANCE METRICS

| Metric | Target | Current |
|--------|--------|---------|
| Clips per podcast | 3-5 | 3 |
| Clip duration | 15-60s | 30s |
| QA pass rate | ≥ 95% | ~90% |
| Search success | ≥ 90% | ~85% |

---

# 8. EXAMPLE USAGE

```bash
curl -X POST http://localhost:8003/api/podcast/run \
  -H "Content-Type: application/json" \
  -d '{
    "niche": "health_fitness",
    "max_clips": 3
  }'
```

---

**This document is the permanent source of truth for Podcast Clipper agent.**

**Last verified:** August 19, 2026
