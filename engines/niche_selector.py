"""
Niche Selector — AI-powered niche + topic selection.
Uses trend data to pick the best niche and topic for today.
FREE: Local logic + simple scoring
"""
import json
import random
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("niche_selector")

# ─── Niche Database ───────────────────────────────────────────────────────────
NICHES = {
    "health_fitness": {
        "name": "Health & Fitness",
        "emoji": "💪",
        "hashtags": ["#fitness", "#health", "#workout", "#gym", "#wellness", "#nutrition"],
        "content_types": ["tips", "exercises", "nutrition_facts", "supplements", "before_after"],
        "affiliate_products": ["protein", "vitamins", "workout_gear", "supplements"],
        "best_posting_times": ["6:00", "12:00", "18:00"],
    },
    "finance_crypto": {
        "name": "Finance & Crypto",
        "emoji": "💰",
        "hashtags": ["#finance", "#crypto", "#investing", "#bitcoin", "#money", "#wealth"],
        "content_types": ["tips", "market_analysis", "passive_income", "trading_basics", "news"],
        "affiliate_products": ["trading_platforms", "courses", "tools"],
        "best_posting_times": ["8:00", "14:00", "20:00"],
    },
    "tech_ai": {
        "name": "Tech & AI",
        "emoji": "🤖",
        "hashtags": ["#ai", "#tech", "#coding", "#automation", "#chatgpt", "#python"],
        "content_types": ["tutorials", "tool_reviews", "news", "tips", "demos"],
        "affiliate_products": ["software", "courses", "hosting", "tools"],
        "best_posting_times": ["9:00", "15:00", "21:00"],
    },
    "ecommerce": {
        "name": "E-Commerce",
        "emoji": "🛍️",
        "hashtags": ["#ecommerce", "#shopify", "#dropshipping", "#onlinebusiness", "#sidehustle"],
        "content_types": ["tips", "platform_reviews", "success_stories", "tools", "strategies"],
        "affiliate_products": ["shopify", "tools", "courses"],
        "best_posting_times": ["10:00", "16:00", "20:00"],
    },
    "education": {
        "name": "Education",
        "emoji": "📚",
        "hashtags": ["#learning", "#education", "#study", "#courses", "#skills", "#knowledge"],
        "content_types": ["study_tips", "book_reviews", "skill_tutorials", "life_lessons", "facts"],
        "affiliate_products": ["courses", "books", "tools"],
        "best_posting_times": ["7:00", "13:00", "19:00"],
    },
    "motivation": {
        "name": "Motivation",
        "emoji": "🔥",
        "hashtags": ["#motivation", "#success", "#mindset", "#goals", "#discipline", "#growth"],
        "content_types": ["quotes", "stories", "tips", "habits", "transformations"],
        "affiliate_products": ["books", "courses", "journals"],
        "best_posting_times": ["6:00", "12:00", "21:00"],
    },
    "food_nutrition": {
        "name": "Food & Nutrition",
        "emoji": "🥗",
        "hashtags": ["#food", "#nutrition", "#healthyfood", "#recipes", "#diet", "#mealprep"],
        "content_types": ["recipes", "nutrition_facts", "meal_prep", "superfoods", "reviews"],
        "affiliate_products": ["kitchen_gadgets", "supplements", "cookbooks"],
        "best_posting_times": ["8:00", "12:00", "18:00"],
    },
    "travel": {
        "name": "Travel",
        "emoji": "✈️",
        "hashtags": ["#travel", "#wanderlust", "#adventure", "#explore", "#vacation", "#digitalnomad"],
        "content_types": ["tips", "destinations", "budget_travel", "hidden_gems", "packing"],
        "affiliate_products": ["booking", "gear", "insurance"],
        "best_posting_times": ["9:00", "14:00", "20:00"],
    },
    "beauty_skincare": {
        "name": "Beauty & Skincare",
        "emoji": "✨",
        "hashtags": ["#beauty", "#skincare", "#glow", "#selfcare", "#antiaging", "#routine"],
        "content_types": ["routines", "product_reviews", "tips", "diy", "transformations"],
        "affiliate_products": ["skincare", "tools", "courses"],
        "best_posting_times": ["7:00", "13:00", "19:00"],
    },
    "productivity": {
        "name": "Productivity",
        "emoji": "⚡",
        "hashtags": ["#productivity", "#timemanagement", "#automation", "#focus", "#habits"],
        "content_types": ["tips", "tool_reviews", "routines", "hacks", "transformations"],
        "affiliate_products": ["tools", "courses", "planners"],
        "best_posting_times": ["6:00", "12:00", "18:00"],
    },
}

