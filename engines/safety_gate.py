"""
Content Safety Gate — Detects harmful content before publishing.

Categories:
- hate, harassment, threats, sexual_content, violence
- illegal_activity, dangerous_instructions, fraud
- medical_misinformation, minor_safety

Each category scored 0-1. Overall risk = weighted average.
"""
import re
import logging

logger = logging.getLogger("safety_gate")

# ─── Blocklists ───────────────────────────────────────────────────────────────
HATE_KEYWORDS = [
    "nigger", "faggot", "kike", "spic", "chink", "wetback",
    "retard", "cripple", "tard", "gook", "coon",
]

HARASSMENT_KEYWORDS = [
    "kill yourself", "kys", "go die", "wish you were dead",
    "stupid idiot", "worthless", "pathetic loser", "no one likes you",
    "you should quit", "you're nothing",
]

THREAT_KEYWORDS = [
    "i will kill", "i'm going to kill", "gonna kill you",
    "i will find you", "i know where you live",
    "you're dead", "watch your back",
]

SEXUAL_KEYWORDS = [
    "sex tape", "nude", "naked", "explicit", "porn",
    "onlyfans", "xxx", "adult content", "nsfw",
    "sexual assault", "rape",
]

VIOLENCE_KEYWORDS = [
    "behead", "torture", "murder", "stab", "shoot to kill",
    "mass shooting", "bomb making", "build a bomb",
    "how to kill", "weapon",
]

ILLEGAL_KEYWORDS = [
    "buy drugs", "sell drugs", "meth lab", "heroin",
    "cocaine dealer", "money laundering", "tax evasion",
    "identity theft", "credit card fraud", "hack account",
]

DANGEROUS_KEYWORDS = [
    "suicide method", "how to suicide", "overdose",
    "self harm", "cut yourself", "eating disorder tips",
    "starve yourself", "purge",
]

FRAUD_KEYWORDS = [
    "guaranteed returns", "double your money", "get rich quick",
    "pyramid scheme", "mlm", "ponzi", "invest now",
    "send me money", "wire transfer", "crypto scam",
]

MEDICAL_MISINFO_KEYWORDS = [
    "vaccines cause", "cure cancer with", "miracle cure",
    "doctors don't want you to know", "big pharma conspiracy",
    "homeopathy cures", "essential oils cure",
]

MINOR_SAFETY_KEYWORDS = [
    "child labor", "child abuse", "exploit children",
    "minor dating", "underage", "pedo",
]

# ─── Emotion/Danger Indicators ────────────────────────────────────────────────
EMOTIONAL_INTENSITY_WORDS = [
    "outrageous", "disgusting", "unbelievable", "shocking",
    "terrifying", "horrifying", "devastating", "catastrophic",
]

PROFANITY_PATTERNS = [
    r'\bf+u+c+k+\w*\b', r'\bs+h+i+t+\w*\b', r'\ba+s+s+h+o+l+e+\w*\b',
    r'\bb+i+t+c+h+\w*\b', r'\bd+a+m+n+\w*\b',
]


def _count_matches(text: str, keywords: list) -> int:
    """Count keyword matches in text."""
    text_lower = text.lower()
    count = 0
    for kw in keywords:
        if kw in text_lower:
            count += 1
    return count


def _count_pattern_matches(text: str, patterns: list) -> int:
    """Count regex pattern matches."""
    count = 0
    for pat in patterns:
        count += len(re.findall(pat, text, re.IGNORECASE))
    return count


