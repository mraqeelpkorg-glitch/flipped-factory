# TRENDING AUDIO — SOURCE OF TRUTH
## Agent #9: Trending Sound + Niche = Viral Content
**Document:** `agents/sources_of_truth/trending_audio_SOURCE_OF_TRUTH.md`
**Version:** 1.0
**Last Updated:** 2026-08-19
**Auto-Update:** Daily at 00:00 UTC
**Purpose:** Complete reference for Trending Audio agent.

---

# 1. WHAT IS TRENDING AUDIO?

Trending Audio takes trending TikTok/Reels sounds and creates **niche-specific content** by:
1. Taking trending audio (or using default)
2. Selecting topic from niche
3. Generating script
4. Creating TTS voiceover
5. Building video with niche content
6. Merging audio + video

**Output:** Vertical video with trending audio, ready for Instagram Reels.

---

# 2. WORKFLOW

```
NICHE + TRENDING AUDIO
    ↓
┌─────────────────────────────────────────┐
│ 1. INPUT VALIDATION                     │
│    - Audio exists (or use default)      │
│    - Niche selected                     │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 2. RIGHTS GATE                          │
│    - Audio licensed/platform-supported? │
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
│ 4. SELECT TOPIC                         │
│    - Niche-based topic selection        │
│    - Trending content match             │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 5. GENERATE SCRIPT                      │
│    - AI script generation               │
│    - Hook + body + CTA                  │
│    - Duration: 15-30 seconds            │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 6. TTS + VIDEO                          │
│    - Voiceover generation               │
│    - Video creation                     │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 7. MERGE + QA                           │
│    - Video + audio                      │
│    - Instagram compliance               │
└─────────────────────────────────────────┘
    ↓
OUTPUT: Niche video with trending audio
```

---

# 3. TRENDING AUDIO SOURCES

| Source | Method |
|--------|--------|
| TikTok | Platform API (future) |
| Instagram Reels | Hashtag research |
| Default | Built-in audio library |

**Current:** Default audio library (TTS-based)
**Future:** Platform API integration

---

# 4. BEST PRACTICES

## Before Creation
1. **Check Audio Rights** — Must be licensed
2. **Verify Niche Match** — Audio fits niche
3. **Rights Gate** — Check for copyright

## During Creation
1. **Trending Hooks** — Use viral patterns
2. **Niche Relevance** — Content matches audio
3. **Short Duration** — 15-30 seconds optimal

## After Creation
1. **QA Check** — All standards met
2. **Register Content** — For dedup

---

# 5. COMMON ISSUES

| Issue | Cause | Solution |
|-------|-------|----------|
| Audio not trending | Outdated | Research current trends |
| Rights violation | Unlicensed audio | Use platform-supported |
| Niche mismatch | Bad topic selection | Improve topic selection |

---

# 6. PERFORMANCE METRICS

| Metric | Target | Current |
|--------|--------|---------|
| Creation time | < 45s | ~35s |
| QA pass rate | ≥ 95% | ~90% |

---

# 7. EXAMPLE USAGE

```bash
curl -X POST http://localhost:8003/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "trending_niche",
    "niche": "health_fitness",
    "hook": "You need to try this morning routine!"
  }'
```

---

**Last verified:** August 19, 2026
