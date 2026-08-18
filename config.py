"""
Flipped Factory — Configuration
All settings in one place. $0 budget — everything free/local.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
VIDEOS_DIR = DATA_DIR / "videos"
RAW_DIR = VIDEOS_DIR / "raw"
PROCESSED_DIR = VIDEOS_DIR / "processed"
PUBLISHED_DIR = VIDEOS_DIR / "published"
SCRIPTS_DIR = DATA_DIR / "scripts"
LOGS_DIR = BASE_DIR / "logs"

# Ensure dirs exist
for d in [DATA_DIR, VIDEOS_DIR, RAW_DIR, PROCESSED_DIR, PUBLISHED_DIR, SCRIPTS_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─── Load .env ────────────────────────────────────────────────────────────────
load_dotenv(BASE_DIR / ".env")

# ─── AI Script Generation (FREE — OpenCode models via Ollama) ────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")  # Free local model
# Alternative: use OpenCode's free models via API
OPENCODE_API_URL = os.getenv("OPENCODE_API_URL", "")
OPENCODE_API_KEY = os.getenv("OPENCODE_API_KEY", "")

# ─── TTS Settings ─────────────────────────────────────────────────────────────
TTS_RATE = int(os.getenv("TTS_RATE", "150"))       # Words per minute
TTS_VOLUME = float(os.getenv("TTS_VOLUME", "0.9"))  # 0.0 to 1.0
TTS_VOICE_INDEX = int(os.getenv("TTS_VOICE_INDEX", "0"))  # Voice selection

# Multi-language TTS voices
TTS_LANGUAGES = {
    "en": {"rate": 150, "voice_index": 0},   # English
    "es": {"rate": 150, "voice_index": 1},   # Spanish
    "hi": {"rate": 140, "voice_index": 0},   # Hindi (uses English voice fallback)
    "ar": {"rate": 130, "voice_index": 0},   # Arabic (uses English voice fallback)
    "pt": {"rate": 145, "voice_index": 1},   # Portuguese
}

# ─── Instagram Settings ───────────────────────────────────────────────────────
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME", "")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "")
INSTAGRAM_SESSION_FILE = DATA_DIR / "instagram_session.json"

# ─── Video Settings ───────────────────────────────────────────────────────────
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920  # 9:16 vertical
VIDEO_FPS = 30
VIDEO_BITRATE = "5M"
MAX_VIDEO_DURATION = 60  # seconds (Instagram Reels limit)
CAPTION_FONT_SIZE = 48
CAPTION_FONT_COLOR = "white"
CAPTION_BG_COLOR = "black"
CAPTION_POSITION = "center"  # top, center, bottom

# ─── Content Settings ─────────────────────────────────────────────────────────
VIDEOS_PER_DAY = int(os.getenv("VIDEOS_PER_DAY", "3"))  # 3 videos daily
NICHES = [
    "health_fitness",
    "finance_crypto",
    "tech_ai",
    "ecommerce",
    "education",
    "motivation",
    "food_nutrition",
    "travel",
    "beauty_skincare",
    "productivity",
]

# ─── Trend Engine ─────────────────────────────────────────────────────────────
TRENDS_REFRESH_HOURS = 6  # Refresh trends every 6 hours
TREND_KEYWORDS = {
    "health_fitness": ["workout", "protein", "vitamins", "weight loss", "gym", "yoga"],
    "finance_crypto": ["bitcoin", "investing", "passive income", "crypto", "stocks"],
    "tech_ai": ["artificial intelligence", "chatgpt", "automation", "coding", "python"],
    "ecommerce": ["dropshipping", "shopify", "amazon fba", "online store", "side hustle"],
    "education": ["learn coding", "online course", "study tips", "productivity", "ai tools"],
    "motivation": ["success", "mindset", "discipline", " habits", "goals"],
    "food_nutrition": ["healthy recipes", "meal prep", "superfoods", "diet", "nutrition"],
    "travel": ["travel tips", "budget travel", "solo travel", "digital nomad", "backpacking"],
    "beauty_skincare": ["skincare routine", "anti aging", "beauty tips", "sunscreen", "glow"],
    "productivity": ["time management", "morning routine", "deep work", "focus", "automation"],
}

# ─── Revenue Tracking ─────────────────────────────────────────────────────────
AFFILIATE_LINKS = {
    "iherb": "https://www.iherb.com/?rcode=",
    "amazon": "https://www.amazon.com/dp/",
    "shopify": "https://partners.shopify.com/",
    "binance": "https://www.binance.com/en/register?ref=",
}

# ─── Dashboard ────────────────────────────────────────────────────────────────
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8003"))

# ─── Database ─────────────────────────────────────────────────────────────────
DATABASE_URL = f"sqlite+aiosqlite:///{DATA_DIR}/flipped_factory.db"
