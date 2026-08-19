# BLOG TO VIDEO — SOURCE OF TRUTH
## Agent #3: Blog Post → Instagram Reel
**Document:** `agents/sources_of_truth/blog_to_video_SOURCE_OF_TRUTH.md`
**Version:** 1.0
**Last Updated:** 2026-08-19
**Auto-Update:** Daily at 00:00 UTC
**Purpose:** Complete reference for Blog to Video agent.

---

# 1. WHAT IS BLOG TO VIDEO?

Blog to Video takes a blog post (URL or text) and creates an **Instagram-ready video** by:
1. Scraping blog content from URL (or using provided text)
2. Generating a script with AI
3. Creating TTS voiceover
4. Building video with Pillow
5. Merging audio + video

**Output:** Vertical video with voiceover, ready for Instagram Reels.

---

# 2. WORKFLOW

```
BLOG URL OR TEXT
    ↓
┌─────────────────────────────────────────┐
│ 1. INPUT VALIDATION                     │
│    - URL or text provided?              │
│    - Not empty?                         │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 2. GET BLOG CONTENT                     │
│    - Scrape URL (if HTTP)               │
│    - Extract text                       │
│    - Or use provided text               │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 3. RIGHTS GATE                          │
│    - Check copyright risk               │
│    - Block if HIGH risk                 │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 4. SAFETY GATE                          │
│    - Check content                      │
│    - Block if violations                │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 5. GENERATE SCRIPT                      │
│    - AI script generation               │
│    - Hook, body, CTA                    │
│    - Duration: 30-60 seconds            │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 6. TTS GENERATION                       │
│    - macOS `say` command                │
│    - Natural voice                      │
│    - Rate: 150 wpm                      │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 7. VIDEO CREATION                       │
│    - Pillow frame generation            │
│    - Gradient backgrounds               │
│    - Text overlays                      │
│    - Safe zone enforcement              │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 8. MERGE                                │
│    - Video + audio                      │
│    - Volume balancing                   │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 9. QA CHECK                             │
│    - Resolution: 1080x1920              │
│    - Duration: 15-60 seconds            │
│    - Audio present                      │
│    - Instagram compliance               │
└─────────────────────────────────────────┘
    ↓
OUTPUT: Video with voiceover for Instagram
```

---

# 3. QUALITY STANDARDS

## Video Requirements
| Parameter | Requirement |
|-----------|-------------|
| Resolution | 1080 x 1920 px |
| Aspect Ratio | 9:16 (vertical) |
| Duration | 30-60 seconds |
| Codec | H.264 + AAC |
| Format | MP4 |

## Script Requirements
| Element | Requirement |
|---------|-------------|
| Hook | 5-15 words, attention-grabbing |
| Body | 3-5 key points |
| CTA | Clear call to action |
| Duration | 30-60 seconds when spoken |

---

# 4. BEST PRACTICES

## Before Conversion
1. **Check Source** — Ensure blog is accessible
2. **Verify Rights** — Use rights gate
3. **Clean Content** — Remove ads, navigation

## During Conversion
1. **Generate Good Script** — Clear, concise
2. **Natural TTS** — Appropriate rate
3. **Visual Design** — Engaging gradients

## After Conversion
1. **QA Check** — All standards met
2. **Safety Check** — No violations
3. **Register Content** — For dedup

---

# 5. COMMON ISSUES

| Issue | Cause | Solution |
|-------|-------|----------|
| Scrape fails | URL blocked | Use text input |
| Script too long | Blog too detailed | Summarize key points |
| TTS robotic | Rate too fast | Slow down rate |
| Video boring | No visuals | Add decorations |

---

# 6. PERFORMANCE METRICS

| Metric | Target | Current |
|--------|--------|---------|
| Conversion time | < 60s | ~45s |
| Script quality | ≥ 4/5 | ~3.5/5 |
| QA pass rate | ≥ 95% | ~90% |
| Scrape success | ≥ 80% | ~75% |

---

# 7. EXAMPLE USAGE

```bash
curl -X POST http://localhost:8003/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "blog_to_video",
    "blog_url_or_text": "https://example.com/blog-post",
    "niche": "tech_ai",
    "language": "en"
  }'
```

---

**This document is the permanent source of truth for Blog to Video agent.**

**Last verified:** August 19, 2026
