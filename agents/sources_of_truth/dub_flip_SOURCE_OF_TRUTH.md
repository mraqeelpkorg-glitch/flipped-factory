# DUB FLIP — SOURCE OF TRUTH
## Agent #5: Multi-Language Video Dubbing
**Document:** `agents/sources_of_truth/dub_flip_SOURCE_OF_TRUTH.md`
**Version:** 1.0
**Last Updated:** 2026-08-19
**Auto-Update:** Daily at 00:00 UTC
**Purpose:** Complete reference for Dub Flip agent — what it does, how it works, quality standards, and best practices.

---

# 1. WHAT IS DUB FLIP?

Dub Flip takes an existing video and creates **multi-language versions** by:
1. Transcribing the original video
2. Translating the script to target languages
3. Generating TTS audio in each language
4. Creating new video with translated script
5. Merging audio with video

**Output:** Multiple language versions of the same video, each ready for Instagram Reels.

---

# 2. SUPPORTED LANGUAGES

## Primary Languages (Tier 1 — Full Support)
| Code | Language | Voice | Quality |
|------|----------|-------|---------|
| `en` | English | Daniel (macOS) | ✅ Excellent |
| `es` | Spanish | Monica (macOS) | ✅ Excellent |
| `hi` | Hindi | Veena (macOS) | ✅ Good |
| `pt` | Portuguese | Joana (macOS) | ✅ Good |
| `fr` | French | Thomas (macOS) | ✅ Good |
| `de` | German | Anna (macOS) | ✅ Good |

## Secondary Languages (Tier 2 — Basic Support)
| Code | Language | Voice | Quality |
|------|----------|-------|---------|
| `ja` | Japanese | Kyoko (macOS) | ⚠️ Fair |
| `ko` | Korean | Yuna (macOS) | ⚠️ Fair |
| `zh` | Chinese | Ting-Ting (macOS) | ⚠️ Fair |
| `ar` | Arabic | Maged (macOS) | ⚠️ Fair |
| `ru` | Russian | Milena (macOS) | ⚠️ Fair |

## Language Selection Rules
1. **Default:** `["en", "es", "hi", "pt"]` — covers 80% of global audience
2. **Niche-specific:** Health/Finance → add `fr`, `de`; Tech → add `ja`, `ko`
3. **Max 6 languages** per run to avoid timeout
4. **Always include English** as source language

---

# 3. WORKFLOW

## Step-by-Step Process

```
INPUT VIDEO
    ↓
┌─────────────────────────────────────────┐
│ 1. INPUT VALIDATION                     │
│    - File exists?                       │
│    - Valid format? (MP4/MOV)            │
│    - Duration > 5 seconds?              │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 2. RIGHTS GATE                          │
│    - Check copyright risk               │
│    - Block if HIGH risk                 │
│    - Allow if LOW/MEDIUM risk           │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 3. TRANSCRIPTION                        │
│    - FFmpeg silence detection           │
│    - Extract audio                      │
│    - Generate transcript                │
│    - Extract segments                   │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 4. SAFETY CHECK (Source)                │
│    - Check transcript for violations    │
│    - Block if HIGH risk                 │
│    - Allow if LOW/MEDIUM risk           │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 5. FOR EACH LANGUAGE:                   │
│    ┌─────────────────────────────────┐  │
│    │ a. TRANSLATE                    │  │
│    │    - Hook, body, CTA            │  │
│    │    - Localize for culture       │  │
│    └─────────────────────────────────┘  │
│    ↓                                    │
│    ┌─────────────────────────────────┐  │
│    │ b. TTS GENERATION              │  │
│    │    - macOS `say` command        │  │
│    │    - Rate: 150 wpm              │  │
│    │    - Output: WAV format         │  │
│    └─────────────────────────────────┘  │
│    ↓                                    │
│    ┌─────────────────────────────────┐  │
│    │ c. VIDEO CREATION              │  │
│    │    - Pillow frame generation    │  │
│    │    - Safe zone enforcement      │  │
│    │    - Instagram specs (1080x1920)│  │
│    └─────────────────────────────────┘  │
│    ↓                                    │
│    ┌─────────────────────────────────┐  │
│    │ d. AUDIO MERGE                 │  │
│    │    - FFmpeg merge               │  │
│    │    - Volume: 0.8                │  │
│    │    - Codec: H.264 + AAC        │  │
│    └─────────────────────────────────┘  │
│    ↓                                    │
│    ┌─────────────────────────────────┐  │
│    │ e. SAFETY CHECK (Dubbed)       │  │
│    │    - Check translated text      │  │
│    │    - Block if violations        │  │
│    └─────────────────────────────────┘  │
│    ↓                                    │
│    ┌─────────────────────────────────┐  │
│    │ f. DEDUP CHECK                 │  │
│    │    - Check for duplicates       │  │
│    │    - Register content           │  │
│    └─────────────────────────────────┘  │
│    ↓                                    │
│    ┌─────────────────────────────────┐  │
│    │ g. QA CHECK                    │  │
│    │    - Resolution: 1080x1920      │  │
│    │    - Duration: 15-60 seconds    │  │
│    │    - Audio present              │  │
│    │    - Instagram compliance       │  │
│    └─────────────────────────────────┘  │
│    ↓                                    │
│    ┌─────────────────────────────────┐  │
│    │ h. ANALYTICS LOG               │  │
│    │    - Log video to database      │  │
│    │    - Track performance          │  │
│    └─────────────────────────────────┘  │
└─────────────────────────────────────────┘
    ↓
OUTPUT: Multiple language versions
```

