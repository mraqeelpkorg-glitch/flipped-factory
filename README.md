# Flipped Factory — AI Content Automation Platform

**Zero-budget** AI content factory that creates Instagram Reels across 12 video types using 100% free tools.

## Architecture

```
flipped-factory/
├── main.py                    # Daily pipeline orchestrator
├── config.py                  # All configuration
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
├── engines/                   # Core engines
│   ├── trend_engine.py        # Google Trends (pytrends)
│   ├── niche_selector.py      # 10 niches, 100+ topics, hashtags
│   ├── content_creator.py     # AI script generation (Ollama/Llama 3)
│   ├── video_builder.py       # MoviePy text/slideshow videos
│   ├── caption_generator.py   # SRT + animated captions
│   └── revenue_tracker.py     # SQLite revenue + analytics
├── agents/                    # 12 specialized content agents
│   ├── agent_youtube_clipper.py    # YouTube → Reels
│   ├── agent_podcast_clipper.py    # Podcast → Clips
│   ├── agent_blog_to_video.py      # Blog → Video
│   ├── agent_remix_flip.py         # Re-edit content
│   ├── agent_dub_flip.py           # Multi-language
│   ├── agent_data_to_video.py      # Research → Infographic
│   ├── agent_product_compilation.py # Top 10 products
│   ├── agent_bts_educational.py    # BTS → Tutorial
│   ├── agent_trending_niche.py     # Trending audio + niche
│   ├── agent_course_teaser.py      # Free preview clip
│   ├── agent_live_highlights.py    # Live → Clips
│   └── agent_screenshot_tutorial.py # Screenshots → Video
├── tools/                     # Utility tools
│   ├── downloader.py          # yt-dlp video downloader
│   ├── transcriber.py         # Whisper transcription
│   ├── tts_engine.py          # pyttsx3 text-to-speech
│   └── video_editor.py        # MoviePy + FFmpeg utils
├── platforms/
│   └── instagram_uploader.py  # instagrapi auto-posting
├── dashboard/
│   ├── app.py                 # FastAPI dashboard server
│   └── index.html             # Full dashboard UI
└── data/                      # Runtime data
    ├── videos/                # Generated videos
    ├── scripts/               # AI scripts
    ├── trends.json            # Trend cache
    └── revenue.db             # SQLite database
```

## Features

- **10 Niches**: Health, Finance, Tech, E-Commerce, Education, Motivation, Food, Travel, Beauty, Productivity
- **12 Agents**: One per video type — all fully automated
- **AI Scripts**: Free Ollama + Llama 3 (zero API cost)
- **Full Dashboard**: FastAPI + HTML — manage niches, agents, queue, revenue
- **Auto-Posting**: Instagram via instagrapi with retry logic
- **Revenue Tracking**: SQLite database + analytics
- **Multi-Language**: en/es/hi/ar/pt support

## Quick Start

```bash
# Install
cd ~/Desktop/flipped-factory
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup (Instagram login + Ollama)
python main.py setup

# Run daily pipeline (3 videos)
python main.py run

# Start dashboard
python main.py dash
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `python main.py run` | Daily pipeline — creates 3 videos |
| `python main.py post` | Post a ready video to Instagram |
| `python main.py status` | Show revenue + video stats |
| `python main.py setup` | First-time Instagram login |
| `python main.py dash` | Start dashboard on port 8003 |

## Dependencies

All **free**, no paid APIs:

| Tool | Purpose |
|------|---------|
| MoviePy | Video editing |
| Whisper | Transcription |
| pyttsx3 | Text-to-speech |
| Pillow | Image processing |
| yt-dlp | Video downloading |
| pytrends | Google Trends |
| instagrapi | Instagram API |
| FastAPI | Dashboard server |
| SQLite | Revenue database |
| Ollama | Free AI scripts |

## Revenue Model

- **Product Links**: Amazon affiliate via Linktree
- **Course Sales**: Gumroad digital products
- **Sponsored Posts**: Brand deals
- **Commission**: Sales from product compilations

## Target

- 10+ videos/day
- 100K+ views/month
- $500+/month revenue
- 100% automated pipeline
