"""
Sentiment analysis using VADER (no API key needed).
Also extracts top issues from reviews.
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from collections import Counter

analyzer = SentimentIntensityAnalyzer()

# Common issue keywords to detect
ISSUE_KEYWORDS = {
    "delivery delay":       ["delay", "late", "slow delivery", "not delivered", "shipping"],
    "bad quality":          ["quality", "cheap", "broke", "damaged", "defective", "fragile"],
    "poor battery":         ["battery", "drain", "charge", "power"],
    "overpriced":           ["expensive", "overpriced", "not worth", "costly", "price"],
    "bad customer service": ["customer service", "support", "refund", "return", "response"],
    "fake product":         ["fake", "duplicate", "original", "genuine", "not original"],
    "packaging issue":      ["packaging", "box", "packing", "wrapper"],
    "size/fit issue":       ["size", "fit", "small", "large", "fitting"],
    "display/screen":       ["screen", "display", "resolution", "brightness", "pixel"],
    "heating issue":        ["heat", "hot", "overheat", "warm"],
}


def classify_review(text: str) -> str:
    """Return 'positive', 'negative', or 'neutral'."""
    score = analyzer.polarity_scores(text)["compound"]
    if score >= 0.05:
        return "positive"
    elif score <= -0.05:
        return "negative"
    return "neutral"


def extract_issues(reviews: list[str]) -> list[str]:
    """Find the most mentioned issues from negative and neutral reviews only."""
    issue_counts = Counter()

    # Only scan non-positive reviews so we don't flag praise as issues
    negative_neutral = [r for r in reviews if classify_review(r) != "positive"]

    # Fall back to all reviews if everything is positive
    source_text = negative_neutral if negative_neutral else reviews
    all_text = " ".join(source_text).lower()

    for issue, keywords in ISSUE_KEYWORDS.items():
        for kw in keywords:
            if kw in all_text:
                issue_counts[issue] += all_text.count(kw)
                break

    return [f"{issue.title()} (mentioned frequently)" for issue, _ in issue_counts.most_common(4)]


def analyze_sentiment(reviews: list[str]) -> dict:
    """
    Analyse a list of review strings.
    Returns: { positive, negative, neutral (%), score, top_issues }
    """
    if not reviews:
        return {"positive": 0, "negative": 0, "neutral": 0, "score": 0, "top_issues": []}

    labels = [classify_review(r) for r in reviews]
    total = len(labels)
    pos = round(labels.count("positive") / total * 100)
    neg = round(labels.count("negative") / total * 100)
    neu = 100 - pos - neg

    # Overall score: neutral counts partially positive
    score = round(pos + neu * 0.4)
    score = min(score, 100)

    issues = extract_issues(reviews)
    return {
        "positive": pos,
        "negative": neg,
        "neutral":  neu,
        "score":    score,
        "top_issues": issues if issues else ["No major issues detected 🎉"],
    }


def get_combined_score(all_reviews: list[str]) -> dict:
    """Same as analyze_sentiment but labelled for combined dashboard."""
    return analyze_sentiment(all_reviews)
