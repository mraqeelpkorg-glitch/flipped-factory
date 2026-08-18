"""
Enhanced Safety Gate — Expanded content safety with Instagram policy compliance.

Adds to existing safety_gate.py:
- Impersonation detection
- Misleading hook verification
- Private info detection (ALL agents)
- Dangerous challenge detection
- Instagram community guidelines compliance
- Automated content warnings
"""

import re
import logging
from typing import Optional

logger = logging.getLogger("enhanced_safety")

# ─── Impersonation Detection ─────────────────────────────────────────────────

IMPERSONATION_KEYWORDS = [
    "official account", "verified account", "real account",
    "this is actually", "i am actually", "i'm actually",
    "official page", "real page", "verified page",
    "i am the real", "i'm the real", "the real",
    "my official", "my verified", "my real",
    "this is the real", "this is the actual",
    "legit account", "authentic account",
]

IMPERSONATION_PATTERNS = [
    r"i\s+am\s+(?:the\s+)?(?:real|actual|official|legit)",
    r"this\s+is\s+(?:the\s+)?(?:real|actual|official|legit)",
    r"(?:my|the)\s+(?:real|actual|official)\s+(?:account|page|profile)",
    r"(?:verified|official)\s+(?:account|page|profile|channel)",
]

名人_NAMES = [
    "elon musk", "jeff bezos", "bill gates", "mark zuckerberg",
    "warren buffett", "dwayne johnson", "taylor swift", "beyonce",
    "kylie jenner", "cristiano ronaldo", "lionel messi",
    "kanye west", "kim kardashian", "mr beast",
]

def check_impersonation(text: str) -> dict:
    """
    Check if content may impersonate someone.
    
    Returns:
        {
            "is_impersonation_risk": bool,
            "risk_level": "low" | "medium" | "high",
            "flags": list,
            "celebrity_mentions": list,
        }
    """
    text_lower = text.lower()
    flags = []
    
    # Check impersonation keywords
    for kw in IMPERSONATION_KEYWORDS:
        if kw in text_lower:
            flags.append(f"impersonation_keyword: '{kw}'")
    
    # Check impersonation patterns
    for pattern in IMPERSONATION_PATTERNS:
        if re.search(pattern, text_lower):
            flags.append(f"impersonation_pattern: '{pattern}'")
    
    # Check celebrity mentions
    celebrity_mentions = []
    for name in 名人_NAMES:
        if name in text_lower:
            celebrity_mentions.append(name)
            flags.append(f"celebrity_mention: '{name}'")
    
    # Determine risk level
    if len(flags) >= 3:
        risk_level = "high"
    elif len(flags) >= 1:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    return {
        "is_impersonation_risk": len(flags) > 0,
        "risk_level": risk_level,
        "flags": flags,
        "celebrity_mentions": celebrity_mentions,
    }


# ─── Misleading Hook Verification ───────────────────────────────────────────

MISLEADING_PATTERNS = [
    (r"(?:you\s+won'?t\s+believe|unbelievable|shocking)", "clickbait_exaggeration"),
    (r"(?:doctors?\s+don'?t\s+want\s+you\s+to\s+know)", "conspiracy_claim"),
    (r"(?:this\s+(?:one\s+)?(?:trick|secret|hack)\s+(?:will|that)\s+(?:change|fix|transform))", "miracle_claim"),
    (r"(?:guaranteed\s+(?:results?|income|success|money))", "guarantee_claim"),
    (r"(?:100%\s+(?:effective|guaranteed|proven))", "absolute_claim"),
    (r"(?:make\s+\$?\d+k?\s+(?:per|in|a)\s+(?:day|week|month|hour))", "income_claim"),
    (r"(?:lose\s+\d+\s*(?:kg|lbs?|pounds?)\s+in\s+\d+\s*(?:days?|weeks?))", "weight_loss_claim"),
    (r"(?:cures?\s+(?:all|every|cancer|diabetes))", "medical_cure_claim"),
    (r"(?:eliminates?\s+(?:all|every)\s+(?:debt|fat|wrinkles?))", "miracle_elimination"),
    (r"(?:secret\s+(?:formula|method|system)\s+(?:that|which)\s+(?:they|big\s+pharma|governments?)\s+hide)", "conspiracy_secret"),
    (r"(?:you\s+need\s+to\s+see\s+this\s+before\s+(?:it'?s?\s+)?taken\s+down)", "urgency_manipulation"),
    (r"(?:last\s+chance|only\s+\d+\s+left|before\s+(?:they|it)\s+(?:delete|remove|ban))", "scarcity_manipulation"),
]

