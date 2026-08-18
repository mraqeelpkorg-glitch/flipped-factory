"""
Daily Strategy Engine — Daily viral content direction.

Responsibilities:
1. Analyze current trends across niches
2. Select best niches/topics for today
3. Choose hook patterns (question, shock, value, story)
4. Determine posting schedule
5. Persist strategy to daily_strategy/YYYY-MM-DD.json

The system makes its OWN daily content direction — user should NOT have to provide daily direction.
"""
import json
import os
import random
import logging
from pathlib import Path
from datetime import datetime, date

logger = logging.getLogger("daily_strategy")

STRATEGY_DIR = Path(__file__).parent
STRATEGY_DIR.mkdir(parents=True, exist_ok=True)

# ─── Hook Patterns ─────────────────────────────────────────────────────────────
HOOK_PATTERNS = {
    "question": [
        "Did you know {stat}?",
        "What if I told you {topic}?",
        "Why is everyone talking about {topic}?",
        "Have you ever wondered about {topic}?",
        "What's the secret behind {topic}?",
    ],
    "shock": [
        "This changes everything about {topic}",
        "Nobody talks about this...",
        "{stat} — and most people don't know",
        "Stop doing this if you want {benefit}",
        "The truth about {topic} that nobody tells you",
    ],
    "value": [
        "Here's how to {benefit} in 30 seconds",
        "The #1 way to {benefit}",
        "3 things you need to know about {topic}",
        "Save this for later — {topic}",
        "Your complete guide to {topic}",
    ],
    "story": [
        "I tried {topic} for 30 days...",
        "From zero to {benefit} — here's how",
        "The moment I realized {topic}",
        "My journey with {topic}",
        "What happened when I {action}",
    ],
}

# ─── Niche Weights (adjust based on performance) ──────────────────────────────
NICHE_WEIGHTS = {
    "health_fitness": 1.0,
    "finance_crypto": 1.0,
    "tech_ai": 1.0,
    "education": 1.0,
    "motivation": 1.0,
    "ecommerce": 1.0,
    "food_nutrition": 1.0,
    "travel": 1.0,
    "beauty_skincare": 1.0,
    "productivity": 1.0,
}

# ─── Content Mix (what percentage of each agent type per day) ─────────────────
DEFAULT_CONTENT_MIX = {
    "youtube_clipper": 2,
    "podcast_clipper": 2,
    "blog_to_video": 1,
    "remix_flip": 1,
    "dub_flip": 1,
    "data_to_video": 1,
    "product_compilation": 1,
    "bts_educational": 0,
    "trending_niche": 2,
    "course_teaser": 0,
    "live_highlights": 1,
    "screenshot_tutorial": 0,
}


def generate_daily_strategy(target_date: str = None) -> dict:
    """
    Generate a daily content strategy.
    
    Returns strategy with:
    - target_niches: which niches to focus on
    - hook_patterns: which hook types to use
    - content_mix: how many of each agent type
    - priority_topics: topics to prioritize
    - posting_schedule: when to post
    """
    if target_date is None:
        target_date = date.today().isoformat()
    
    # Seed random with date for consistency within a day
    seed = hash(target_date) % (2**31)
    rng = random.Random(seed)
    
    # 1. Select 3-4 niches to focus on today
    all_niches = list(NICHE_WEIGHTS.keys())
    # Weight by performance (default 1.0, adjustable)
    weights = [NICHE_WEIGHTS[n] for n in all_niches]
    selected_niches = rng.choices(all_niches, weights=weights, k=min(4, len(all_niches)))
    selected_niches = list(dict.fromkeys(selected_niches))  # dedupe while preserving order
    
    # 2. Select hook patterns
    pattern_names = list(HOOK_PATTERNS.keys())
    selected_patterns = rng.sample(pattern_names, k=min(3, len(pattern_names)))
    
    # 3. Generate hooks for selected niches
    priority_hooks = []
    for niche in selected_niches:
        pattern = rng.choice(selected_patterns)
        hook_template = rng.choice(HOOK_PATTERNS[pattern])
        hook = hook_template.format(
            stat="85% of people don't know this",
            topic=niche.replace("_", " "),
            benefit=f"better {niche.replace('_', ' ')}",
            action=f"tried {niche.replace('_', ' ')}",
        )
        priority_hooks.append({
            "niche": niche,
            "pattern": pattern,
            "hook": hook,
        })
    
    # 4. Content mix
    content_mix = dict(DEFAULT_CONTENT_MIX)
    total_posts = sum(content_mix.values())
    
    # 5. Posting schedule (4 posts per day, evenly spaced)
    posting_schedule = [
        {"time": "09:00", "type": "hook_value"},
        {"time": "12:00", "type": "educational"},
        {"time": "17:00", "type": "entertainment"},
        {"time": "21:00", "type": "viral_potential"},
    ]
    
    strategy = {
        "date": target_date,
        "generated_at": datetime.now().isoformat(),
        "target_niches": selected_niches,
        "hook_patterns": selected_patterns,
        "priority_hooks": priority_hooks,
        "content_mix": content_mix,
        "total_posts_target": total_posts,
        "posting_schedule": posting_schedule,
        "notes": "Auto-generated daily strategy. Adjust NICHE_WEIGHTS based on performance.",
    }
    
    # Persist
    save_strategy(strategy, target_date)
    
    logger.info(f"Daily strategy generated for {target_date}: {len(selected_niches)} niches, {total_posts} posts")
    return strategy


def save_strategy(strategy: dict, target_date: str):
    """Save strategy to daily_strategy/YYYY-MM-DD.json"""
    filepath = STRATEGY_DIR / f"{target_date}.json"
    with open(filepath, "w") as f:
        json.dump(strategy, f, indent=2)
    logger.info(f"Strategy saved: {filepath}")


def load_strategy(target_date: str = None) -> dict:
    """Load strategy for a given date. Returns None if not found."""
    if target_date is None:
        target_date = date.today().isoformat()
    
    filepath = STRATEGY_DIR / f"{target_date}.json"
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    return None


def get_todays_strategy() -> dict:
    """Get or generate today's strategy."""
    strategy = load_strategy()
    if strategy is None:
        strategy = generate_daily_strategy()
    return strategy


def get_next_content_item() -> dict:
    """
    Get the next content item to create based on today's strategy.
    Returns: {agent_type, niche, hook, hook_pattern}
    """
    strategy = get_todays_strategy()
    
    # Get remaining content to create
    mix = strategy.get("content_mix", {})
    hooks = strategy.get("priority_hooks", [])
    
    # Find agent types with remaining slots
    available = []
    for agent_type, count in mix.items():
        if count > 0:
            available.append(agent_type)
    
    if not available:
        return {"agent_type": "youtube_clipper", "niche": "education", "hook": "Check this out!"}
    
    agent_type = available[0]
    niche = hooks[0]["niche"] if hooks else "education"
    hook = hooks[0]["hook"] if hooks else "Check this out!"
    
    return {
        "agent_type": agent_type,
        "niche": niche,
        "hook": hook,
        "hook_pattern": hooks[0].get("pattern", "value") if hooks else "value",
    }


def update_niche_weight(niche: str, weight: float):
    """Update niche weight based on performance."""
    if niche in NICHE_WEIGHTS:
        NICHE_WEIGHTS[niche] = max(0.1, min(3.0, weight))
        logger.info(f"Niche weight updated: {niche} = {NICHE_WEIGHTS[niche]}")


if __name__ == "__main__":
    strategy = generate_daily_strategy()
    print(json.dumps(strategy, indent=2))
