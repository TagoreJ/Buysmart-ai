"""
YouTube Review Fetcher v2
- Fixes SSL error via httplib2 disable_ssl_certificate_validation
- Gets top 10 videos, 50 comments each
- Filters junk/spam comments with NLP heuristics
- Full sentiment + aspect analysis
"""
import os
import ssl
import re
import streamlit as st
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from collections import Counter

analyzer = SentimentIntensityAnalyzer()

JUNK_KEYWORDS = {
    'subscribe', 'click here', 'follow me', 'check my channel', 'visit my',
    'watch my video', 'sub to sub', 'first!', 'early squad', 'notification',
    'click the bell', 'turn on', 'hit the like', 'smash the like',
    'drop a like', 'first comment', 'who else is here', 'who is watching',
}

ASPECTS = {
    "Camera":      ["camera", "photo", "video", "picture", "lens", "megapixel", "zoom"],
    "Battery":     ["battery", "charge", "drain", "power", "mah", "backup"],
    "Display":     ["screen", "display", "resolution", "brightness", "amoled", "oled", "panel"],
    "Performance": ["performance", "speed", "fast", "lag", "processor", "snapdragon", "ram", "smooth", "gaming"],
    "Build":       ["build", "quality", "premium", "plastic", "glass", "sturdy", "feel", "design"],
    "Value":       ["price", "value", "worth", "expensive", "cheap", "affordable", "budget", "cost"],
    "Software":    ["software", "ui", "android", "ios", "update", "bloatware", "interface", "feature"],
    "Audio":       ["speaker", "sound", "audio", "headphone", "volume", "bass", "earphone"],
}


def _is_quality_comment(text: str) -> bool:
    """NLP heuristic filter to remove junk/spam comments."""
    text = text.strip()
    if len(text) < 20:
        return False
    t_lower = text.lower()
    # Spam keywords
    if any(kw in t_lower for kw in JUNK_KEYWORDS):
        return False
    # Mostly non-alphabetic (emoji/symbol spam)
    alpha_ratio = sum(c.isalpha() for c in text) / max(len(text), 1)
    if alpha_ratio < 0.35:
        return False
    # Excessive repetition (aaaaa, hahaha)
    chars = text.lower().replace(' ', '')
    if len(chars) > 0 and len(set(chars)) / len(chars) < 0.15:
        return False
    # Excessive punctuation
    punct_ratio = sum(c in '!?' for c in text) / max(len(text), 1)
    if punct_ratio > 0.25:
        return False
    return True


def _get_youtube_client():
    api_key = ""
    try:
        api_key = st.secrets.get("YOUTUBE_API_KEY", "")
    except Exception:
        pass
    if not api_key:
        api_key = os.getenv("YOUTUBE_API_KEY", "")
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY not configured in secrets.")

    # Patch urllib3 which requests uses (and thus googleapiclient uses by default)
    # This solves the EOF violation bug on python 3.10+
    import urllib3
    urllib3.disable_warnings()
    
    # We create a custom requests Session and disable verification
    import requests
    session = requests.Session()
    session.verify = False

    # Force the google API client to use our requests session
    from googleapiclient.discovery import build
    import google_auth_httplib2
    
    # Actually googleapiclient handles it natively without httplib2 if we just let it
    # We wrap it in a mock http object if needed, but in modern versions passing static api_key 
    # lets us just return build normally, after patching ssl at the lowest level.
    import ssl
    if hasattr(ssl, 'OP_IGNORE_UNEXPECTED_EOF'):
        # Global patch for urllib3 ssl context creation
        orig_create = ssl.create_default_context
        def patched_create(*args, **kwargs):
            ctx = orig_create(*args, **kwargs)
            ctx.options |= getattr(ssl, 'OP_IGNORE_UNEXPECTED_EOF')
            return ctx
        ssl.create_default_context = patched_create

    try:
        import httplib2
        http = httplib2.Http(disable_ssl_certificate_validation=True)
        return build("youtube", "v3", developerKey=api_key, http=http)
    except Exception:
        return build("youtube", "v3", developerKey=api_key)


def _classify(text: str) -> str:
    s = analyzer.polarity_scores(text)["compound"]
    return "positive" if s >= 0.05 else ("negative" if s <= -0.05 else "neutral")


