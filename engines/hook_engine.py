"""
Hook Engine — Podcast clip hook generation.

Generates 3 candidate hooks per clip candidate using deterministic,
content-grounded heuristics — NO paid AI APIs and NO invented facts.

Hook types:
    QUESTION   -> "Did you know that {claim taken verbatim from the clip}?"
    STATEMENT  -> teaser framed around the clip's actual topic
    STAT       -> the real statistic found in the clip (only when one exists)
    FACT       -> echoes the clip's own attribution (research/study/data)
    EMOTIONAL  -> the clip's own emotional line (only when emotion is present)

Accuracy rules (hard constraints):
    * Numbers are never invented. A STAT hook is only produced when the clip
      transcript actually contains a number with a meaningful unit/context.
    * Facts are only claimed when the clip itself cites research/studies/data.
    * Emotional hooks quote the clip verbatim (trimmed) — never fabricated.
    * Every hook embeds real words/sentences from the transcript.

Hook object shape (matches engines/podcast_db.py save_hooks):
    {"text": str, "type": "question|statement|stat|fact|emotional", "score": int}

Public API:
    generate_hooks(clip_text, clip_duration, niche, speaker_name="") -> list[dict]
    select_best_hook(hooks)                                          -> dict
    analyze_hook_quality(hook_text)                                  -> int 0-100
"""
import logging
import re

logger = logging.getLogger("hook_engine")

HOOK_TYPES = ("question", "statement", "stat", "fact", "emotional")

# ─── Text helpers ─────────────────────────────────────────────────────────────
_PLACEHOLDER_RE = re.compile(r"\[.*?\]|\(.*?\)|♪|\*\*+")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_DISCOURSE_PREFIX_RE = re.compile(
    r"^(?:so|well|and|but|that|you know|i mean|like|basically|actually|"
    r"right|ok|okay|yeah|yes|no|now|look|listen|um|uh)\b[,:]?\s+",
    re.IGNORECASE,
)
_ATTRIBUTION_CLAUSE_RE = re.compile(
    r"^(?:according to\s+)?(?:research|studies|the study|study|data|evidence|"
    r"scientists|researchers|experts|doctors?)\s*"
    r"(?:show[s]?|found|say[s]?|indicat\w*|suggest\w*|confirm\w*|prove\w*|that)?"
    r"[,:]?\s+",
    re.IGNORECASE,
)
_STAT_NUM_RE = re.compile(
    r"(?<!\w)(\d+(?:[.,]\d+)?)\s*"
    r"(%|percent|per cent|fold|x|times|k|m|b|million|billion|thousand|"
    r"years?|days?|weeks?|months?|hours?|minutes?|seconds?)?"
)


def _tokenize(text: str) -> list:
    """Lowercase word tokens, keeping numbers and apostrophes (here's)."""
    return re.findall(r"[a-z0-9']+", text.lower())


def _word_hits(text: str, wordlist: frozenset) -> set:
    """Unique tokens of `text` that appear in `wordlist`."""
    return set(_tokenize(text)) & wordlist


