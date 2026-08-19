# BTS EDUCATIONAL — SOURCE OF TRUTH
## Agent #8: Behind-the-Scenes → Educational Tutorial
**Document:** `agents/sources_of_truth/bts_educational_SOURCE_OF_TRUTH.md`
**Version:** 1.0
**Last Updated:** 2026-08-19
**Auto-Update:** Daily at 00:00 UTC
**Purpose:** Complete reference for BTS Educational agent.

---

# 1. WHAT IS BTS EDUCATIONAL?

BTS Educational takes behind-the-scenes footage and converts it into **educational tutorial content** by:
1. Taking BTS video path
2. Transcribing video (or using placeholder)
3. Generating tutorial script
4. Creating TTS voiceover
5. Building video with educational overlays
6. Merging audio + video

**Output:** Vertical educational tutorial video, ready for Instagram Reels.

---

# 2. WORKFLOW

```
BTS VIDEO
    ↓
┌─────────────────────────────────────────┐
│ 1. INPUT VALIDATION                     │
│    - File exists?                       │
│    - Valid format?                      │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 2. RIGHTS GATE                          │
│    - BTS footage authorized?            │
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
│    - Extract text (or placeholder)      │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 5. GENERATE TUTORIAL SCRIPT             │
│    - AI script generation               │
│    - Educational format                 │
│    - Duration: 30-60 seconds            │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 6. TTS + VIDEO                          │
│    - Voiceover generation               │
│    - Video with step overlays           │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 7. MERGE + QA                           │
│    - Video + audio                      │
│    - Instagram compliance               │
└─────────────────────────────────────────┘
    ↓
OUTPUT: Educational tutorial video
```

---

# 3. QUALITY STANDARDS

## Video Requirements
| Parameter | Requirement |
|-----------|-------------|
| Resolution | 1080 x 1920 px |
| Aspect Ratio | 9:16 (vertical) |
| Duration | 30-60 seconds |
| Format | MP4 |

## Script Requirements
| Element | Requirement |
|---------|-------------|
| Steps | Clear numbered steps |
| Explanations | Simple, concise |
| CTA | "Follow for more tips" |

---

# 4. BEST PRACTICES

## Before Conversion
1. **Check Rights** — BTS must be authorized
2. **Verify Quality** — Good enough for tutorial
3. **Identify Steps** — What can be taught?

## During Conversion
1. **Clear Steps** — Numbered, simple
2. **Visual Overlays** — Step numbers on screen
3. **Natural TTS** — Appropriate rate

## After Conversion
1. **QA Check** — All standards met
2. **Register Content** — For dedup

---

# 5. COMMON ISSUES

| Issue | Cause | Solution |
|-------|-------|----------|
| Steps unclear | Poor transcription | Use placeholder text |
| Video too long | Too many steps | Limit to 3-5 steps |
| Boring visuals | No overlays | Add step numbers |

---

# 6. PERFORMANCE METRICS

| Metric | Target | Current |
|--------|--------|---------|
| Conversion time | < 60s | ~45s |
| QA pass rate | ≥ 95% | ~90% |

---

# 7. EXAMPLE USAGE

```bash
curl -X POST http://localhost:8003/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "bts_educational",
    "bts_video_path": "data/videos/raw/bts.mp4",
    "niche": "tech_ai",
    "tutorial_topic": "How to set up VS Code"
  }'
```

---

**Last verified:** August 19, 2026
