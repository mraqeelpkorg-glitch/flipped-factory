# INSTAGRAM SOURCE OF TRUTH
## Flipped Factory — Video Making, Quality & Trends Standard
**Document:** `INSTAGRAM_SOURCE_OF_TRUTH.md`
**Version:** 1.0
**Last Updated:** 2026-08-19
**Purpose:** Permanent reference for all video creation, quality, and trend decisions.

---

# 1. VIDEO SPECIFICATIONS (Instagram Reels 2026)

## Technical Requirements

| Parameter | Requirement | Our Target |
|-----------|-------------|------------|
| **Resolution** | 1080 x 1920 px | ✅ 1080 x 1920 |
| **Aspect Ratio** | 9:16 (vertical) | ✅ 9:16 |
| **Frame Rate** | 24-60 FPS (30 recommended) | ✅ 30 FPS |
| **Duration** | 3 seconds — 90 seconds | ✅ 15-60 seconds |
| **File Format** | MP4 or MOV | ✅ MP4 |
| **Video Codec** | H.264 | ✅ H.264 |
| **Audio Codec** | AAC | ✅ AAC |
| **Max File Size** | 4 GB | ✅ < 100 MB |
| **Bitrate** | ≥ 3,500 kbps | ✅ 5,000 kbps |
| **Audio Sample Rate** | ≥ 44.1 kHz | ✅ 44.1 kHz |
| **Audio Bitrate** | ≥ 128 kbps | ✅ 128 kbps |

## Duration Sweet Spots (2026 Data)

| Duration | Best For | Our Use |
|----------|----------|---------|
| **7-15 seconds** | High-velocity entertainment, hooks | Quick tips, facts |
| **15-30 seconds** | Optimal for virality, high completion | Main content |
| **30-60 seconds** | Educational, storytelling | Tutorials, deep content |
| **60-90 seconds** | Longer tutorials, interviews | Avoid (lower completion) |
| **30-40 seconds** | ⚠️ DEAD ZONE — avoid | AVOID |

**Our Standard:** Target 15-30 seconds for maximum virality.

---

# 2. SAFE ZONES (Critical for Text/CTA)

Instagram overlays UI elements on your video. Text outside safe zones gets hidden.

```
┌─────────────────────────┐
│░░░░ TOP SAFE ZONE ░░░░░░│ ← Top 10% (profile, username)
│                         │
│   ┌─────────────────┐   │
│   │                 │   │
│   │   SAFE CENTER   │   │ ← Text/CTA goes here
│   │   (Main Content)│   │
│   │                 │   │
│   └─────────────────┘   │
│                         │
│░░░ BOTTOM SAFE ZONE ░░░░│ ← Bottom 15% (captions, buttons)
│░░░ (25% total) ░░░░░░░░│
└─────────────────────────┘
```

| Zone | Percentage | What Goes There |
|------|------------|-----------------|
| **Top** | 0-10% | AVOID — username, profile pic |
| **Safe Center** | 10-75% | ✅ Main content, text, hooks, CTAs |
| **Bottom** | 75-100% | AVOID — captions, like/comment/share buttons |

**Our Standard:** All text must be in 10-75% vertical zone.

---

# 3. ALGORITHM SIGNALS (How Instagram Ranks Reels)

## Primary Signals (Most Important)

| Signal | Weight | What It Means |
|--------|--------|---------------|
| **Completion Rate** | 🔴 HIGHEST | % of viewers who watch until end |
| **Rewatch Rate** | 🔴 HIGH | % who watch again |
| **Watch Time** | 🔴 HIGH | Total seconds watched |
| **Share Rate** | 🟠 HIGH | % who send to friends |
| **Save Rate** | 🟠 HIGH | % who bookmark |
| **Comment Rate** | 🟡 MEDIUM | % who comment |
| **Like Rate** | 🟡 MEDIUM | % who like |
| **Follow Rate** | 🟢 LOW-MED | % who follow after watching |

## 2026 Algorithm Facts

1. **Instagram is now a Discovery Engine** — it prioritizes what you WATCH over who you FOLLOW
2. **Reels get 36% more reach** than carousels (Buffer 2026 study)
3. **3% Share Rate** = 90% chance of hitting 100K views
4. **Reels up to 3 minutes** are now eligible for non-follower recommendation
5. **Audio tracks matter** — trending sounds boost distribution
6. **Initial follower momentum** — posting to main feed helps early engagement

---

# 4. VIRAL CONTENT PATTERNS (What Actually Works)

## Top Performing Formats (2026)

| Format | Why It Works | Our Agent |
|--------|-------------|-----------|
| **Story/Drama** | Curiosity loops, rewatch | YouTube Clipper, Podcast Clipper |
| **Educational** | Saves, shares | Blog to Video, Data to Video |
| **Transformation** | Before/after, retention | Remix Flip |
| **Trend-Based** | Already proven format | Trending Audio |
| **ASMR/Calming** | High completion, saves | Remix Flip (ASMR style) |
| **List/Countdown** | Clear structure, shares | Data to Video |
| **Mistake/Myth** | Curiosity, comments | Blog to Video |
| **Behind-the-Scenes** | Authenticity, follows | BTS Educational |