def _normalize(text: str) -> str:
    """Folded text for comparison: lowercase, punctuation stripped, spaces."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", text.lower())).strip()


def _trim_to_words(text: str, n: int) -> str:
    """Trim text to n words, appending '...' when truncated."""
    parts = text.split()
    if len(parts) <= n:
        return text
    return " ".join(parts[:n]).rstrip(" ,;:-") + "..."


def _to_claim(text: str, max_words: int = 13) -> str:
    """
    Turn a sentence into a clean lowercase-starting clause (verbatim words).
    Strips leading discourse fillers, trims to max_words, removes terminal
    punctuation so it can be embedded in "Did you know that {claim}?".
    """
    claim = _PLACEHOLDER_RE.sub(" ", text or "")
    claim = claim.replace("…", " ").strip(" \t\"'“”‘’")
    for _ in range(2):
        m = _DISCOURSE_PREFIX_RE.match(claim)
        if m:
            claim = claim[m.end():]
    claim = _trim_to_words(claim, max_words)
    claim = re.sub(r"[.!?]+$", "", claim).rstrip()
    if claim and claim[0].isupper():
        claim = claim[0].lower() + claim[1:]
    return claim


def _display_topic(topic: str) -> str:
    """Capitalize the first letter of a topic phrase for hook display."""
    topic = (topic or "this").strip()
    return topic[0].upper() + topic[1:] if topic else "this"


# ─── Content lexicons ─────────────────────────────────────────────────────────
_STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "if", "then", "so", "just", "like",
    "really", "very", "actually", "basically", "literally", "you", "your",
    "you're", "i", "i'm", "im", "me", "my", "we", "we're", "our", "us", "they",
    "them", "their", "he", "she", "it", "its", "this", "that", "these", "those",
    "there", "here", "is", "are", "was", "were", "be", "been", "being", "have",
    "has", "had", "do", "does", "did", "doing", "will", "would", "can", "could",
    "should", "shall", "may", "might", "must", "of", "in", "on", "at", "to",
    "for", "with", "about", "from", "by", "as", "into", "out", "up", "down",
    "over", "under", "again", "once", "what", "which", "who", "whom", "when",
    "where", "why", "how", "all", "any", "both", "each", "few", "more", "most",
    "other", "some", "such", "no", "nor", "not", "only", "own", "same", "than",
    "too", "s", "t", "don't", "doesn't", "didn't", "won't", "can't", "let's",
    "gonna", "wanna", "yeah", "uh", "um", "ok", "okay", "right", "well", "now",
    "say", "said", "says", "know", "think", "mean", "going", "go", "get",
    "got", "one", "thing", "stuff", "way", "kinda", "sorta", "alright",
})

_ANCHOR_WORDS = frozenset({
    "surprisingly", "surprising", "surprised", "actually", "truth", "secret",
    "nobody", "everyone", "shocking", "shock", "crazy", "unbelievable",
    "incredible", "weird", "strange", "contrary", "opposite", "myth",
    "misconception", "wrong", "different", "reveal", "revealed", "discovered",
    "discovery", "turns", "research", "study", "studies", "data", "stat",
    "stats", "statistic", "percent", "percentage", "million", "billion",
    "thousand", "only", "never", "always", "stop", "start", "worst", "best",
    "biggest", "first", "last", "problem", "mistake", "error", "fail",
    "failure", "important", "key", "huge", "massive", "dramatically",
})

_EMOTION_WORDS = frozenset({
    "love", "loved", "amazing", "awesome", "incredible", "excited", "exciting",
    "happy", "joy", "grateful", "wonderful", "fantastic", "beautiful", "proud",
    "hopeful", "inspired", "motivated", "hate", "hated", "terrible", "awful",
    "scared", "fear", "afraid", "angry", "mad", "furious", "sad", "depressed",
    "depressing", "anxious", "anxiety", "worried", "worry", "frustrated",
    "frustrating", "annoyed", "annoying", "disgusting", "gross", "crying",
    "cried", "pain", "painful", "hurt", "heartbroken", "devastated",
    "terrified", "horrible", "shocked", "surprised", "wow", "whoa",
    "unbelievable", "omg", "yikes", "gosh", "nervous", "terrifying", "crazy",
})

_CONTRADICTION_WORDS = frozenset({
    "wrong", "myth", "myths", "misconception", "contrary", "opposite", "lie",
    "lies", "lied", "truth", "assumption", "assumptions", "common", "popular",
    "turns",
})

_CURIOSITY_WORDS = frozenset({
    "why", "how", "what", "secret", "truth", "nobody", "everyone", "never",
    "imagine", "wonder", "wait", "guess", "surprising", "surprised", "shocked",
    "reveal", "revealed", "wrong", "miss", "really", "actually", "insane",
    "crazy", "believe",
})

_VAGUE_PHRASES = (
    "something", "someone", "somebody", "somewhere", "stuff", "thing",
    "things", "kinda", "maybe", "whatever", "whoever", "somehow", "a bit",
)

# Niche topic boosters — slightly favor words that match the chosen niche so
# the extracted topic phrase reads naturally for that audience.
NICHE_TOPIC_WORDS = {
    "health_fitness": {
        "health", "fitness", "workout", "protein", "muscle", "diet",
        "nutrition", "weight", "sleep", "exercise", "training", "body",
    },
    "finance_crypto": {
        "money", "invest", "investing", "investor", "crypto", "bitcoin",
        "stock", "stocks", "market", "trading", "finance", "retirement",
        "wealth", "debt", "income", "savings",
    },
    "tech_ai": {
        "ai", "technology", "software", "code", "coding", "computer", "data",
        "robot", "automation", "internet", "app", "startup", "startups",
    },
    "ecommerce": {
        "store", "shop", "selling", "seller", "amazon", "product", "products",
        "dropshipping", "customer", "brand", "ads",
    },
    "education": {
        "learn", "learning", "study", "student", "school", "course",
        "teacher", "teaching", "skill", "skills", "knowledge",
    },
    "motivation": {
        "mindset", "success", "habit", "habits", "goal", "goals", "discipline",
        "fear", "confidence", "growth", "motivation",
    },
    "food_nutrition": {
        "food", "eat", "eating", "meal", "recipe", "cooking", "sugar", "fat",
        "diet", "nutrition", "breakfast", "dinner",
    },
    "travel": {
        "travel", "trip", "destination", "hotel", "flight", "country", "visa",
        "backpack", "tourist", "airport",
    },
    "beauty_skincare": {
        "skin", "skincare", "face", "cream", "beauty", "hair", "sunscreen",
        "wrinkle", "glow", "makeup",
    },
    "productivity": {
        "time", "morning", "routine", "focus", "task", "tasks", "work",
        "schedule", "calendar", "productivity", "deep", "email",
    },
}

# Fact attribution word -> label used in the FACT hook.
_FACT_SOURCE_LABELS = {
    "research": "research",
    "study": "research",
    "studies": "research",
    "scientists": "scientists",
    "researchers": "researchers",
    "data": "the data",
    "evidence": "the evidence",
    "experts": "experts",
    "expert": "experts",
    "doctor": "doctors",
    "doctors": "doctors",
    "according to": "experts",
}


def _lemma(token: str) -> str:
    """Very light singularization so 'startup'/'startups' count together."""
    if token.endswith("s") and len(token) > 3 and not token.endswith("ss"):
        return token[:-1]
    return token


def _extract_topic(text: str, niche: str = "") -> str:
    """Extract the dominant content word (niche-boosted) from the clip."""
    tokens = [t for t in _tokenize(text) if t not in _STOPWORDS and len(t) > 2]
    if not tokens:
        return "this"
    freq = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    # Count lemmas so 'startup'/'startups' stack.
    lemma_freq = {}
    surface = {}
    for t, c in freq.items():
        key = _lemma(t)
        lemma_freq[key] = lemma_freq.get(key, 0) + c
        if key not in surface or c > freq.get(surface[key], 0):
            surface[key] = t
    niche_words = NICHE_TOPIC_WORDS.get(niche or "", ())
    for w in niche_words:
        if w in lemma_freq:
            lemma_freq[w] += 1  # small niche boost
    ranked = sorted(lemma_freq, key=lambda w: (lemma_freq[w], len(w)), reverse=True)
    if not ranked:
        return "this"
    return surface[ranked[0]]


def _sentence_interest_score(sentence: str) -> float:
    """Score how 'hookable' a sentence is (surprise/stats/emotion)."""
    words = _tokenize(sentence)
    if not words:
        return 0.0
    low = sentence.lower()
    score = 0.0
    score += len(_word_hits(sentence, _ANCHOR_WORDS)) * 2.0
    score += len(_word_hits(sentence, _EMOTION_WORDS)) * 1.5
    score += len(re.findall(r"\d", sentence)) * 2.0
    for p in ("%", "percent", "million", "billion", "times", "only ", "never ",
              "always ", "turns out"):
        if p in low:
            score += 1.5
    if len(words) > 30:
        score -= 2.0
    return score


def _extract_anchor_sentences(text: str) -> list:
    """Sentences of the clip ordered by hookiness (most interesting first)."""
    cleaned = _PLACEHOLDER_RE.sub(" ", text or "").strip()
    raw = [s.strip() for s in _SENTENCE_RE.split(cleaned)]
    sentences = [s for s in raw if len(_tokenize(s)) >= 3] or (
        [cleaned] if cleaned else [])
    scored = sorted(((_sentence_interest_score(s), s) for s in sentences),
                    key=lambda x: x[0], reverse=True)
    return [s for _, s in scored]


def _stat_match_score(num: str, unit: str, sentence: str, pos: int) -> int:
    """Score a detected number as a usable statistic (>=2 is usable)."""
    if not unit and re.fullmatch(r"\d{4}", num):
        return 0  # bare 4-digit number is almost always a year/date
    score = 0
    if unit in ("%", "percent", "million", "billion", "thousand", "m", "b",
                "k", "x", "times", "fold"):
        score += 3
    elif unit:
        score += 2  # years/days/hours/... — meaningful unit
    else:
        score += 1
    prefix = sentence[max(0, pos - 12):pos].lower()
    if re.search(
        r"(only|just|nearly|over|under|about|roughly|around|almost|"
        r"more than|less than)\s*$", prefix
    ):
        score += 1  # comparative framing makes the stat more hookable
    if "," in num or "." in num:
        score += 1
    return score


def _extract_stat(text: str) -> str | None:
    """
    Return the best verbatim statistic phrase from the clip, or None.
    Only returns phrases grounded in an actual number found in the text.
    """
    cleaned = _PLACEHOLDER_RE.sub(" ", text or "")
    best_phrase, best_score = None, 0
    for sentence in _SENTENCE_RE.split(cleaned):
        spans = list(re.finditer(r"\S+", sentence))
        for m in _STAT_NUM_RE.finditer(sentence):
            num, unit = m.group(1), (m.group(2) or "").lower()
            score = _stat_match_score(num, unit, sentence, m.start())
            if score < 2 or score <= best_score:
                continue
            start_idx = None
            for i, sp in enumerate(spans):
                if sp.start() <= m.start() < sp.end():
                    start_idx = i
                    break
            if start_idx is None:
                continue
            lo = max(0, start_idx - 4)
            hi = min(len(spans), start_idx + 5)
            phrase = " ".join(sp.group() for sp in spans[lo:hi])
            phrase = _trim_to_words(phrase, 16)
            phrase = _to_claim(phrase, max_words=16)  # strip fillers, no period
            if phrase and len(_tokenize(phrase)) >= 3:
                best_phrase, best_score = phrase, score
    return best_phrase


def _find_attribution_word(text: str) -> str | None:
    """First attribution keyword the clip itself uses, or None."""
    low = text.lower()
    for kw in ("according to", "research", "studies", "study", "scientists",
               "researchers", "data", "evidence", "experts", "expert",
               "doctors", "doctor"):
        if kw in low:
            return kw
    return None


# ─── Hook builders (all content-grounded) ─────────────────────────────────────
def _build_question(anchor: str, max_words: int = 13) -> dict:
    text = (anchor or "").strip().strip("\"'“”‘’")
    if not text:
        return {"text": "Did you know that this clip reveals something surprising?",
                "type": "question", "score": 0}
    if text.endswith("?"):
        return {"text": _trim_to_words(text, max_words), "type": "question",
                "score": 0}
    claim = _to_claim(text, max_words=max_words)
    if not claim:
        claim = _to_claim(text, max_words=max_words + 3)
    return {"text": f"Did you know that {claim}?", "type": "question", "score": 0}


def _build_statement(topic: str, has_contradiction: bool, variant: int = 0) -> dict:
    topic_disp = _display_topic(topic)
    if variant == 0:
        if has_contradiction:
            return {"text": f"Here's what most people get wrong about {topic_disp}.",
                    "type": "statement", "score": 0}
        return {"text": f"What nobody tells you about {topic_disp}.",
                "type": "statement", "score": 0}
    return {"text": f"Most people miss this about {topic_disp}.",
            "type": "statement", "score": 0}


def _build_stat(stat_phrase: str) -> dict:
    phrase = (stat_phrase or "").strip().strip("\"'“”‘’").rstrip(".,;:")
    if not phrase:
        return {"text": "The numbers in this clip will surprise you.",
                "type": "stat", "score": 0}
    if not phrase[0].isupper():
        phrase = phrase[0].upper() + phrase[1:]
    return {"text": f"{phrase}. Most people don't know this.",
            "type": "stat", "score": 0}


def _build_fact(attribution_word: str, attributed_sentence: str,
                max_words: int = 13) -> dict | None:
    """FACT hook from the sentence that actually contains the attribution."""
    claim = _to_claim(attributed_sentence, max_words=max_words)
    claim = re.sub(r"^that\s+", "", claim)
    for _ in range(2):
        m = _ATTRIBUTION_CLAUSE_RE.match(claim)
        if m:
            claim = claim[m.end():]
    claim = claim.strip()
    if len(_tokenize(claim)) < 4:
        return None  # nothing substantive left — don't force a fact
    label = _FACT_SOURCE_LABELS.get(attribution_word, "research")
    if not claim[0].isupper():
        claim = claim[0].upper() + claim[1:]
    return {"text": f"According to {label}, {claim}.",
            "type": "fact", "score": 0}


def _build_emotional(anchor_sentences: list, max_words: int = 14) -> dict | None:
    """Verbatim (trimmed) emotional sentence from the clip."""
    for s in anchor_sentences:
        if _EMOTION_WORDS & _word_hits(s, _EMOTION_WORDS):
            frag = s.strip().strip("\"'“”‘’")
            return {"text": _trim_to_words(frag, max_words),
                    "type": "emotional", "score": 0}
    return None

# ─── Public API ───────────────────────────────────────────────────────────────
def generate_hooks(clip_text: str, clip_duration: float, niche: str,
                   speaker_name: str = "") -> list:
    """
    Generate 3 content-accurate hook candidates for a clip.

    Args:
        clip_text:      transcript text of the clip candidate
        clip_duration:  clip length in seconds (used to size hooks)
        niche:          content niche key (see config.NICHES) for topic boost
        speaker_name:   optional speaker name used in fallback framing

    Returns:
        List of 3 dicts: {"text", "type", "score"}.
    """
    clip_text = (clip_text or "").strip()
    if not clip_text:
        logger.warning("generate_hooks called with empty clip_text")
        return [
            {"text": "Did you know this?", "type": "question", "score": 35},
            {"text": "You'll want to hear this one.", "type": "statement", "score": 35},
            {"text": "This clip is worth your time.", "type": "statement", "score": 30},
        ]

    duration = clip_duration or 30
    if duration <= 15:
        max_words = 10
    elif duration >= 60:
        max_words = 16
    else:
        max_words = 13

    anchors = _extract_anchor_sentences(clip_text)
    anchor = anchors[0] if anchors else clip_text
    topic = _extract_topic(clip_text, niche)
    has_contradiction = bool(_CONTRADICTION_WORDS & _word_hits(clip_text, _CONTRADICTION_WORDS))
    has_emotion = bool(_EMOTION_WORDS & _word_hits(clip_text, _EMOTION_WORDS))

    candidates = []

    # 1. QUESTION — always available, built from the strongest claim.
    candidates.append(_build_question(anchor, max_words=max_words))

    # 2. STAT — only when the clip really contains a usable number.
    stat_phrase = _extract_stat(clip_text)
    if stat_phrase:
        candidates.append(_build_stat(stat_phrase))

    # 3. FACT — only when the clip itself cites research/study/data/experts.
    attribution_word = _find_attribution_word(clip_text)
    if attribution_word:
        attributed = next(
            (s for s in anchors if attribution_word in s.lower()), anchor)
        fact = _build_fact(attribution_word, attributed, max_words=max_words)
        if fact:
            candidates.append(fact)

    # 4. EMOTIONAL — only when the clip contains real emotion words.
    if has_emotion:
        emotional = _build_emotional(anchors, max_words=max_words)
        if emotional:
            candidates.append(emotional)

    # 5. STATEMENT — always available (topic teaser).
    candidates.append(_build_statement(topic, has_contradiction, variant=0))

    # Fill to exactly 3 with grounded variants.
    filler = 0
    while len(candidates) < 3:
        filler += 1
        if filler == 1:
            candidates.append(_build_statement(topic, has_contradiction, variant=1))
        elif speaker_name and speaker_name.strip():
            candidates.append({
                "text": f"What did {speaker_name.strip()} say about {_display_topic(topic)}?",
                "type": "question", "score": 0,
            })
        elif len(anchors) > 1:
            candidates.append(_build_question(anchors[1], max_words=max_words))
        else:
            candidates.append({
                "text": f"So what's really going on with {_display_topic(topic)}?",
                "type": "question", "score": 0,
            })

    # Pick the first 3 unique hooks (dedupe exact text).
    chosen, seen = [], set()
    for h in candidates:
        key = _normalize(h["text"])
        if key in seen:
            continue
        seen.add(key)
        chosen.append(h)
        if len(chosen) == 3:
            break
    i = 0
    while len(chosen) < 3 and i < len(candidates):
        h = candidates[i]
        key = _normalize(h["text"])
        if key not in seen:
            seen.add(key)
            chosen.append(h)
        i += 1

    # Score each hook (quality + small groundedness bonuses).
    for h in chosen:
        base = analyze_hook_quality(h["text"])
        bonus = 0
        if h["type"] == "stat" and re.search(r"\d", h["text"]):
            bonus += 6  # real number quoted verbatim is highly trustworthy
        if h["type"] in ("fact", "emotional"):
            bonus += 3  # verbatim/attributed — more accurate than teasers
        h["score"] = max(0, min(100, base + bonus))

    return chosen


def analyze_hook_quality(hook_text: str) -> int:
    """
    Score a hook 0-100 across five dimensions:

        curiosity gap   (25%)  — does it make you want to know more?
        clarity         (20%)  — is it easy to understand?
        relevance       (25%)  — content specificity / groundedness
        brevity         (15%)  — concise 5-14 words
        emotional pull  (15%)  — emotional charge

    Args:
        hook_text: the hook text to score.

    Returns:
        int 0-100.
    """
    text = (hook_text or "").strip()
    if not text:
        return 0
    words = _tokenize(text)
    wc = len(words)
    if wc == 0:
        return 0
    low = text.lower()
    word_set = set(words)

    # 1. Curiosity gap — does it make you want to know more?
    curiosity = 0.0
    if _CURIOSITY_WORDS & word_set:
        curiosity += 45
    if text.rstrip().endswith("?") or "..." in text:
        curiosity += 15
    if any(p in low for p in (
        "did you know", "most people", "nobody", "everyone", "don't know",
        "no idea", "won't believe", "get wrong", "miss this", "never hear",
        "tells you", "surprising", "reveal", "truth",
    )):
        curiosity += 20
    if re.search(r"\d", text):
        curiosity += 20
    curiosity = min(100.0, curiosity)

    # 2. Clarity — is it easy to understand?
    clarity = 100.0
    if text[0].isalpha() and not text[0].isupper():
        clarity -= 10  # hooks should start with a capital letter
    avg_wlen = sum(len(w) for w in words) / wc
    if avg_wlen > 8:
        clarity -= 30
    elif avg_wlen > 6.5:
        clarity -= 12
    if wc > 18:
        clarity -= 25
    elif wc > 14:
        clarity -= 10
    if not re.search(r"[.!?][\"']?$", text.rstrip()):
        clarity -= 10
    if re.search(r"[!?]{2,}|[.,]{3,}", text):
        clarity -= 10
    clarity = max(0.0, min(100.0, clarity))

    # 3. Relevance — content specificity / groundedness (no fake claims).
    relevance = 0.0
    if re.search(r"\d", text):
        relevance += 35
    content_words = [w for w in words if w not in _STOPWORDS and len(w) > 3]
    relevance += min(40, len(set(content_words)) * 6)
    if any(v in low for v in _VAGUE_PHRASES):
        relevance -= 25
    if '"' in text or "“" in text:
        relevance += 10
    relevance = max(0.0, min(100.0, relevance))

    # 4. Brevity — concise hooks (ideal 5-14 words).
    if 5 <= wc <= 14:
        brevity = 100.0
    elif wc < 5:
        brevity = max(0.0, 100.0 - (5 - wc) * 12)
    else:
        brevity = max(0.0, 100.0 - (wc - 14) * 8)

    # 5. Emotional pull.
    emotional = 0.0
    hits = _EMOTION_WORDS & word_set
    emotional += min(60, len(hits) * 20)
    if any(p in low for p in (
        "won't believe", "don't realize", "had no idea", "shocked",
        "crazy", "insane", "changed", "surprising", "surprise", "truth",
    )):
        emotional += 25
    if text.rstrip().endswith(("?", "!")):
        emotional += 15
    emotional = min(100.0, emotional)

    total = (
        curiosity * 0.25 + clarity * 0.20 + relevance * 0.25 +
        brevity * 0.15 + emotional * 0.15
    )
    return int(round(total))


def select_best_hook(hooks: list) -> dict | None:
    """Return the highest-scored hook (ties keep the first one)."""
    if not hooks:
        return None
    best = None
    for h in hooks:
        score = h.get("score")
        if score is None:
            score = analyze_hook_quality(h.get("text", ""))
        if best is None or score > best[0]:
            best = (score, h)
    if best is None:  # unreachable when hooks is non-empty
        return None
    return best[1]


# ─── Demo / smoke test ────────────────────────────────────────────────────────
def demo() -> None:
    """Run a quick smoke test with a realistic clip transcript."""
    sample = (
        "So I was honestly shocked when I found out that only 4 percent of "
        "startups actually survive past their fifth year. Most people think "
        "the opposite, but the research is pretty clear on this. It's not "
        "about the idea, it's about the execution."
    )
    hooks = generate_hooks(sample, clip_duration=45, niche="tech_ai",
                           speaker_name="Sarah")
    print("\n=== HOOK ENGINE DEMO ===")
    for h in hooks:
        print(f"[{h['type']:>10}] ({h['score']:3d}) {h['text']}")
    best = select_best_hook(hooks)
    if best is None:
        print("\nNo hooks generated.")
        return
    print(f"\nBest hook:   {best['text']}")
    print(f"Best type:   {best['type']} (score {best['score']})")
    print(f"Quality:     {analyze_hook_quality(best['text'])}/100")

    # Accuracy check — no fabricated numbers when the clip has none.
    no_stats = (
        "We talked about building the habit of writing every single day. "
        "It's hard at first, but after a while it becomes automatic."
    )
    hooks2 = generate_hooks(no_stats, clip_duration=30, niche="productivity")
    print("\n=== NO-STAT CLIP (must contain no invented numbers) ===")
    for h in hooks2:
        print(f"[{h['type']:>10}] ({h['score']:3d}) {h['text']}")


if __name__ == "__main__":
    demo()