def _calculate_category_score(count: int, text_length: int) -> float:
    """Convert raw count to 0-1 score based on text length."""
    if text_length == 0:
        return 0.0
    # Normalize: 1 match per 50 words = high score
    words = max(1, text_length // 5)
    density = count / words
    score = min(1.0, density * 5)
    return round(score, 3)


def check_safety(text: str, audio_path: str = None) -> dict:
    """
    Check content safety across all categories.
    Returns dict with per-category scores (0-1) and overall_risk (0-1).
    """
    if not text or not text.strip():
        return {
            "hate": 0, "harassment": 0, "threats": 0,
            "sexual_content": 0, "violence": 0,
            "illegal_activity": 0, "dangerous": 0,
            "fraud": 0, "medical_misinfo": 0,
            "minor_safety": 0, "profanity": 0,
            "overall_risk": 0,
        }
    
    text_len = max(1, len(text))
    
    # Count matches per category
    hate_count = _count_matches(text, HATE_KEYWORDS)
    harass_count = _count_matches(text, HARASSMENT_KEYWORDS)
    threat_count = _count_matches(text, THREAT_KEYWORDS)
    sexual_count = _count_matches(text, SEXUAL_KEYWORDS)
    violence_count = _count_matches(text, VIOLENCE_KEYWORDS)
    illegal_count = _count_matches(text, ILLEGAL_KEYWORDS)
    dangerous_count = _count_matches(text, DANGEROUS_KEYWORDS)
    fraud_count = _count_matches(text, FRAUD_KEYWORDS)
    medical_count = _count_matches(text, MEDICAL_MISINFO_KEYWORDS)
    minor_count = _count_matches(text, MINOR_SAFETY_KEYWORDS)
    profanity_count = _count_pattern_matches(text, PROFANITY_PATTERNS)
    
    # Calculate scores
    scores = {
        "hate": _calculate_category_score(hate_count, text_len),
        "harassment": _calculate_category_score(harass_count, text_len),
        "threats": _calculate_category_score(threat_count, text_len),
        "sexual_content": _calculate_category_score(sexual_count, text_len),
        "violence": _calculate_category_score(violence_count, text_len),
        "illegal_activity": _calculate_category_score(illegal_count, text_len),
        "dangerous": _calculate_category_score(dangerous_count, text_len),
        "fraud": _calculate_category_score(fraud_count, text_len),
        "medical_misinfo": _calculate_category_score(medical_count, text_len),
        "minor_safety": _calculate_category_score(minor_count, text_len),
        "profanity": _calculate_category_score(profanity_count, text_len),
    }
    
    # Overall risk = weighted average
    weights = {
        "hate": 1.5, "harassment": 1.3, "threats": 1.5,
        "sexual_content": 1.2, "violence": 1.3,
        "illegal_activity": 1.4, "dangerous": 1.4,
        "fraud": 1.2, "medical_misinfo": 1.0,
        "minor_safety": 1.5, "profanity": 0.3,
    }
    
    total_weight = sum(weights.values())
    weighted_sum = sum(scores[k] * weights[k] for k in weights)
    overall_risk = round(weighted_sum / total_weight, 3)
    
    scores["overall_risk"] = overall_risk
    
    logger.info(f"Safety check: overall_risk={overall_risk:.3f}")
    return scores


def get_safety_status(safety_result: dict) -> str:
    """
    Determine safety status from check result.
    Returns: APPROVED / HUMAN_REVIEW_REQUIRED / BLOCKED
    """
    overall = safety_result.get("overall_risk", 0)
    
    # Check for any high-severity category
    for key, value in safety_result.items():
        if key == "overall_risk":
            continue
        if isinstance(value, (int, float)):
            if value >= 0.8:
                return "BLOCKED"
    
    # Check thresholds
    if overall >= 0.6:
        return "BLOCKED"
    elif overall >= 0.3 or overall > 0.4:
        return "HUMAN_REVIEW_REQUIRED"
    else:
        return "APPROVED"


def get_safety_report(safety_result: dict) -> str:
    """Generate human-readable safety report."""
    status = get_safety_status(safety_result)
    
    lines = [f"Safety Status: {status}"]
    lines.append(f"Overall Risk: {safety_result.get('overall_risk', 0):.3f}")
    lines.append("")
    
    for key, value in safety_result.items():
        if key == "overall_risk":
            continue
        if isinstance(value, (int, float)) and value > 0:
            level = "HIGH" if value >= 0.5 else "MEDIUM" if value >= 0.3 else "LOW"
            lines.append(f"  {key}: {value:.3f} ({level})")
    
    return "\n".join(lines)
