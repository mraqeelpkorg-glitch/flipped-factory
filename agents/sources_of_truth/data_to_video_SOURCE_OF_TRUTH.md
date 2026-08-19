# DATA TO VIDEO — SOURCE OF TRUTH
## Agent #6: Research/Data → Infographic Video
**Document:** `agents/sources_of_truth/data_to_video_SOURCE_OF_TRUTH.md`
**Version:** 1.0
**Last Updated:** 2026-08-19
**Auto-Update:** Daily at 00:00 UTC
**Purpose:** Complete reference for Data to Video agent.

---

# 1. WHAT IS DATA TO VIDEO?

Data to Video takes research data and statistics and creates **animated infographic videos** by:
1. Taking data source + stats list
2. Generating script with stats
3. Creating TTS voiceover
4. Building video with text overlays
5. Merging audio + video

**Output:** Vertical infographic video with voiceover, ready for Instagram Reels.

---

# 2. WORKFLOW

```
DATA SOURCE + STATS
    ↓
┌─────────────────────────────────────────┐
│ 1. INPUT VALIDATION                     │
│    - Data source not empty?             │
│    - Stats: list with ≥ 2 items?        │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 2. RIGHTS GATE                          │
│    - Never invent statistics            │
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
│ 4. GENERATE SCRIPT                      │
│    - Stats-based script                 │
│    - Hook + stat highlights             │
│    - Duration: 30-60 seconds            │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 5. TTS GENERATION                       │
│    - macOS `say` command                │
│    - Rate: 150 wpm                      │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 6. VIDEO CREATION                       │
│    - Text overlays with stats           │
│    - Gradient backgrounds               │
│    - Safe zone enforcement              │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 7. MERGE + QA                           │
│    - Video + audio                      │
│    - Instagram compliance               │
└─────────────────────────────────────────┘
    ↓
OUTPUT: Infographic video with stats
```

---

# 3. QUALITY STANDARDS

## Video Requirements
| Parameter | Requirement |
|-----------|-------------|
| Resolution | 1080 x 1920 px |
| Aspect Ratio | 9:16 (vertical) |
| Duration | 30-60 seconds |
| Stats | Minimum 2 stats |
| Format | MP4 |

---

# 4. BEST PRACTICES

## Before Creation
1. **Verify Data** — Never invent statistics
2. **Source Check** — Use credible sources
3. **Rights Gate** — Check for copyright

## During Creation
1. **Clear Stats** — Large, readable numbers
2. **Visual Appeal** — Gradient backgrounds
3. **Safe Zone** — Text within 10-85%

## After Creation
1. **QA Check** — All standards met
2. **Register Content** — For dedup

---

# 5. COMMON ISSUES

| Issue | Cause | Solution |
|-------|-------|----------|
| Stats unclear | Text too small | Increase font size |
| Too many stats | Overwhelming | Limit to 4-5 |
| Boring visuals | No gradients | Add gradient backgrounds |

---

# 6. PERFORMANCE METRICS

| Metric | Target | Current |
|--------|--------|---------|
| Creation time | < 60s | ~45s |
| QA pass rate | ≥ 95% | ~90% |

---

# 7. EXAMPLE USAGE

```bash
curl -X POST http://localhost:8003/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "data_to_video",
    "data_source": "Video marketing stats",
    "niche": "tech_ai",
    "stats": ["85% of marketers use video", "93% see video as important"]
  }'
```

---

**Last verified:** August 19, 2026