EXAGGERATED_CLAIMS = [
    "proven to work", "scientifically proven", "doctors recommend",
    "clinically tested", "FDA approved", "100% natural",
    "no side effects", "instant results", "overnight success",
    "get rich quick", "passive income guaranteed", "financial freedom",
    "lose weight fast", "build muscle fast", "reverse aging",
]

def check_misleading_hook(hook_text: str) -> dict:
    """
    Check if a hook may be misleading or violate Instagram guidelines.
    
    Returns:
        {
            "is_misleading": bool,
            "risk_level": "low" | "medium" | "high",
            "flags": list,
            "suggestion": str,
        }
    """
    text_lower = hook_text.lower()
    flags = []
    
    # Check patterns
    for pattern, flag_type in MISLEADING_PATTERNS:
        if re.search(pattern, text_lower):
            flags.append(f"{flag_type}: '{pattern}'")
    
    # Check exaggerated claims
    for claim in EXAGGERATED_CLAIMS:
        if claim in text_lower:
            flags.append(f"exaggerated_claim: '{claim}'")
    
    # Determine risk
    if len(flags) >= 2:
        risk_level = "high"
    elif len(flags) == 1:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    # Generate suggestion
    suggestion = ""
    if flags:
        suggestion = (
            "Hook may be flagged as misleading. Consider: "
            "1) Replace absolute claims with qualified statements, "
            "2) Add context/disclaimers, "
            "3) Use 'may help' instead of 'guarantees', "
            "4) Cite sources for health/financial claims"
        )
    
    return {
        "is_misleading": len(flags) > 0,
        "risk_level": risk_level,
        "flags": flags,
        "suggestion": suggestion,
    }


# ─── Private Info Detection ──────────────────────────────────────────────────

PRIVATE_INFO_PATTERNS = [
    (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "phone_number"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "email_address"),
    (r"\b\d{3}[-]?\d{2}[-]?\d{4}\b", "ssn"),
    (r"\b(?:password|passwd|pwd)\s*[=:]\s*\S+", "password"),
    (r"\b[A-Za-z0-9]{32,}\b", "api_key_or_token"),
    (r"\bsk[-_](?:live|test)[-_][A-Za-z0-9]{20,}\b", "stripe_key"),
    (r"\bghp_[A-Za-z0-9]{36}\b", "github_token"),
    (r"\bAKIA[A-Z0-9]{16}\b", "aws_access_key"),
    (r"\b\d{1,5}\s+\w+\s+(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln)\b", "street_address"),
    (r"\b\d{10,}\b", "credit_card_or_id"),
]

PRIVATE_KEYWORDS = [
    "password", "secret", "confidential", "private",
    "do not share", "don't share", "internal use only",
    "nda", "non-disclosure", "classified",
]

def check_private_info(text: str) -> dict:
    """
    Check if text contains private/sensitive information.
    
    Returns:
        {
            "has_private_info": bool,
            "risk_level": "low" | "medium" | "high",
            "detected_types": list,
            "flags": list,
        }
    """
    flags = []
    detected_types = set()
    
    # Check patterns
    for pattern, info_type in PRIVATE_INFO_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            detected_types.add(info_type)
            flags.append(f"{info_type}: {len(matches)} instance(s)")
    
    # Check keywords
    text_lower = text.lower()
    for kw in PRIVATE_KEYWORDS:
        if kw in text_lower:
            detected_types.add("sensitive_keyword")
            flags.append(f"sensitive_keyword: '{kw}'")
    
    # Determine risk
    high_risk_types = {"password", "api_key_or_token", "stripe_key", "github_token", "aws_access_key", "ssn"}
    if detected_types & high_risk_types:
        risk_level = "high"
    elif detected_types:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    return {
        "has_private_info": len(flags) > 0,
        "risk_level": risk_level,
        "detected_types": list(detected_types),
        "flags": flags,
    }


