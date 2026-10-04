"""
Lightweight sentiment analysis.

How it works (simple on purpose):
1. TextBlob gives a polarity score between -1 (negative) and +1 (positive).
2. A small list of campus-feedback words/phrases nudges the score, because general
   purpose lexicons miss words like "outdated" or "needs improvement".
3. The final score is turned into a label:
       score >=  0.10  -> Positive
       score <= -0.10  -> Negative
       otherwise       -> Neutral

This is NOT a trained AI model. It is a rule/lexicon approach and can be wrong,
especially with sarcasm or very short comments.
If TextBlob is not installed, the keyword lists alone are used.
"""
import re

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except Exception:  # library missing or broken: fall back to keywords only
    TEXTBLOB_AVAILABLE = False

POSITIVE_WORDS = {
    "excellent", "great", "good", "amazing", "helpful", "enjoyed", "enjoy", "clear", "clearly",
    "friendly", "clean", "best", "engaging", "supportive", "wonderful", "fantastic", "love",
    "loved", "outstanding", "awesome", "satisfied", "impressive", "interesting", "perfect",
    "well-organized", "organised", "organized", "informative", "comfortable", "tasty",
    "fresh", "modern", "brilliant", "inspiring", "polite", "recommend", "thank", "thanks",
}
NEGATIVE_WORDS = {
    "bad", "poor", "worst", "terrible", "awful", "boring", "dirty", "slow", "broken", "old",
    "outdated", "unhygienic", "crowded", "overpriced", "uncomfortable", "insufficient",
    "lack", "lacking", "rude", "unhelpful", "confusing", "late", "delayed", "noisy",
    "disappointed", "disappointing", "unsafe", "limited", "irregular", "expensive",
    "problem", "problems", "issue", "issues", "waste", "complaint", "worse", "unclear",
    "faulty", "damaged", "stale", "smelly", "leaking",
}
NEGATIVE_PHRASES = [
    "needs improvement", "need improvement", "needs to improve", "not working", "not enough",
    "not clean", "not satisfied", "not helpful", "too old", "too crowded", "too slow",
    "does not work", "doesn't work", "hard to understand", "no proper", "must be improved",
    "should be improved", "needs repair", "need repair",
]
NEUTRAL_WORDS = {"okay", "ok", "average", "fine", "normal", "decent", "moderate",
                 "alright", "so-so", "fair", "acceptable"}

POSITIVE_THRESHOLD = 0.10
NEGATIVE_THRESHOLD = -0.10


def analyze_sentiment(text):
    """Return (label, score) for a feedback comment."""
    text = (text or "").strip()
    if not text:
        return "Neutral", 0.0

    lowered = text.lower()
    words = re.findall(r"[a-z][a-z'\-]*", lowered)

    pos_hits = sum(1 for w in words if w in POSITIVE_WORDS)
    neg_hits = sum(1 for w in words if w in NEGATIVE_WORDS)
    neg_hits += sum(lowered.count(p) for p in NEGATIVE_PHRASES)
    neutral_hits = sum(1 for w in words if w in NEUTRAL_WORDS)

    base = TextBlob(text).sentiment.polarity if TEXTBLOB_AVAILABLE else 0.0

    # "okay / average" style comments with no strong words stay neutral
    if neutral_hits and pos_hits == 0 and neg_hits == 0:
        score = base * 0.1
    else:
        score = base + 0.2 * (pos_hits - neg_hits)
        # simple negation handling for "not good", "not great", ...
        if re.search(r"\b(not|never|no)\s+(very\s+)?(good|great|helpful|clean|clear|satisfied|enough)", lowered):
            score = min(score, -0.2)

    score = max(-1.0, min(1.0, score))
    score = round(score, 3)

    if score >= POSITIVE_THRESHOLD:
        label = "Positive"
    elif score <= NEGATIVE_THRESHOLD:
        label = "Negative"
    else:
        label = "Neutral"
    return label, score
