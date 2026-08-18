"""
Clip Scorer — Podcast clip scoring engine.

Scores podcast clip candidates on seven dimensions (0-100 each) using
simple, deterministic heuristics — no paid AI APIs:

    hook_score        — Does it start with a strong hook?
    interest_score    — Is the content interesting/surprising?
    emotion_score     — Does it evoke emotion?
    educational_score — Is it educational/useful?
    context_score     — Does it make sense standalone?
    viral_score       — Is it shareable?
    ending_score      — Does it end well?

Final score = weighted average of the seven dimensions (0-100).

Rejection rules (reject_bad_candidates):
    * context_score < 30            — starts without context
    * context_score < 40            — depends on missing previous conversation
    * ending_score < 20             — ends abruptly
    * silence ratio > 30%           — excessive silence
    * unintelligible audio          — too little / garbled speech
    * duplicate of another clip     — near-identical content
    * safety check failed           — profanity / harmful content
    * final score < min_total       — below quality threshold

Preferred clips (rewarded via scoring, not hard rejects):
    strong opening (hook > 70), standalone meaning (context > 60),
    surprising insight (interest > 70), emotional reaction (emotion > 60),
    useful information (educational > 60), clear ending (ending > 60).

Transcript segment format matches tools/transcriber.py:
    {"start": float, "end": float, "text": str}

Silence ratio is measured with ffmpeg silencedetect when an audio file is
provided (cached per clip window); otherwise it falls back to gaps between
transcript segments.
"""
import logging
import os
import re
import subprocess
import tempfile

logger = logging.getLogger("clip_scorer")

# ─── Weights for the final weighted average ───────────────────────────────────
SCORE_WEIGHTS = {
    "hook": 0.20,
    "interest": 0.15,
    "emotion": 0.10,
    "educational": 0.15,
    "context": 0.10,
    "viral": 0.20,
    "ending": 0.10,
}
SCORE_KEYS = [
    "hook_score", "interest_score", "emotion_score",
    "educational_score", "context_score", "viral_score", "ending_score",
]

# ─── Lexicons (tokens matched against the lowercase word set) ─────────────────
STRONG_HOOK_WORDS = frozenset({
    "you", "your", "imagine", "watch", "listen", "look", "wait", "guess",
    "believe", "why", "how", "what", "never", "always", "stop", "start",
    "remember", "secret", "truth", "nobody", "everyone", "biggest", "best",
    "worst", "crazy", "warning", "here's", "there's", "this is",
})

INTEREST_WORDS = frozenset({
    "surprisingly", "surprising", "surprised", "actually", "truth", "secret",
    "nobody", "everyone", "shocking", "shock", "crazy", "unbelievable",
    "incredible", "weird", "strange", "contrary", "opposite", "myth",
    "misconception", "lies", "lied", "wrong", "different", "reveal",
    "revealed", "discovered", "discovery", "turns", "turns out", "research",
    "study", "studies", "data", "stat", "stats", "statistic", "statistics",
    "percent", "percentage", "numbers", "billions", "millions",
})

EMOTION_WORDS = frozenset({
    # positive
    "love", "loved", "amazing", "awesome", "incredible", "excited", "excitement",
    "happy", "joy", "grateful", "wonderful", "fantastic", "beautiful", "proud",
    "hopeful", "inspired", "motivated", "grateful",
    # negative
    "hate", "hated", "terrible", "awful", "scared", "fear", "afraid", "angry",
    "mad", "furious", "sad", "depressed", "depressing", "anxious", "anxiety",
    "worried", "worry", "frustrated", "frustrating", "annoyed", "annoying",
    "disgusting", "gross", "crying", "cried", "pain", "painful", "hurt",
    "heartbroken", "devastated", "terrified", "horrible", "hate",
    # surprise / interjection
    "wow", "whoa", "shocked", "surprised", "unbelievable", "omg", "jeez",
    "yikes", "oh", "ah", "huh", "no way", "gosh",
})

