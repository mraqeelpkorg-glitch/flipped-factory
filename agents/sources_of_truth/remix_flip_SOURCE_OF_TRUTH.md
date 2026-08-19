# REMIX FLIP — SOURCE OF TRUTH
## Agent #4: Re-edit Existing Video with Fresh Hook
**Document:** `agents/sources_of_truth/remix_flip_SOURCE_OF_TRUTH.md`
**Version:** 1.0
**Last Updated:** 2026-08-19
**Auto-Update:** Daily at 00:00 UTC
**Purpose:** Complete reference for Remix Flip agent.

---

# 1. WHAT IS REMIX FLIP?

Remix Flip takes an existing video and creates a **fresh version** by:
1. Adding a new hook/intro at the beginning
2. Combining hook with original video
3. Creating a renewed, engaging piece

**Output:** Remixed video with new hook, ready for Instagram Reels.

---

# 2. WORKFLOW

```
EXISTING VIDEO
    ↓
┌─────────────────────────────────────────┐
│ 1. INPUT VALIDATION                     │
│    - File exists?                       │
│    - Valid format?                      │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 2. RIGHTS GATE                          │
│    - Check copyright risk               │
│    - Block if HIGH risk                 │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 3. SAFETY GATE                          │
│    - Check hook text                    │
│    - Block if violations                │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 4. GENERATE NEW HOOK                    │
│    - AI-generated hook                  │
│    - Or use provided hook               │
│    - Duration: 3-5 seconds              │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 5. CREATE HOOK VIDEO                    │
│    - Text overlay                       │
│    - Gradient background                │
│    - Safe zone enforcement              │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 6. COMBINE                              │
│    - Concat hook + original             │
│    - Smooth transition                  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 7. DEDUP CHECK                          │
│    - Check for duplicates               │
│    - Register content                   │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 8. QA CHECK                             │
│    - Resolution: 1080x1920              │
│    - Duration: 15-60 seconds            │
│    - Audio present                      │
│    - Instagram compliance               │
└─────────────────────────────────────────┘
    ↓
OUTPUT: Remixed video with new hook
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

## Hook Requirements
| Element | Requirement |
|---------|-------------|
| Duration | 3-5 seconds |
| Text | 5-15 words |
| Style | Attention-grabbing |
| Placement | Safe zone (10-85%) |

---

# 4. BEST PRACTICES

## Before Remixing
1. **Check Rights** — Must own or have permission
2. **Check Safety** — No violations in hook
3. **Choose Good Source** — High quality video

## During Remixing
1. **Create Engaging Hook** — Grab attention fast
2. **Smooth Transition** — No jarring cuts
3. **Maintain Quality** — Don't degrade video

## After Remixing
1. **QA Check** — All standards met
2. **Safety Check** — No violations
3. **Register Content** — For dedup

---

# 5. COMMON ISSUES

| Issue | Cause | Solution |
|-------|-------|----------|
| Jarring transition | Bad concatenation | Smooth fade |
| Hook too long | Text too much | Shorten to 5 words |
| Quality drop | Re-encoding | Use same codec |
| Safety block | Hook violation | Rewrite hook |

---

# 6. PERFORMANCE METRICS

| Metric | Target | Current |
|--------|--------|---------|
| Remix time | < 30s | ~20s |
| Hook quality | ≥ 4/5 | ~3.5/5 |
| QA pass rate | ≥ 95% | ~90% |

---

# 7. EXAMPLE USAGE

```bash
curl -X POST http://localhost:8003/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "remix_flip",
    "video_path": "data/videos/processed/existing.mp4",
    "niche": "motivation",
    "new_hook": "You need to see this!"
  }'
```

---

**This document is the permanent source of truth for Remix Flip agent.**

**Last verified:** August 19, 2026