# ─── Topic Pool Per Niche ─────────────────────────────────────────────────────
TOPIC_POOLS = {
    "health_fitness": [
        "5 exercises you should do every morning",
        "Why protein is essential for muscle recovery",
        "Top 3 vitamins for immune system boost",
        "The truth about weight loss supplements",
        "How to stay fit without a gym membership",
        "Best pre-workout foods for energy",
        "Why sleep is the #1 fitness hack",
        "How to stretch properly before workout",
        "Benefits of cold water exposure",
        "How to build muscle after 30",
    ],
    "finance_crypto": [
        "3 passive income ideas for beginners",
        "How to start investing with $100",
        "Bitcoin explained in 60 seconds",
        "5 money habits that keep you poor",
        "How to build an emergency fund",
        "Stock market basics for beginners",
        "Crypto investing mistakes to avoid",
        "How to save money on taxes legally",
        "The power of compound interest",
        "Side hustles that make $1000/month",
    ],
    "tech_ai": [
        "5 AI tools that save you 10 hours/week",
        "How to use ChatGPT like a pro",
        "Python automation for beginners",
        "Best free AI tools in 2026",
        "How to build a website in 10 minutes",
        "AI that will replace your job",
        "How to automate Instagram posting",
        "Free tools every creator needs",
        "How to use AI for content creation",
        "Coding mistakes beginners make",
    ],
    "ecommerce": [
        "How to start dropshipping in 2026",
        "Shopify vs WooCommerce which is better",
        "5 products that sell like crazy",
        "How to find winning products",
        "Amazon FBA for beginners",
        "How to run Facebook ads profitably",
        "E-commerce mistakes that kill your store",
        "How to create a brand not just a store",
        "Supplier negotiation tips",
        "How to scale from $0 to $10K/month",
    ],
    "education": [
        "How to learn anything 10x faster",
        "5 books every person should read",
        "The best free online courses",
        "How to take effective notes",
        "Study techniques that actually work",
        "How to stay motivated while learning",
        "Skills that will be valuable in 2030",
        "How to learn a new language fast",
        "The science of memory retention",
        "How to build a learning routine",
    ],
    "motivation": [
        "The 5AM rule that changed my life",
        "Why discipline beats motivation",
        "5 habits of highly successful people",
        "How to stay consistent when motivation fades",
        "The power of tiny daily improvements",
        "Why most people never achieve their goals",
        "How to overcome fear of failure",
        "The mindset shift that changed everything",
        "Why you should stop comparing yourself",
        "How to bounce back from setbacks",
    ],
    "food_nutrition": [
        "5 superfoods you should eat daily",
        "Meal prep Sunday guide for beginners",
        "Why most protein bars are unhealthy",
        "How to read nutrition labels properly",
        "Easy healthy recipes under 5 minutes",
        "Foods that boost your metabolism",
        "How to reduce sugar intake naturally",
        "Best plant-based protein sources",
        "How to eat healthy on a budget",
        "Foods that improve brain function",
    ],
    "travel": [
        "How to travel for free using points",
        "Hidden gems in Europe you must visit",
        "Budget travel tips for solo travelers",
        "How to pack light for any trip",
        "Best travel apps you need to download",
        "How to find cheap flights consistently",
        "Digital nomad lifestyle guide",
        "Travel safety tips everyone should know",
        "Best destinations for food lovers",
        "How to plan a trip in 30 minutes",
    ],
    "beauty_skincare": [
        "Simple skincare routine for glowing skin",
        "Why sunscreen is the best anti-aging product",
        "DIY face masks that actually work",
        "How to layer skincare products correctly",
        "Best ingredients for oily skin",
        "Nighttime skincare routine explained",
        "How to get rid of dark circles",
        "Skincare mistakes you're making daily",
        "Best budget skincare products 2026",
        "How to choose the right moisturizer",
    ],
    "productivity": [
        "The 2-minute rule that changed my life",
        "How to eliminate distractions permanently",
        "Best free productivity apps in 2026",
        "How to plan your week like a CEO",
        "The Pomodoro technique explained",
        "How to automate repetitive tasks",
        "Morning routine for maximum productivity",
        "How to focus in a world of distractions",
        "Time blocking method for deep work",
        "How to batch process your work",
    ],
}


# ─── Selection Logic ──────────────────────────────────────────────────────────
def select_niche(trend_rankings: list[dict] = None, prefer_variety: bool = True) -> str:
    """
    Select best niche based on trends + variety.
    If no trend data, picks randomly with weight.
    """
    if trend_rankings and len(trend_rankings) > 0:
        # Weighted random from top 5 niches
        top_5 = trend_rankings[:5]
        weights = [max(1, n["score"]) for n in top_5]
        chosen = random.choices(top_5, weights=weights, k=1)[0]
        return chosen["niche"]
    
    # Fallback: random selection
    return random.choice(list(NICHES.keys()))


def select_topic(niche: str, used_topics: list[str] = None) -> str:
    """Select a topic from the niche pool, avoiding recently used ones."""
    topics = TOPIC_POOLS.get(niche, TOPIC_POOLS["health_fitness"])
    if used_topics:
        available = [t for t in topics if t not in used_topics]
        if available:
            return random.choice(available)
    return random.choice(topics)


def get_niche_info(niche: str) -> dict:
    """Get full info for a niche."""
    return NICHES.get(niche, NICHES["health_fitness"])


def get_hashtags(niche: str, extra: list[str] = None) -> list[str]:
    """Get hashtags for a niche + extras."""
    info = get_niche_info(niche)
    tags = info["hashtags"].copy()
    if extra:
        tags.extend(extra)
    # Always add generic viral tags
    tags.extend(["#viral", "#trending", "#fyp", "#reels"])
    return tags[:15]  # Instagram limit


def get_posting_time(niche: str) -> str:
    """Get best posting time for niche."""
    info = get_niche_info(niche)
    return random.choice(info["best_posting_times"])