STRONG_EMOTION_WORDS = frozenset({
    "love", "hate", "crying", "terrible", "amazing", "devastated",
    "terrified", "incredible", "heartbroken", "furious", "fear",
})

EDUCATIONAL_WORDS = frozenset({
    "how", "why", "because", "reason", "research", "study", "studies",
    "science", "data", "evidence", "fact", "facts", "statistics", "statistic",
    "percent", "percentage", "important", "key", "tip", "tips", "trick",
    "tricks", "method", "strategy", "strategies", "technique", "step", "steps",
    "process", "example", "examples", "learn", "learning", "understand",
    "explain", "explains", "explained", "means", "mean", "actually",
    "basically", "essentially", "remember", "lesson", "principle", "rule",
    "rules", "cause", "effect", "benefit", "benefits", "advantage",
    "result", "results", "outcome", "proven", "recommended", "recommendation",
})

VIRAL_WORDS = frozenset({
    "you", "your", "nobody", "everyone", "people", "secret", "truth", "why",
    "how", "what", "never", "always", "stop", "start", "biggest", "best",
    "worst", "first", "last", "only", "free", "new", "now", "today",
    "instant", "guaranteed", "hack", "hacks", "life-changing", "game changer",
    "shocking", "crazy", "unbelievable", "controversial", "proven", "powerful",
    "easy", "simple", "fast", "quick", "million", "billion", "millionaire",
    "billionaire", "percent", "number", "dollar", "money", "success",
})

# First token that implies the clip continues an earlier thought.
CONTINUATION_OPENERS = frozenset({
    "and", "but", "because", "which", "if", "when", "then", "since", "though",
    "although", "while", "or", "however",
})

# Third-person openers usually refer to someone introduced earlier.
STRONG_PRONOUN_OPENERS = frozenset({"he", "she", "they", "his", "her", "their"})
WEAK_PRONOUN_OPENERS = frozenset({"it", "this", "that", "these", "those", "there"})

# Last token that suggests the clip was cut mid-thought.
DANGLING_TAIL = frozenset({
    "and", "but", "so", "because", "or", "the", "a", "an", "of", "in", "with",
    "to", "for", "on", "at", "by", "that", "which",
})

# Natural conversational conclusions (only a bonus when a sentence ends).
CLOSING_WORDS = frozenset({
    "yeah", "right", "exactly", "anyway", "there", "done", "basically",
    "period", "so", "fine", "great", "perfect",
})

# Safety: profanity, slurs, exploitation, violence/self-harm, illegal acts.
# Educational mentions of hard drugs will be flagged — configurable per policy.
SAFETY_BLOCKLIST = frozenset({
    # profanity
    "fuck", "fucking", "fucked", "shit", "shitting", "bitch", "asshole",
    "bastard", "cunt", "dick", "pussy", "slut", "whore", "bullshit",
    # slurs
    "nigger", "faggot", "retard", "retarded", "chink", "spic",
    # exploitation / sexual abuse
    "rape", "raped", "rapist", "molest", "molested", "pedophile", "pedo",
    "child porn", "cp",
    # violence / self-harm
    "suicide", "kill yourself", "kill urself", "self harm", "self-harm",
    "cutting myself", "bomb", "explosive", "school shooting", "massacre",
    "terrorist", "beheading", "murder", "murdered", "kidnap", "kidnapped",
    "torture", "tortured",
    # hard drugs / illegal substances
    "cocaine", "heroin", "meth", "methamphetamine", "fentanyl", "crack",
    "oxycontin", "crystal meth",
})

# ─── Regex helpers ────────────────────────────────────────────────────────────
_PLACEHOLDER_RE = re.compile(r"\[.*?\]|\(.*?\)|♪|♪|\*\*+")
_STAT_RE = re.compile(r"\d|[$%]")