---

# 4. QUALITY STANDARDS

## Video Requirements (Instagram Reels)
| Parameter | Requirement |
|-----------|-------------|
| Resolution | 1080 x 1920 px |
| Aspect Ratio | 9:16 (vertical) |
| Frame Rate | 30 FPS |
| Duration | 15-60 seconds |
| Codec | H.264 + AAC |
| Bitrate | ≥ 3500 kbps |
| File Size | < 100 MB |

## Audio Requirements
| Parameter | Requirement |
|-----------|-------------|
| Sample Rate | ≥ 44.1 kHz |
| Bitrate | ≥ 128 kbps |
| Format | WAV (intermediate), AAC (final) |
| Volume | 0.8 (merged) |
| Rate | 150 wpm (TTS) |

## Translation Requirements
| Requirement | Details |
|-------------|---------|
| Accuracy | ≥ 90% meaning preservation |
| Naturalness | Native-sounding phrasing |
| Cultural Fit | Localized idioms, not literal |
| Claims | Statistics/dates verified |
| Brand Terms | Kept in original language |

---

# 5. BEST PRACTICES

## Before Dubbing
1. **Clean Audio** — Source video must have clear speech
2. **Simple Language** — Avoid idioms that don't translate
3. **Measured Pace** — Slower speech = better sync
4. **Natural Pauses** — Give AI room to sync timing
5. **No Overlapping** — Only one speaker at a time

## During Translation
1. **Localize, Don't Literal** — Adapt for culture
2. **Keep Brand Names** — Don't translate proper nouns
3. **Verify Numbers** — Check statistics, dates, prices
4. **Check Units** — Don't convert°F/°C or miles/km unexpectedly
5. **Review Idioms** — "Ball game" → local equivalent

## After Dubbing
1. **Watch Full Video** — Check opening 30 seconds especially
2. **Check Close-ups** — Lip sync most visible here
3. **Verify Claims** — Statistics in translated narration
4. **Check Audio Quality** — No clipping or cutoffs
5. **Native Speaker Review** — When possible

---

# 6. COMMON ISSUES & SOLUTIONS

| Issue | Cause | Solution |
|-------|-------|----------|
| **Poor lip sync** | Fast speech in source | Slow down TTS rate |
| **Unnatural phrasing** | Literal translation | Use localized idioms |
| **Audio clipping** | Volume too high | Reduce to 0.7 |
| **Missing words** | Transcript errors | Manual review |
| **Wrong units** | Auto-conversion | Disable unit conversion |
| **Cultural mismatch** | Idiom not adapted | Localize for region |
| **Timeout error** | Too many languages | Limit to 4 languages |
| **Safety block** | Translation violation | Review and adjust |

---

# 7. LANGUAGE-SPECIFIC NOTES

## Spanish (es)
- **Variant:** Latin American (not Castilian)
- **Pronunciation:** Clear, measured
- **Common Issues:** Formal/informal register