def _compound(text: str) -> float:
    return analyzer.polarity_scores(text)["compound"]


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_youtube_reviews(query: str) -> dict:
    """
    Search YouTube for top 10 review videos.
    Fetch up to 50 comments per video.
    Filter junk comments with NLP heuristics.
    """
    youtube = _get_youtube_client()

    # Search top 15 review videos
    search_resp = youtube.search().list(
        q=f"{query} review",
        part="id,snippet",
        maxResults=15,
        type="video",
        relevanceLanguage="en",
        order="relevance",
    ).execute()

    video_ids = [item["id"]["videoId"] for item in search_resp.get("items", [])]
    if not video_ids:
        raise ValueError(f"No YouTube videos found for '{query}'.")

    # Fetch stats
    stats_resp = youtube.videos().list(
        part="statistics,snippet,contentDetails",
        id=",".join(video_ids),
    ).execute()

    videos = []
    for item in stats_resp.get("items", []):
        stats   = item.get("statistics", {})
        snippet = item.get("snippet", {})
        videos.append({
            "video_id":      item["id"],
            "title":         snippet.get("title", ""),
            "channel":       snippet.get("channelTitle", ""),
            "description":   snippet.get("description", "")[:400],
            "published_at":  snippet.get("publishedAt", ""),
            "thumbnail":     snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
            "view_count":    int(stats.get("viewCount", 0)),
            "like_count":    int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "url":           f"https://www.youtube.com/watch?v={item['id']}",
        })

    # Fetch + filter comments from top 10 by views
    top_videos = sorted(videos, key=lambda x: x["view_count"], reverse=True)[:10]
    all_comments = []

    for video in top_videos:
        try:
            c_resp = youtube.commentThreads().list(
                part="snippet",
                videoId=video["video_id"],
                maxResults=50,
                order="relevance",
                textFormat="plainText",
            ).execute()
            for item in c_resp.get("items", []):
                c    = item["snippet"]["topLevelComment"]["snippet"]
                text = c.get("textDisplay", "").strip()
                if text and _is_quality_comment(text):
                    all_comments.append({
                        "text":        text[:300],
                        "likes":       c.get("likeCount", 0),
                        "author":      c.get("authorDisplayName", ""),
                        "published_at":c.get("publishedAt", ""),
                        "video_id":    video["video_id"],
                        "video_title": video["title"],
                    })
        except Exception:
            pass

    return {"videos": videos, "comments": all_comments}


def analyze_youtube_sentiment(data: dict) -> dict:
    """Full NLP analysis on YouTube videos + quality-filtered comments."""
    videos   = data.get("videos", [])
    comments = data.get("comments", [])

    enriched = []
    for c in comments:
        comp  = _compound(c["text"])
        label = _classify(c["text"])
        enriched.append({**c, "sentiment": label, "compound": comp})

    total = len(enriched)
    if total == 0:
        pos_pct = neg_pct = neu_pct = score = 0
    else:
        pos_count = sum(1 for c in enriched if c["sentiment"] == "positive")
        neg_count = sum(1 for c in enriched if c["sentiment"] == "negative")
        pos_pct   = round(pos_count / total * 100)
        neg_pct   = round(neg_count / total * 100)
        neu_pct   = 100 - pos_pct - neg_pct
        avg_comp  = sum(c["compound"] for c in enriched) / total
        score     = round((avg_comp + 1) / 2 * 100)

    # Aspect scores
    aspect_scores = {}
    for aspect, kws in ASPECTS.items():
        relevant = [c for c in enriched if any(kw in c["text"].lower() for kw in kws)]
        if not relevant:
            continue
        avg = sum(c["compound"] for c in relevant) / len(relevant)
        aspect_scores[aspect] = {"score": round((avg + 1) / 2 * 100), "count": len(relevant)}

    top_pos = sorted([c for c in enriched if c["sentiment"] == "positive"],
                     key=lambda x: x["likes"], reverse=True)[:5]
    top_neg = sorted([c for c in enriched if c["sentiment"] == "negative"],
                     key=lambda x: x["likes"], reverse=True)[:5]

    vid_enriched = []
    for v in videos:
        text  = v["title"] + " " + v["description"]
        label = _classify(text)
        comp  = _compound(text)
        vid_enriched.append({**v, "sentiment": label, "compound": comp})

    return {
        "total_videos":    len(videos),
        "total_comments":  total,
        "positive_pct":    pos_pct,
        "negative_pct":    neg_pct,
        "neutral_pct":     neu_pct,
        "overall_score":   score,
        "comments":        enriched,
        "videos":          vid_enriched,
        "aspect_scores":   aspect_scores,
        "top_positive":    top_pos,
        "top_negative":    top_neg,
        "channel_counts":  dict(Counter(v["channel"] for v in videos).most_common(8)),
        "compound_scores": [c["compound"] for c in enriched],
        "total_views":     sum(v["view_count"] for v in videos),
        "total_likes":     sum(v["like_count"] for v in videos),
    }