## Hook Families (What Gets Clicks)

| Family | Example | Best For |
|--------|---------|----------|
| **Curiosity** | "Most people don't know this..." | All niches |
| **Mistake** | "You're doing this wrong..." | Education, Health |
| **Contradiction** | "Everyone says X. Here's why..." | Finance, Tech |
| **Story** | "This started with one mistake..." | Motivation |
| **Before/After** | "Before you do X, see this..." | Fitness, Beauty |
| **Question** | "Would you do this if...?" | All niches |
| **Specific Value** | "3 things you need to know..." | All niches |
| **Shock** | "This changes everything..." | Tech, News |

---

# 5. QUALITY STANDARDS (What We Enforce)

## Pre-Publish Checklist (Every Video)

| Check | Standard | Gate |
|-------|----------|------|
| **Resolution** | 1080x1920 | ✅ shared_qa.py |
| **Aspect Ratio** | 9:16 | ✅ shared_qa.py |
| **Codec** | H.264 + AAC | ✅ shared_qa.py |
| **Duration** | 15-60 seconds | ✅ shared_qa.py |
| **File Size** | < 100 MB | ✅ shared_qa.py |
| **Audio** | Present, clear | ✅ shared_qa.py |
| **Black Bars** | None | ✅ shared_qa.py |
| **Corrupted Frames** | None | ✅ shared_qa.py |
| **Safety** | No hate/violence/etc | ✅ safety_gate.py |
| **Impersonation** | Not faking identity | ✅ enhanced_safety.py |
| **Misleading** | No false claims | ✅ enhanced_safety.py |
| **Private Info** | No passwords/emails | ✅ enhanced_safety.py |
| **Dangerous** | No harmful challenges | ✅ enhanced_safety.py |
| **Copyright** | Authorized content | ✅ content_checker.py |
| **Duplicate** | Not already published | ✅ dedup_engine.py |

## Audio Quality Standards

| Parameter | Requirement |
|-----------|-------------|
| **Sample Rate** | ≥ 44.1 kHz |
| **Bitrate** | ≥ 128 kbps |
| **Peak Volume** | -3 dB to -6 dB |
| **Background Noise** | Minimal |
| **Voice Clarity** | Clear, understandable |
| **Music Balance** | Voice > Music |

---

# 6. POSTING STRATEGY

## Best Times to Post (2026 Data)

| Day | Best Times (Local) |
|-----|-------------------|
| **Monday** | 6 AM, 12 PM, 7 PM |
| **Tuesday** | 7 AM, 1 PM, 8 PM |
| **Wednesday** | 7 AM, 1 PM, 8 PM |
| **Thursday** | 6 AM, 12 PM, 7 PM |
| **Friday** | 7 AM, 1 PM, 8 PM |
| **Saturday** | 9 AM, 2 PM, 9 PM |
| **Sunday** | 9 AM, 2 PM, 9 PM |

**Our Timezone:** Asia/Karachi (UTC+5)

## Posting Frequency

| Strategy | Frequency | Purpose |
|----------|-----------|---------|
| **Minimum** | 1 Reel/day | Maintain presence |
| **Optimal** | 2-3 Reels/day | Growth |
| **Maximum** | 4-5 Reels/day | Saturation |
| **Quality > Quantity** | Always | Never sacrifice quality |

---

# 7. CAPTION & HASHTAG STRATEGY

## Caption Best Practices

| Element | Recommendation |
|---------|----------------|
| **Length** | 150-300 characters optimal |
| **First Line** | Hook — must grab attention |
| **Keywords** | Include in first line (SEO) |
| **CTA** | Ask question or tell action |
| **Emojis** | 2-3 relevant emojis |
| **Line Breaks** | Use for readability |

## Hashtag Strategy (2026)

| Rule | Detail |
|------|--------|
| **Count** | 3-5 hashtags (NOT 30) |
| **Relevance** | Must match content exactly |
| **Mix** | 1 broad + 2-3 niche + 1 branded |
| **Placement** | In caption, not comments |
| **Avoid** | Banned hashtags, irrelevant tags |

---

# 8. TRENDING CONTENT TYPES (August 2026)

## Currently Viral Formats

1. **AI-Generated Content** — AI visuals, storytelling, voiceovers
2. **"This is how I..." Stories** — Personal narrative hooks
3. **Trend-Based/Meme Reels** — Using trending sounds with niche twist
4. **Transformation** — Before/after, glow-ups, makeovers
5. **Educational Lists** — "3 things you need to know..."
6. **ASMR/Calming** — Relaxing visuals, soft audio
7. **Controversial Takes** — Opinion-led content
8. **Day in the Life** — Authentic, relatable content
9. **Quick Tutorials** — 15-30 second how-tos
10. **Data/Stats** — Infographic-style reels