## Hindi (hi)
- **Script:** Devanagari
- **Pronunciation:** Clear consonants
- **Common Issues:** Code-mixing with English

## Portuguese (pt)
- **Variant:** Brazilian (not European)
- **Pronunciation:** Open vowels
- **Common Issues:** Nasal sounds

## French (fr)
- **Variant:** Metropolitan
- **Pronunciation:** Nasal vowels
- **Common Issues:** Liaisons, elision

## German (de)
- **Pronunciation:** Compound words
- **Common Issues:** Gendered nouns

---

# 8. PERFORMANCE METRICS

## Target Metrics
| Metric | Target | Current |
|--------|--------|---------|
| Languages per run | 4 | 4 |
| Time per language | < 60s | ~45s |
| Translation accuracy | ≥ 90% | ~85% |
| Audio quality | ≥ 4/5 | ~3.5/5 |
| QA pass rate | ≥ 95% | ~90% |
| Safety pass rate | 100% | 100% |

## Tracking
- Database: `data/revenue.db`
- Table: `videos`
- Fields: `language`, `agent_type`, `qa_status`

---

# 9. DAILY AUTO-UPDATE

This document auto-updates daily at 00:00 UTC with:
- New language support
- Updated best practices
- Performance metrics
- Common issues discovered
- Quality improvements

**Update Script:** `agents/sources_of_truth/update_dub_flip.py`
**Trigger:** Cron job or manual run

---

# 10. EXAMPLE USAGE

## API Call
```bash
curl -X POST http://localhost:8003/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "dub_flip",
    "video_path": "data/videos/processed/example.mp4",
    "niche": "health_fitness",
    "languages": ["en", "es", "hi", "pt"]
  }'
```

## CLI Call
```bash
python main.py agent dub_flip \
  video_path="data/videos/processed/example.mp4" \
  niche="health_fitness" \
  languages="en,es,hi,pt"
```

## Expected Output
```json
{
  "success": true,
  "versions_created": 4,
  "results": [
    {"language": "en", "video_path": "dub_final_en_120000.mp4", "safety_status": "APPROVED", "qa_status": "PASSED"},
    {"language": "es", "video_path": "dub_final_es_120000.mp4", "safety_status": "APPROVED", "qa_status": "PASSED"},
    {"language": "hi", "video_path": "dub_final_hi_120000.mp4", "safety_status": "APPROVED", "qa_status": "PASSED"},
    {"language": "pt", "video_path": "dub_final_pt_120000.mp4", "safety_status": "APPROVED", "qa_status": "PASSED"}
  ],
  "errors": [],
  "source_safety": "APPROVED"
}
```

---

# 11. INTEGRATION POINTS

## Connected Engines
- `engines/content_creator.py` — Translation
- `engines/video_builder.py` — Video creation
- `engines/safety_gate.py` — Safety check
- `engines/dedup_engine.py` — Duplicate detection
- `engines/shared_qa.py` — Quality assurance
- `engines/revenue_tracker.py` — Analytics

## Connected Tools
- `tools/tts_engine.py` — Text-to-speech
- `tools/video_editor.py` — FFmpeg operations
- `tools/transcriber.py` — Audio transcription

## Connected Agents
- `agents/agent_youtube_clipper.py` — Can feed into Dub Flip
- `agents/agent_podcast_clipper.py` — Can feed into Dub Flip
- `agents/agent_blog_to_video.py` — Can feed into Dub Flip

---

# 12. FUTURE IMPROVEMENTS

## Planned
- [ ] Add more Tier 1 languages (ja, ko, zh)
- [ ] Implement voice cloning for consistency
- [ ] Add lip sync adjustment
- [ ] Implement batch processing
- [ ] Add native speaker review queue

## Research Needed
- [ ] AI dubbing tools comparison (HeyGen, ElevenLabs, DubSmart)
- [ ] Lip sync technology evaluation
- [ ] Voice cloning quality assessment

---

**This document is the permanent source of truth for Dub Flip agent.**

When in doubt, refer to this document.

**Last verified:** August 19, 2026
**Sources:** Dubly.ai, DubSmart.ai, FluxNote.io, Meta AI, Instagram Best Practices