_SILENCE_CACHE = {}  # (audio_path, start, end) -> silence ratio or None


# ─── Text helpers ─────────────────────────────────────────────────────────────
def _tokenize(text: str) -> list:
    """Lowercase word tokens, keeping numbers and apostrophes (here's)."""
    return re.findall(r"[a-z0-9']+", text.lower())


def _normalize_text(text: str) -> str:
    """Folded text for comparison: lowercase, punctuation stripped, spaces."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", text.lower())).strip()


def _word_hits(text: str, wordlist: frozenset) -> set:
    """Unique tokens of `text` that appear in `wordlist`."""
    tokens = set(_tokenize(text))
    return tokens & wordlist


def _first_sentence(text: str) -> str:
    """First sentence of the text, including its terminal punctuation."""
    match = re.search(r".*?[.!?]", text)
    if match:
        return match.group(0)
    return text[:120]


def _has_terminal_punctuation(text: str) -> bool:
    return bool(re.search(r"[.!?][\"']?$", text.strip()))


def _has_stat(text: str) -> bool:
    return bool(_STAT_RE.search(text)) or any(
        w in text.lower() for w in ("million", "billion", "percent", "percentage")
    )


def _continuation_penalty(text: str) -> int:
    """Penalty when the clip starts by continuing an earlier thought."""
    tokens = _tokenize(text)
    if not tokens:
        return 0
    first = tokens[0]
    if first in ("so", "and", "but"):
        # "so here's the thing" is a fine standalone opener.
        if len(tokens) > 1 and tokens[1] in ("here's", "this", "the"):
            return 0
    if first in CONTINUATION_OPENERS:
        return 12
    if first in STRONG_PRONOUN_OPENERS:
        return 12
    if first in WEAK_PRONOUN_OPENERS:
        return 6
    return 0


def _dangling_tail_penalty(text: str) -> int:
    """Penalty when the clip ends mid-thought (cut before completing a phrase)."""
    tokens = _tokenize(text)
    if not tokens:
        return 20
    last = tokens[-1]
    if last not in DANGLING_TAIL:
        return 0
    return 20 if not _has_terminal_punctuation(text) else 10


def _closing_bonus(text: str) -> int:
    """Bonus when the clip ends on a natural conclusion."""
    tokens = _tokenize(text)
    if not tokens:
        return 0
    if tokens[-1] in CLOSING_WORDS and _has_terminal_punctuation(text):
        return 10
    return 0


# ─── Duration / density helpers ───────────────────────────────────────────────
def _duration_score(duration: float, ideal_lo: float, ideal_hi: float,
                    hard_min: float, hard_max: float) -> float:
    """
    Triangular score: 0 outside [hard_min, hard_max], ramps to 100 across the
    ideal window, 100 inside it.
    """
    if duration <= hard_min or duration >= hard_max:
        return 0.0
    if duration < ideal_lo:
        return 100.0 * (duration - hard_min) / (ideal_lo - hard_min)
    if duration <= ideal_hi:
        return 100.0
    return 100.0 * (hard_max - duration) / (hard_max - ideal_hi)


def _density_score(wps: float) -> float:
    """Speech-density quality (words/second) — 0-100."""
    if wps <= 0.5:
        return 0.0
    if wps < 1.2:
        return 30.0 * (wps - 0.5) / 0.7
    if wps <= 1.8:
        return 30.0 + 50.0 * (wps - 1.2) / 0.6
    if wps <= 3.0:
        return 80.0 + 20.0 * (wps - 1.8) / 1.2
    if wps <= 4.2:
        return 100.0 - 30.0 * (wps - 3.0) / 1.2
    return 70.0 - 40.0 * min(wps - 4.2, 2.0) / 2.0


# ─── Position in transcript ───────────────────────────────────────────────────
def _position_zone(start: float, total_duration: float) -> str:
    if total_duration <= 0:
        return "middle"
    frac = start / total_duration
    if frac < 0.15:
        return "beginning"
    if frac > 0.75:
        return "end"
    return "middle"


# ─── Silence measurement ──────────────────────────────────────────────────────
def _ffmpeg_silence_ratio(audio_path: str | None, start: float, end: float):
    """
    Measure the silence ratio of [start, end] in `audio_path` with ffmpeg
    silencedetect. Returns None when measurement is not possible.
    """
    if not audio_path or not os.path.exists(audio_path):
        return None
    key = (audio_path, round(start, 3), round(end, 3))
    if key in _SILENCE_CACHE:
        return _SILENCE_CACHE[key]

    duration = max(end - start, 0.1)
    ratio = None
    tmp_path = None
    try:
        # 1) Extract the clip window to a temp wav so silencedetect timestamps
        #    are relative to the clip start (robust across ffmpeg versions).
        fd, tmp_path = tempfile.mkstemp(suffix=".wav", prefix="clip_scorer_")
        os.close(fd)
        extract = subprocess.run(
            ["ffmpeg", "-y", "-ss", str(start), "-t", str(duration), "-i",
             audio_path, "-vn", "-ac", "1", "-ar", "16000", tmp_path],
            capture_output=True, text=True, timeout=30,
        )
        if extract.returncode != 0 or not os.path.exists(tmp_path):
            return None

        # 2) Detect silences inside the extracted clip.
        detect = subprocess.run(
            ["ffmpeg", "-i", tmp_path,
             "-af", "silencedetect=noise=-30dB:d=0.5",
             "-f", "null", "-"],
            capture_output=True, text=True, timeout=60,
        )
        silence_starts = []
        silence_ends = []
        for line in detect.stderr.splitlines():
            m = re.search(r"silence_start:\s*([\d.]+)", line)
            if m:
                silence_starts.append(float(m.group(1)))
                continue
            m = re.search(r"silence_end:\s*([\d.]+)", line)
            if m:
                silence_ends.append(float(m.group(1)))

        total_silence = 0.0
        for s in silence_starts:
            e = min(duration, 2**31 - 1)
            # Pair each start with the next end (or clip end).
            e = next((x for x in silence_ends if x > s), duration)
            total_silence += max(0.0, min(e, duration) - max(s, 0.0))
        ratio = min(total_silence / duration, 1.0)
    except Exception as exc:  # ffmpeg missing / timeout / bad file
        logger.debug(f"Silence measurement failed: {exc}")
        ratio = None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    _SILENCE_CACHE[key] = ratio
    return ratio


def _gap_silence_ratio(window_segments: list, start: float, end: float) -> float:
    """Fallback: silence ratio derived from gaps between transcript segments."""
    if not window_segments:
        return 0.0
    duration = max(end - start, 0.1)
    total_gap = 0.0
    prev = start
    for seg in sorted(window_segments, key=lambda s: s["start"]):
        gap = seg["start"] - prev
        if gap > 0:
            total_gap += gap
        prev = max(prev, seg["end"])
    total_gap += max(end - prev, 0.0)
    return min(total_gap / duration, 1.0)


# ─── Transcript normalization ─────────────────────────────────────────────────
def _normalize_transcript(transcript):
    """
    Accept a transcript as a list of segment dicts (transcriber.py format),
    list of (start, end, text) tuples, or a plain text string.
    Returns (segments, total_duration).
    """
    if isinstance(transcript, str):
        est = max(len(transcript.split()) / 2.5, 10.0)
        return [{"start": 0.0, "end": est, "text": transcript}], est

    segments = []
    total = 0.0
    for seg in transcript or []:
        if isinstance(seg, dict):
            start = float(seg.get("start", 0))
            end = float(seg.get("end", start))
            text = str(seg.get("text", ""))
        elif isinstance(seg, (list, tuple)) and len(seg) >= 3:
            start, end, text = float(seg[0]), float(seg[1]), str(seg[2])
        else:
            continue
        if text.strip():
            segments.append({"start": start, "end": end, "text": text})
            total = max(total, end)
    return segments, (total if total > 0 else 1.0)


# ─── Safety check ─────────────────────────────────────────────────────────────
def _safety_check(text: str) -> dict:
    """Block profanity, slurs, exploitation, violence/self-harm, illegal acts."""
    folded = " " + _normalize_text(text).replace("-", " ") + " "
    hits = []
    for term in sorted(SAFETY_BLOCKLIST):
        probe = term if " " in term else f" {term} "
        if probe in folded:
            hits.append(term)
    if hits:
        return {"safe": False, "reason": "blocked term(s): " + ", ".join(hits), "hits": hits}
    return {"safe": True, "reason": "", "hits": []}


# ─── Intelligibility check ────────────────────────────────────────────────────
def _intelligibility(text: str, word_count: int, wps: float) -> bool:
    """Heuristic: enough real speech, reasonable density, few placeholder tags."""
    placeholder_ratio = len(_PLACEHOLDER_RE.findall(text)) / max(word_count, 1)
    return word_count >= 8 and wps >= 0.9 and placeholder_ratio <= 0.4


# ─── Core analysis ────────────────────────────────────────────────────────────
def _clamp(value: float) -> int:
    return max(0, min(100, int(round(value))))


def _analyze(start: float, end: float, segments: list, total_duration: float,
             audio_path: str | None = None, forced_text: str | None = None) -> dict:
    """Shared analysis used by analyze_segment and score_all_candidates."""
    start = float(start)
    end = float(end)
    duration = max(end - start, 0.1)

    if forced_text is not None and forced_text.strip():
        text = forced_text.strip()
        window = [s for s in segments if s["start"] < end and s["end"] > start]
        # Keep segments for silence fallback; force_text overrides content.
        word_count = len(_tokenize(text))
        gap_before = 0.0
        gap_after = 0.0
    else:
        window = [s for s in segments if s["start"] < end and s["end"] > start]
        text = " ".join(s["text"] for s in window).strip()
        word_count = len(_tokenize(text))
        gap_before = max(window[0]["start"] - start, 0.0) if window else duration
        gap_after = max(end - window[-1]["end"], 0.0) if window else duration

    wps = word_count / duration
    zone = _position_zone(start, total_duration)

    # Silence ratio: ffmpeg ground truth, transcript gaps as fallback.
    silence_ratio = _ffmpeg_silence_ratio(audio_path, start, end)
    if silence_ratio is None:
        silence_ratio = _gap_silence_ratio(window, start, end)

    intelligible = _intelligibility(text, word_count, wps)

    # ── hook_score ────────────────────────────────────────────────────────────
    hook = 30.0
    first_sentence = _first_sentence(text)
    first_tokens = _tokenize(text)[:6]
    if "?" in first_sentence:
        hook += 25.0
    if "!" in first_sentence:
        hook += 10.0
    if _has_stat(first_sentence):
        hook += 15.0
    if STRONG_HOOK_WORDS.intersection(first_tokens):
        hook += 15.0
    if gap_before <= 2.5:
        hook += 10.0          # speech starts immediately
    else:
        hook -= 10.0          # dead air at the open
    hook += 10.0 * _duration_score(duration, 20, 45, 8, 90) / 100.0

    # ── interest_score ────────────────────────────────────────────────────────
    interest = 30.0
    interest += min(30.0, 4.0 * len(_word_hits(text, INTEREST_WORDS)))
    if _has_stat(text):
        interest += 15.0
    if "?" in text:
        interest += 10.0
    if any(w in _tokenize(text) for w in ("but", "however", "yet", "instead")):
        interest += 10.0
    if 0.9 <= wps <= 4.5:
        interest += 5.0

    # ── emotion_score ─────────────────────────────────────────────────────────
    emotion = 20.0
    emotion += min(50.0, 6.0 * len(_word_hits(text, EMOTION_WORDS)))
    emotion += min(15.0, 5.0 * len(_word_hits(text, STRONG_EMOTION_WORDS)))
    emotion += min(10.0, 5.0 * text.count("!"))
    if any(w in text.lower() for w in ("wow", "whoa", "oh", "no way", "omg")):
        emotion += 10.0

    # ── educational_score ─────────────────────────────────────────────────────
    educational = 25.0
    educational += min(40.0, 4.0 * len(_word_hits(text, EDUCATIONAL_WORDS)))
    if _has_stat(text):
        educational += 15.0
    # question followed by a substantive answer (education pattern)
    if "?" in text:
        after_q = text.split("?", 1)[1] if "?" in text else ""
        if len(_tokenize(after_q)) >= 6:
            educational += 10.0
    if any(w in _tokenize(text) for w in ("because", "why", "how", "means", "mean")):
        educational += 10.0
    if any(w in _tokenize(text) for w in ("first", "second", "step", "key", "important")):
        educational += 5.0

    # ── context_score ─────────────────────────────────────────────────────────
    context = 45.0
    if word_count >= 30:
        context += 10.0
    if _has_terminal_punctuation(text):
        context += 10.0
    if zone == "beginning":
        context += 15.0
    elif zone == "end":
        context += 5.0
    if 0.9 <= wps <= 4.5:
        context += 5.0
    context -= _continuation_penalty(text)
    if word_count < 8:
        context -= 25.0

    # ── ending_score ──────────────────────────────────────────────────────────
    ending = 40.0
    if _has_terminal_punctuation(text):
        ending += 25.0
    else:
        ending -= 10.0
    ending -= _dangling_tail_penalty(text)
    ending += _closing_bonus(text)
    trailing_ratio = gap_after / duration
    if gap_after <= 2.0:
        ending += 15.0
    elif trailing_ratio > 0.15:
        ending -= 15.0
    if duration >= 20:
        ending += 5.0

    # ── viral_score ───────────────────────────────────────────────────────────
    viral = calculate_viral_score(text, duration)

    scores = {
        "hook_score": _clamp(hook),
        "interest_score": _clamp(interest),
        "emotion_score": _clamp(emotion),
        "educational_score": _clamp(educational),
        "context_score": _clamp(context),
        "viral_score": viral,
        "ending_score": _clamp(ending),
    }
    final_score = round(
        sum(SCORE_WEIGHTS[k] * scores[f"{k}_score"] for k in SCORE_WEIGHTS), 2
    )

    return {
        "start": round(start, 2),
        "end": round(end, 2),
        "duration": round(duration, 2),
        "text": text,
        "word_count": word_count,
        "word_density": round(wps, 2),
        "silence_ratio": round(silence_ratio, 3),
        "intelligible": intelligible,
        "position": zone,
        "scores": scores,
        "final_score": final_score,
    }


# ─── Public API ───────────────────────────────────────────────────────────────
def analyze_segment(start: float, end: float, transcript_segments: list,
                    audio_path: str | None = None) -> dict:
    """
    Score a single clip candidate defined by [start, end] seconds.

    Args:
        start: clip start time (seconds)
        end: clip end time (seconds)
        transcript_segments: list of {"start", "end", "text"} dicts
            (transcriber.py format) covering the full episode
        audio_path: path to the episode audio/video (optional; used for
            ffmpeg silence measurement, falls back to transcript gaps)

    Returns:
        dict with the seven scores, final_score and analysis metadata.
    """
    segments, total_duration = _normalize_transcript(transcript_segments)
    return _analyze(start, end, segments, total_duration, audio_path)


def score_all_candidates(candidates: list, transcript, audio_path: str | None = None) -> list:
    """
    Score every clip candidate and return them sorted by final_score (best first).

    Args:
        candidates: list of dicts with "start" and "end" (seconds); an
            optional "text" key overrides the transcript text for that clip.
        transcript: episode transcript — list of segment dicts, list of
            (start, end, text) tuples, or plain text.
        audio_path: optional episode audio file for silence measurement.

    Returns:
        Sorted list of scored candidate dicts (see analyze_segment).
    """
    segments, total_duration = _normalize_transcript(transcript)
    if total_duration <= 1.0:
        # Plain-text transcripts carry no timeline; use candidate end times.
        total_duration = max((float(c.get("end", 0)) for c in candidates), default=0.0)

    scored = []
    for cand in candidates:
        start = cand.get("start")
        end = cand.get("end")
        if start is None or end is None:
            logger.warning("Skipping candidate without start/end: %s", cand)
            continue
        result = _analyze(
            float(start), float(end), segments, total_duration,
            audio_path, forced_text=cand.get("text"),
        )
        scored.append(result)

    scored.sort(key=lambda r: r["final_score"], reverse=True)
    return scored


def _is_duplicate(text: str, start: float, approved: list) -> bool:
    """Near-identical content or near-identical clip window => duplicate."""
    folded = _normalize_text(text)
    tokens = set(folded.split())
    for other in approved:
        if abs(other["start"] - start) < 3.0:
            return True
        other_folded = _normalize_text(other.get("text", ""))
        other_tokens = set(other_folded.split())
        if not folded or not other_folded:
            continue
        if len(tokens) < 6 or len(other_tokens) < 6:
            if folded == other_folded:
                return True
            continue
        overlap = len(tokens & other_tokens) / max(len(tokens), len(other_tokens))
        if overlap > 0.85:
            return True
    return False


def _evaluate_candidate(cand: dict, approved: list, min_total: float) -> list:
    """Return rejection reasons for one candidate (empty = approvable)."""
    reasons = []
    s = cand.get("scores", {})

    if s.get("context_score", 0) < 30:
        reasons.append(f"starts without context (context_score={s.get('context_score')} < 30)")
    if s.get("context_score", 0) < 40:
        reasons.append(f"depends on missing previous conversation (context_score={s.get('context_score')} < 40)")
    if s.get("ending_score", 0) < 20:
        reasons.append(f"ends abruptly (ending_score={s.get('ending_score')} < 20)")

    silence = cand.get("silence_ratio", 0.0)
    if silence > 0.30:
        reasons.append(f"excessive silence ({silence * 100:.0f}% > 30%)")

    if not cand.get("intelligible", True):
        reasons.append("unintelligible audio (too few words / low density)")

    safety = _safety_check(cand.get("text", ""))
    if not safety["safe"]:
        reasons.append(f"failed safety check ({safety['reason']})")

    if _is_duplicate(cand.get("text", ""), cand.get("start", 0.0), approved):
        reasons.append("duplicate of an approved candidate")

    if cand.get("final_score", 0) < min_total:
        reasons.append(
            f"below minimum total score ({cand.get('final_score')} < {min_total})"
        )

    return reasons


def reject_bad_candidates(scored_candidates: list, min_total: float = 40) -> list:
    """
    Apply all rejection rules and return the approved candidates.

    Rejects: missing context (<30 / <40), abrupt endings (<20), excessive
    silence (>30%), unintelligible audio, duplicates, safety-check failures,
    and candidates whose final score is below `min_total`.

    Each returned candidate carries its scores plus a "rejection_reasons"
    list (empty for approved clips).
    """
    approved = []
    for cand in scored_candidates:
        reasons = _evaluate_candidate(cand, approved, min_total)
        entry = dict(cand)
        entry["rejection_reasons"] = reasons
        if not reasons:
            approved.append(entry)

    return approved


def calculate_viral_score(text: str, duration: float = 0) -> int:
    """
    Viral/shareability score (0-100) from content analysis of the clip text.

    Signals: direct address, share triggers ("nobody", "secret", "truth"),
    questions, exclamations, numbers/stats, and the optimal 20-45s clip length.
    """
    if not text or not text.strip():
        return 0

    viral = 25.0
    tokens = _tokenize(text)

    viral += min(30.0, 3.0 * len(_word_hits(text, VIRAL_WORDS)))
    if "?" in text:
        viral += 12.0
    if "!" in text:
        viral += 8.0
    if _has_stat(text):
        viral += 12.0

    share_triggers = {
        "nobody", "everyone", "secret", "truth", "why", "never", "stop",
        "biggest", "worst", "best", "hack", "guaranteed", "proven", "only",
    }
    viral += min(20.0, 8.0 * len(set(tokens) & share_triggers))
    if "you" in tokens or "your" in tokens:
        viral += 10.0

    if duration > 0:
        if 20 <= duration <= 45:
            viral += 10.0
        elif duration > 75:
            viral -= 10.0
        elif duration < 10:
            viral -= 15.0

    return _clamp(viral)


# ─── Demo / self-test ─────────────────────────────────────────────────────────
def demo() -> None:
    """Synthetic end-to-end run (no ffmpeg needed; uses transcript gaps)."""
    segments = [
        {"start": 0.0, "end": 4.0, "text": "Welcome back to the show, everyone."},
        {"start": 4.0, "end": 9.0, "text": "Today we answer a surprising question."},
        {"start": 9.0, "end": 13.0, "text": "Why do most startups fail within 3 years?"},
        {"start": 13.0, "end": 17.0, "text": "The data says it is not the idea."},
        {"start": 17.0, "end": 22.0, "text": "It is the strategy, and I can prove it."},
        {"start": 22.0, "end": 26.0, "text": "Here is the one thing nobody tells you."},
        {"start": 26.0, "end": 30.0, "text": "You have to test before you build."},
        {"start": 30.0, "end": 34.0, "text": "That is the secret to everything."},
        {"start": 34.0, "end": 38.0, "text": "Amazing, right? I love that insight."},
        {"start": 38.0, "end": 42.0, "text": "Anyway, that is how we do it."},
        {"start": 60.0, "end": 64.0, "text": "And he said that the market was"},
        {"start": 64.0, "end": 68.0, "text": "ready, so we decided to"},
        {"start": 68.0, "end": 72.0, "text": "launch it anyway, and"},
    ]

    candidates = [
        {"start": 4.0, "end": 30.0},    # strong: question + stats + secret + ending
        {"start": 60.0, "end": 75.0},   # weak: continuation opener, dangling tail
        {"start": 4.0, "end": 30.0},    # duplicate of the strong one
        {"start": 40.0, "end": 90.0},   # silent: big transcript gap, short text
    ]

    print("=" * 62)
    print("CLIP SCORER DEMO")
    print("=" * 62)
    scored = score_all_candidates(candidates, segments)
    for i, c in enumerate(scored, 1):
        print(f"\n#{i} [{c['start']:.0f}s-{c['end']:.0f}s] final={c['final_score']} "
              f"pos={c['position']} silence={c['silence_ratio']:.0%} "
              f"intelligible={c['intelligible']}")
        print(f"   text: {c['text'][:70]!r}")
        print("   scores:", ", ".join(f"{k}={v}" for k, v in c["scores"].items()))

    print("\n" + "=" * 62)
    print("REJECTION PASS (min_total=40)")
    print("=" * 62)
    rejected_count = len(scored) - len(reject_bad_candidates(scored))
    approved_running = []
    for c in scored:
        reasons = _evaluate_candidate(c, approved_running, 40)
        status = "APPROVED" if not reasons else "REJECTED"
        print(f"\n[{status}] final={c['final_score']} {c['start']:.0f}s-{c['end']:.0f}s")
        for r in reasons:
            print(f"   - {r}")
        if not reasons:
            approved_running.append(c)
    print(f"\nApproved: {len(scored) - rejected_count} of {len(scored)} candidates")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo()
