"""
Content Creator — AI script generation using FREE local models.
Uses Ollama (Llama 3) or pyttsx3 fallback for scripts.
"""
import json
import random
import logging
import subprocess
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("content_creator")

SCRIPTS_DIR = Path(__file__).parent.parent / "data" / "scripts"
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)


# ─── Script Templates ─────────────────────────────────────────────────────────
# Used when AI model is not available — these are hand-crafted, high-quality
SCRIPT_TEMPLATES = {
    "health_fitness": [
        {
            "hook": "Stop doing this if you want to lose weight!",
            "body": "Most people make this one mistake with their diet. They skip protein and load up on carbs. But research shows protein is essential for fat loss and muscle recovery. Aim for 1 gram per pound of body weight daily.",
            "cta": "Follow for more health tips!",
            "duration": 30,
        },
        {
            "hook": "This supplement changed my life",
            "body": "Vitamin D deficiency affects over 40% of adults. It causes fatigue, weak immunity, and mood issues. The fix? Get 15 minutes of sunlight daily or take 2000 IU of Vitamin D3 with K2.",
            "cta": "Save this for later!",
            "duration": 35,
        },
        {
            "hook": "The 5 minute morning routine that works",
            "body": "Wake up. Drink water. Do 10 pushups. Stretch for 2 minutes. Write 3 goals. This simple routine sets your day up for success. No gym required. No equipment needed.",
            "cta": "Try this tomorrow morning!",
            "duration": 30,
        },
    ],
    "finance_crypto": [
        {
            "hook": "How to make money while you sleep",
            "body": "Passive income is not truly passive at first. You need to put in the work upfront. Start with index funds. Then build a digital product. Then invest in dividend stocks. Compound interest does the rest.",
            "cta": "Follow for money tips!",
            "duration": 35,
        },
        {
            "hook": "Rich people never say this phrase",
            "body": "I cannot afford it. Instead they ask: How can I afford it? This mindset shift changes everything. Stop limiting yourself with scarcity thinking. Start looking for opportunities.",
            "cta": "Share with someone who needs this!",
            "duration": 30,
        },
    ],
    "tech_ai": [
        {
            "hook": "This free AI tool will blow your mind",
            "body": "ChatGPT can write code, create content, analyze data, and even build websites. But most people use it wrong. The secret is in the prompts. Be specific. Give context. Ask for step by step.",
            "cta": "Follow for AI tips!",
            "duration": 35,
        },
        {
            "hook": "Automate your life with Python in 5 minutes",
            "body": "You can automate emails, social media posts, file organization, and web scraping with just 10 lines of Python. No coding experience needed. Just copy, paste, and run.",
            "cta": "Save this tutorial!",
            "duration": 30,
        },
    ],
    "ecommerce": [
        {
            "hook": "The product that sells itself",
            "body": "Winning products solve a real problem. They have high perceived value. They are lightweight for shipping. They have wow factor. Check trends on TikTok and Amazon to find what is selling right now.",
            "cta": "Follow for e-commerce tips!",
            "duration": 35,
        },
    ],
    "motivation": [
        {
            "hook": "Why you are stuck in life",
            "body": "You are not lazy. You are scared. Scared of failure. Scared of judgment. Scared of success. The cure? Take action before you are ready. Messy action beats perfect planning every time.",
            "cta": "Share with someone who needs this!",
            "duration": 30,
        },
        {
            "hook": "Do this every morning for 30 days",
            "body": "Wake up early. Write down 3 things you are grateful for. Visualize your goals for 2 minutes. Take cold water on your face. Move your body for 5 minutes. Watch how your life changes.",
            "cta": "Start tomorrow!",
            "duration": 35,
        },
    ],
    "food_nutrition": [
        {
            "hook": "Eat this every morning for energy",
            "body": "Oats with banana, honey, and cinnamon. This combo gives you sustained energy for 4 hours. No crash. No sugar spike. Add protein powder for extra fuel. Takes 2 minutes to make.",
            "cta": "Save this recipe!",
            "duration": 30,
        },
    ],
    "travel": [
        {
            "hook": "Travel for free using this trick",
            "body": "Sign up for travel credit cards with sign up bonuses. Use them for everyday spending. Pay them off monthly. Redeem points for flights. This is how frequent flyers travel for almost nothing.",
            "cta": "Follow for travel hacks!",
            "duration": 35,
        },
    ],
    "beauty_skincare": [
        {
            "hook": "Your skincare routine is wrong",
            "body": "You are applying products in the wrong order. Cleanse first. Then toner. Then serum. Then moisturizer. Then sunscreen. Never skip sunscreen. Even indoors. UV rays cause 80% of aging.",
            "cta": "Save this routine!",
            "duration": 30,
        },
    ],
    "productivity": [
        {
            "hook": "How I get 8 hours of work done in 4",
            "body": "Time blocking changed everything. I batch similar tasks together. No multitasking. Phone on airplane mode during deep work. Two hour blocks with breaks in between. Output doubled.",
            "cta": "Try this today!",
            "duration": 35,
        },
    ],
}