## Trending Niches (2026)

| Niche | Growth | Our Coverage |
|-------|--------|--------------|
| **AI/Tech** | 🔥🔥🔥 | ✅ Tech & AI |
| **Personal Finance** | 🔥🔥🔥 | ✅ Finance & Crypto |
| **Health/Wellness** | 🔥🔥 | ✅ Health & Fitness |
| **Productivity** | 🔥🔥 | ✅ Productivity |
| **Education** | 🔥🔥 | ✅ Education |
| **Motivation** | 🔥 | ✅ Motivation |
| **Food/Recipes** | 🔥 | ✅ Food & Nutrition |
| **Travel** | 🔥 | ✅ Travel |
| **Beauty/Skincare** | 🔥 | ✅ Beauty & Skincare |
| **E-Commerce** | 🔥 | ✅ E-Commerce |

---

# 9. INSTAGRAM COMMUNITY GUIDELINES (What Gets Banned)

## Zero Tolerance (Immediate Ban)

- Hate speech or discrimination
- Violence or graphic content
- Sexual content or nudity
- Harassment or bullying
- Spam or fake engagement
- Illegal activities
- Scams or fraud
- Dangerous challenges

## Warning Zone (May Reduce Reach)

- Misleading claims
- Clickbait hooks
- Impersonation
- Private information exposure
- Unverified health/financial claims
- Excessive hashtags
- Low-quality content

## Our Protection

| Threat | Protection | Engine |
|--------|-----------|--------|
| Hate speech | Safety Gate (11 categories) | safety_gate.py |
| Violence | Safety Gate | safety_gate.py |
| Sexual content | Safety Gate | safety_gate.py |
| Impersonation | Enhanced Safety | enhanced_safety.py |
| Misleading hooks | Hook Verification | enhanced_safety.py |
| Private info | Privacy Detection | enhanced_safety.py |
| Dangerous challenges | Challenge Detection | enhanced_safety.py |
| Copyright | Rights Gate | content_checker.py |
| Spam/Duplicates | Dedup Engine | dedup_engine.py |

---

# 10. PERFORMANCE BENCHMARKS

## What "Good" Looks Like (2026)

| Metric | Poor | Average | Good | Viral |
|--------|------|---------|------|-------|
| **Completion Rate** | <30% | 30-50% | 50-70% | >70% |
| **Share Rate** | <0.5% | 0.5-1% | 1-3% | >3% |
| **Save Rate** | <1% | 1-3% | 3-5% | >5% |
| **Comment Rate** | <0.5% | 0.5-1% | 1-2% | >2% |
| **Like Rate** | <3% | 3-5% | 5-10% | >10% |

## Viral Threshold

- **Small Account (<10K):** 20K views in 2 days = viral
- **Medium Account (10K-100K):** 100K views in 2 days = viral
- **Large Account (100K+):** 1M views in 2 days = viral

---

# 11. OUR PRODUCTION STANDARDS

## Every Video Must Have

1. ✅ Strong hook in first 1-3 seconds
2. ✅ Vertical 9:16 format (1080x1920)
3. ✅ Clear audio (no background noise)
4. ✅ Text in safe zone (10-75%)
5. ✅ Value delivered (educate/entertain/inspire)
6. ✅ Clear CTA (follow/share/save/comment)
7. ✅ Safety check passed
8. ✅ Rights check passed
9. ✅ QA check passed
10. ✅ No duplicates

## Our Content Mix

| Type | Percentage | Purpose |
|------|------------|---------|
| **Educational** | 30% | Saves, shares |
| **Entertainment** | 25% | Watch time, completion |
| **Motivation** | 20% | Shares, follows |
| **Trend-Based** | 15% | Reach, discovery |
| **ASMR/Calming** | 10% | Saves, completion |

---

# 12. QUICK REFERENCE CARD

```
INSTAGRAM REELS — QUICK REFERENCE
═══════════════════════════════════

FORMAT:     1080 x 1920 px (9:16)
CODEC:      H.264 + AAC
DURATION:   15-30 seconds (optimal)
FPS:        30
BITRATE:    ≥ 3,500 kbps
SIZE:       < 4 GB

SAFE ZONE:  Text in 10-75% vertical
HOOK:       First 1-3 seconds
COMPLETION: Target >50%
SHARES:     Target >1%

AVOID:
• 30-40 second dead zone
• Text outside safe zones
• Horizontal video
• Low bitrate (<2000 kbps)
• Missing audio
• Black bars
• Copyrighted music

POST:
• 2-3 times daily
• Best times: 12 PM, 7 PM
• Use 3-5 hashtags
• Reply to comments fast
• Post to main feed first
```

---

**This document is the permanent source of truth for all Instagram video decisions.**

When in doubt, refer to this document.

**Last verified:** August 19, 2026
**Sources:** Instagram Help Center, Buffer 2026, Socialinsider 2026, Later.com, Hootsuite