# ─── Dangerous Challenge Detection ──────────────────────────────────────────

DANGEROUS_CHALLENGES = [
    "blackout challenge", "choking challenge", "suffocation challenge",
    "balloon challenge", "tidal pod challenge", "fire challenge",
    "duct tape challenge", "skull breaker challenge", "velcro challenge",
    "cinnamon challenge", "milk crate challenge", "corn kernel challenge",
    "bus surfer challenge", "train surfing", "roof surfing",
    "gasoline challenge", "dry ice challenge", "bleach challenge",
    "salt and ice challenge", "rice challenge", " condom challenge",
    "nyquil challenge", "benadryl challenge", "sleeping pill challenge",
]

DANGEROUS_KEYWORDS = [
    "try this at home", "do this yourself", "copy this",
    "challenge", "dare", "stunt", "extreme",
    "dangerous", "risky", "hazardous", "lethal",
    "fatal", "death", "suicide", "self-harm",
    "drink bleach", "swallow", "overdose",
]

def check_dangerous_challenge(text: str) -> dict:
    """
    Check if content promotes dangerous challenges or activities.
    
    Returns:
        {
            "is_dangerous": bool,
            "risk_level": "low" | "medium" | "high",
            "flags": list,
            "challenge_detected": str | None,
        }
    """
    text_lower = text.lower()
    flags = []
    challenge_detected = None
    
    # Check specific dangerous challenges
    for challenge in DANGEROUS_CHALLENGES:
        if challenge in text_lower:
            challenge_detected = challenge
            flags.append(f"dangerous_challenge: '{challenge}'")
    
    # Check dangerous keywords
    danger_count = 0
    for kw in DANGEROUS_KEYWORDS:
        if kw in text_lower:
            danger_count += 1
            flags.append(f"dangerous_keyword: '{kw}'")
    
    # Determine risk
    if challenge_detected:
        risk_level = "high"
    elif danger_count >= 3:
        risk_level = "high"
    elif danger_count >= 1:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    return {
        "is_dangerous": len(flags) > 0,
        "risk_level": risk_level,
        "flags": flags,
        "challenge_detected": challenge_detected,
    }


# ─── Combined Enhanced Safety Check ──────────────────────────────────────────

def enhanced_safety_check(text: str, hook_text: str = "") -> dict:
    """
    Run ALL enhanced safety checks on content.
    
    Args:
        text: Full content text
        hook_text: Hook text (if different from full text)
    
    Returns:
        {
            "overall_safe": bool,
            "overall_risk": str,  # "low", "medium", "high"
            "checks": {
                "impersonation": {...},
                "misleading": {...},
                "private_info": {...},
                "dangerous": {...},
            },
            "action": "approve" | "review" | "block",
            "reasons": list,
        }
    """
    checks = {
        "impersonation": check_impersonation(text),
        "misleading": check_misleading_hook(hook_text or text),
        "private_info": check_private_info(text),
        "dangerous": check_dangerous_challenge(text),
    }
    
    # Determine overall risk
    risks = [c.get("risk_level", "low") for c in checks.values()]
    
    if "high" in risks:
        overall_risk = "high"
        action = "block"
    elif "medium" in risks:
        overall_risk = "medium"
        action = "review"
    else:
        overall_risk = "low"
        action = "approve"
    
    # Collect reasons
    reasons = []
    for check_name, check_result in checks.items():
        if check_result.get("is_impersonation_risk") or \
           check_result.get("is_misleading") or \
           check_result.get("has_private_info") or \
           check_result.get("is_dangerous"):
            reasons.append(f"{check_name}: {check_result.get('risk_level', 'low')} risk")
    
    return {
        "overall_safe": action == "approve",
        "overall_risk": overall_risk,
        "checks": checks,
        "action": action,
        "reasons": reasons,
    }


# ─── Convenience Functions ────────────────────────────────────────────────────

def check_all(text: str, hook_text: str = "") -> dict:
    """Run all enhanced safety checks."""
    return enhanced_safety_check(text, hook_text)

def check_hook(hook_text: str) -> dict:
    """Check a hook for misleading content."""
    return check_misleading_hook(hook_text)

def check_content_safety(text: str) -> dict:
    """Check content for private info, impersonation, dangerous challenges."""
    return enhanced_safety_check(text)