# ─── AI Script Generation (via Ollama) ────────────────────────────────────────
def generate_script_with_ai(topic: str, niche: str, duration: int = 30, language: str = "en") -> dict:
    """
    Generate a video script using Ollama (FREE local AI).
    Falls back to templates if Ollama is not running.
    """
    prompt = f"""Create a short-form video script for Instagram Reels.

Topic: {topic}
Niche: {niche}
Target duration: {duration} seconds
Language: {language}

Format your response as JSON with these keys:
{{
    "hook": "Opening line that grabs attention (5 seconds)",
    "body": "Main content - conversational, informative (20 seconds)",
    "cta": "Call to action - follow/save/share (5 seconds)",
    "duration": {duration},
    "hashtags": ["relevant", "hashtags", "for", "instagram"]
}}

Rules:
- Keep it conversational and engaging
- Use simple language
- Include specific numbers or facts when possible
- Make the hook irresistible
- CTA should be clear and actionable
- Output ONLY valid JSON, no other text"""

    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:11434/api/generate",
             "-d", json.dumps({"model": "mistral", "prompt": prompt, "stream": False})],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            response = json.loads(result.stdout)
            text = response.get("response", "")
            # Extract JSON from response
            if "{" in text:
                json_str = text[text.index("{"):text.rindex("}") + 1]
                script = json.loads(json_str)
                logger.info(f"AI script generated for: {topic}")
                return script
    except Exception as e:
        logger.warning(f"Ollama not available: {e}")

    # Fallback to templates
    return get_template_script(niche)


def get_template_script(niche: str) -> dict:
    """Get a pre-written template script for the niche."""
    templates = SCRIPT_TEMPLATES.get(niche, SCRIPT_TEMPLATES["health_fitness"])
    script = random.choice(templates).copy()
    script["hashtags"] = []
    return script


# ─── Multi-language ───────────────────────────────────────────────────────────
def translate_script(script: dict, target_lang: str) -> dict:
    """
    Translate script to target language using Ollama.
    Returns translated script or original if translation fails.
    """
    if target_lang == "en":
        return script

    lang_names = {"es": "Spanish", "hi": "Hindi", "ar": "Arabic", "pt": "Portuguese"}
    lang_name = lang_names.get(target_lang, target_lang)

    prompt = f"""Translate this video script to {lang_name}. Keep the same energy and tone.

Original: {json.dumps(script)}

Return ONLY valid JSON with translated hook, body, and cta fields."""

    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:11434/api/generate",
             "-d", json.dumps({"model": "mistral", "prompt": prompt, "stream": False})],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            response = json.loads(result.stdout)
            text = response.get("response", "")
            if "{" in text:
                json_str = text[text.index("{"):text.rindex("}") + 1]
                translated = json.loads(json_str)
                translated["language"] = target_lang
                return translated
    except Exception as e:
        logger.warning(f"Translation failed: {e}")

    script["language"] = target_lang
    return script


# ─── Save/Load Scripts ────────────────────────────────────────────────────────
def save_script(script: dict, agent_type: str) -> Path:
    """Save script to disk."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = SCRIPTS_DIR / f"{timestamp}_{agent_type}.json"
    filename.write_text(json.dumps(script, indent=2, ensure_ascii=False))
    logger.info(f"Script saved: {filename.name}")
    return filename


def load_scripts(limit: int = 10) -> list[dict]:
    """Load recent scripts."""
    files = sorted(SCRIPTS_DIR.glob("*.json"), reverse=True)[:limit]
    scripts = []
    for f in files:
        try:
            scripts.append(json.loads(f.read_text()))
        except Exception:
            pass
    return scripts
