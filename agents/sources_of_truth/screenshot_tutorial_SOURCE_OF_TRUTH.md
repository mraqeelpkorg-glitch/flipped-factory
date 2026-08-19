# SCREENSHOT TUTORIAL — SOURCE OF TRUTH
## Agent #12: Screenshots → Video Tutorial
**Document:** `agents/sources_of_truth/screenshot_tutorial_SOURCE_OF_TRUTH.md`
**Version:** 1.0
**Last Updated:** 2026-08-19
**Auto-Update:** Daily at 00:00 UTC
**Purpose:** Complete reference for Screenshot Tutorial agent.

---

# 1. WHAT IS SCREENSHOT TUTORIAL?

Screenshot Tutorial takes screenshots and creates **video tutorials** by:
1. Taking screenshots directory
2. Scanning for privacy issues (passwords, API keys)
3. Creating slideshow video
4. Adding TTS voiceover
5. Merging audio + video

**Output:** Vertical tutorial video from screenshots, ready for Instagram Reels.

---

# 2. WORKFLOW

```
SCREENSHOTS DIRECTORY
    ↓
┌─────────────────────────────────────────┐
│ 1. INPUT VALIDATION                     │
│    - Directory exists?                  │
│    - Has screenshots (PNG/JPG)?         │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 2. PRIVACY SCAN                         │
│    - Scan for passwords                 │
│    - Scan for API keys                  │
│    - Scan for tokens                    │
│    - Block if found                     │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 3. RIGHTS GATE                          │
│    - Screenshots authorized?            │
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
│    - Tutorial steps                     │
│    - Duration based on screenshots      │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 6. TTS + SLIDESHOW                      │
│    - Voiceover generation               │
│    - Slideshow from screenshots         │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 7. MERGE + QA                           │
│    - Video + audio                      │
│    - Instagram compliance               │
└─────────────────────────────────────────┘
    ↓
OUTPUT: Tutorial video from screenshots
```

---

# 3. PRIVACY SCAN

**Always scan for:**
- Passwords (`password`, `pwd`, `passwd`)
- API keys (`api_key`, `apikey`, `api-key`)
- Tokens (`token`, `access_token`, `bearer`)
- Secrets (`secret`, `private_key`)
- Credit cards (regex pattern)

**If found:** BLOCK the video, never publish sensitive data.

---

# 4. BEST PRACTICES

## Before Creation
1. **Privacy Scan** — Always scan first
2. **Check Rights** — Screenshots authorized
3. **Verify Quality** — Clear screenshots

## During Creation
1. **Clean Screenshots** — Remove sensitive data
2. **Clear Steps** — Numbered tutorial
3. **Natural TTS** — Appropriate rate

## After Creation
1. **QA Check** — All standards met
2. **Register Content** — For dedup

---

# 5. COMMON ISSUES

| Issue | Cause | Solution |
|-------|-------|----------|
| Privacy violation | API key in screenshot | Blur or remove |
| Too many slides | Overwhelming | Limit to 5-10 |
| Poor quality | Blurry screenshots | Use better resolution |

---

# 6. PERFORMANCE METRICS

| Metric | Target | Current |
|--------|--------|---------|
| Creation time | < 60s | ~45s |
| Privacy scan | 100% | 100% |
| QA pass rate | ≥ 95% | ~90% |

---

# 7. EXAMPLE USAGE

```bash
curl -X POST http://localhost:8003/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "screenshot_tutorial",
    "screenshots_dir": "data/screenshots/vscode_setup",
    "niche": "tech_ai",
    "tutorial_title": "How to set up VS Code for Python"
  }'
```

---

**Last verified:** August 19, 2026
