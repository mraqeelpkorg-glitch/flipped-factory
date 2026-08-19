# COURSE TEASER — SOURCE OF TRUTH
## Agent #10: Course Content → Free Preview Clip
**Document:** `agents/sources_of_truth/course_teaser_SOURCE_OF_TRUTH.md`
**Version:** 1.0
**Last Updated:** 2026-08-19
**Auto-Update:** Daily at 00:00 UTC
**Purpose:** Complete reference for Course Teaser agent.

---

# 1. WHAT IS COURSE TEASER?

Course Teaser takes course content and creates **free preview clips** by:
1. Taking course module text
2. Generating teaser script
3. Creating TTS voiceover
4. Building video with course highlights
5. Merging audio + video

**Output:** Vertical teaser video for course promotion, ready for Instagram Reels.

---

# 2. WORKFLOW

```
COURSE MODULE TEXT
    ↓
┌─────────────────────────────────────────┐
│ 1. INPUT VALIDATION                     │
│    - Module text ≥ 10 chars?            │
│    - Course name provided?              │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 2. RIGHTS GATE                          │
│    - Course material authorized?        │
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
│ 4. GENERATE TEASER SCRIPT               │
│    - AI script generation               │
│    - Hook + preview + CTA               │
│    - Duration: 30-60 seconds            │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 5. TTS + VIDEO                          │
│    - Voiceover generation               │
│    - Video with course highlights       │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 6. MERGE + QA                           │
│    - Video + audio                      │
│    - Instagram compliance               │
└─────────────────────────────────────────┘
    ↓
OUTPUT: Course teaser video
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
| Hook | "Want to learn X?" |
| Preview | Key insight from course |
| CTA | "Link in bio for full course" |

---

# 4. BEST PRACTICES

## Before Creation
1. **Check Rights** — Course must be authorized
2. **Verify Content** — Module has value
3. **Rights Gate** — Check for copyright

## During Creation
1. **Teasing** — Show value, don't give it all
2. **Clear CTA** — Direct to course
3. **Short Duration** — 30-60 seconds

## After Creation
1. **QA Check** — All standards met
2. **Register Content** — For dedup

---

# 5. COMMON ISSUES

| Issue | Cause | Solution |
|-------|-------|----------|
| Too much content | Giving away course | Tease, don't teach |
| Unclear CTA | No direction | Add "Link in bio" |
| Boring hook | Generic | Use viral hook |

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
    "agent": "course_teaser",
    "course_module": "In this module you will learn how to build AI agents that can automate your business workflows using free tools.",
    "course_name": "AI Automation Masterclass",
    "niche": "education"
  }'
```

---

**Last verified:** August 19, 2026
