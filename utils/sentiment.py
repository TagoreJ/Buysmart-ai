"""
Enhanced sentiment analysis using VADER.
Provides per-sentence classification, issue/positive extraction,
compound score distribution, and aspect-based scoring.
"""
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from collections import Counter

analyzer = SentimentIntensityAnalyzer()

ISSUE_KEYWORDS = {
    "Delivery Delay":       ["delay", "late", "slow delivery", "not delivered", "shipping"],
    "Build Quality":        ["quality", "cheap", "broke", "damaged", "defective", "fragile", "build"],
    "Poor Battery":         ["battery", "drain", "charge", "power", "mah"],
    "Overpriced":           ["expensive", "overpriced", "not worth", "costly"],
    "Bad Customer Service": ["customer service", "support", "refund", "return"],
    "Fake Product":         ["fake", "duplicate", "not original", "counterfeit"],
    "Packaging Issue":      ["packaging", "box damage", "packing"],
    "Heating Issue":        ["heat", "hot", "overheat", "warm"],
    "Software Bugs":        ["bug", "crash", "freeze", "lag", "glitch"],
    "Missing Accessories":  ["missing", "not included", "accessory", "charger"],
}

POSITIVE_KEYWORDS = {
    "Great Value":           ["value", "worth", "affordable", "great price", "budget"],
    "Excellent Performance": ["fast", "smooth", "performance", "powerful", "speed"],
    "Great Camera":          ["camera", "photo", "picture", "lens"],
    "Long Battery Life":     ["battery life", "long battery", "all day", "lasting"],
    "Premium Build":         ["premium", "solid", "sturdy", "well built"],
    "Fast Delivery":         ["fast delivery", "quick delivery", "arrived early"],
    "Beautiful Display":     ["display", "screen", "beautiful", "bright", "amoled", "oled"],
    "Easy to Use":           ["easy", "intuitive", "user friendly", "simple"],
}

ASPECTS = {
    "Camera":      ["camera", "photo", "video", "picture", "lens", "megapixel"],
    "Battery":     ["battery", "charge", "drain", "power", "mah"],
    "Display":     ["screen", "display", "resolution", "brightness", "amoled"],
    "Performance": ["performance", "speed", "fast", "lag", "processor", "ram", "smooth"],
    "Build":       ["build", "quality", "premium", "plastic", "glass", "feel"],
    "Value":       ["price", "value", "worth", "expensive", "cheap", "affordable"],
    "Software":    ["software", "ui", "os", "android", "ios", "update", "bloat"],
    "Audio":       ["speaker", "sound", "audio", "headphone", "volume", "bass"],
}


def classify_text(text: str) -> str:
    """Return 'positive', 'negative', or 'neutral'."""
    score = analyzer.polarity_scores(text)["compound"]
    if score >= 0.05:   return "positive"
    if score <= -0.05:  return "negative"
    return "neutral"


def extract_issues(reviews: list[str]) -> list[str]:
    non_pos = [r for r in reviews if classify_text(r) != "positive"]
    source  = non_pos if non_pos else reviews
    all_text = " ".join(source).lower()
    counts = Counter()
    for issue, kws in ISSUE_KEYWORDS.items():
        for kw in kws:
            if kw in all_text:
                counts[issue] += all_text.count(kw)
                break
    return [f"{iss}" for iss, _ in counts.most_common(5)]


def extract_positives(reviews: list[str]) -> list[str]:
    pos_reviews = [r for r in reviews if classify_text(r) == "positive"]
    all_text = " ".join(pos_reviews).lower()
    counts = Counter()
    for label, kws in POSITIVE_KEYWORDS.items():
        for kw in kws:
            if kw in all_text:
                counts[label] += all_text.count(kw)
                break
    return [f"{label}" for label, _ in counts.most_common(5)]


def compute_aspect_scores(reviews: list[str]) -> dict:
    """Return per-aspect sentiment score (0-100) for each detected aspect."""
    scores = {}
    for aspect, kws in ASPECTS.items():
        relevant = [r for r in reviews if any(kw in r.lower() for kw in kws)]
        if not relevant:
            continue
        compounds = [analyzer.polarity_scores(r)["compound"] for r in relevant]
        avg = sum(compounds) / len(compounds)
        scores[aspect] = {
            "score":   round((avg + 1) / 2 * 100),  # normalize -1..1 → 0..100
            "count":   len(relevant),
        }
    return scores


def analyze_sentiment(reviews: list[str]) -> dict:
    """
    Full sentiment analysis on a list of text strings.
    Returns unified dict used across all tabs.
    """
    if not reviews:
        return {
            "positive": 0, "negative": 0, "neutral": 0,
            "score": 0, "top_issues": [], "top_positives": [],
            "compound_scores": [], "aspect_scores": {},
        }

    labels    = [classify_text(r) for r in reviews]
    compounds = [analyzer.polarity_scores(r)["compound"] for r in reviews]

    total = len(labels)
    pos   = round(labels.count("positive") / total * 100)
    neg   = round(labels.count("negative") / total * 100)
    neu   = 100 - pos - neg

    avg_compound = sum(compounds) / len(compounds)
    score = round((avg_compound + 1) / 2 * 100)

    return {
        "positive":       pos,
        "negative":       neg,
        "neutral":        neu,
        "score":          score,
        "top_issues":     extract_issues(reviews) or ["No major issues detected"],
        "top_positives":  extract_positives(reviews) or ["Generally well-received"],
        "compound_scores": compounds,
        "aspect_scores":  compute_aspect_scores(reviews),
    }


def get_combined_score(all_reviews: list[str]) -> dict:
    return analyze_sentiment(all_reviews)
