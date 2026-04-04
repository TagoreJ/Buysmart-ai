"""
YouTube review fetcher and NLP analyzer.
Uses YouTube Data API v3 — searches for product review videos,
fetches video stats, comments, and runs full sentiment + aspect analysis.
"""
import os
import streamlit as st
from googleapiclient.discovery import build
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from collections import Counter

analyzer = SentimentIntensityAnalyzer()

ASPECTS = {
    "Camera":      ["camera", "photo", "video", "picture", "lens"],
    "Battery":     ["battery", "charge", "drain", "power"],
    "Display":     ["screen", "display", "resolution", "brightness"],
    "Performance": ["performance", "speed", "fast", "lag", "smooth"],
    "Build":       ["build", "quality", "premium", "sturdy"],
    "Value":       ["price", "value", "worth", "afford", "expensive"],
    "Software":    ["software", "ui", "android", "ios", "update"],
    "Audio":       ["speaker", "sound", "audio", "bass"],
}


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
    return build("youtube", "v3", developerKey=api_key)


def _classify(text: str) -> str:
    s = analyzer.polarity_scores(text)["compound"]
    if s >= 0.05:   return "positive"
    if s <= -0.05:  return "negative"
    return "neutral"


def _compound(text: str) -> float:
    return analyzer.polarity_scores(text)["compound"]


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_youtube_reviews(query: str) -> dict:
    """
    Search YouTube for product review videos, fetch statistics + comments.
    Returns raw data dict for analysis.
    """
    youtube = _get_youtube_client()

    # 1. Search review videos
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

    # 2. Fetch video statistics
    stats_resp = youtube.videos().list(
        part="statistics,snippet,contentDetails",
        id=",".join(video_ids),
    ).execute()

    videos = []
    for item in stats_resp.get("items", []):
        stats   = item.get("statistics", {})
        snippet = item.get("snippet", {})
        videos.append({
            "video_id":     item["id"],
            "title":        snippet.get("title", ""),
            "channel":      snippet.get("channelTitle", ""),
            "description":  snippet.get("description", "")[:400],
            "published_at": snippet.get("publishedAt", ""),
            "thumbnail":    snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
            "view_count":   int(stats.get("viewCount", 0)),
            "like_count":   int(stats.get("likeCount", 0)),
            "comment_count":int(stats.get("commentCount", 0)),
            "url":          f"https://www.youtube.com/watch?v={item['id']}",
        })

    # 3. Fetch comments from top 8 videos
    all_comments = []
    for video in sorted(videos, key=lambda x: x["view_count"], reverse=True)[:8]:
        try:
            c_resp = youtube.commentThreads().list(
                part="snippet",
                videoId=video["video_id"],
                maxResults=50,
                order="relevance",
                textFormat="plainText",
            ).execute()
            for item in c_resp.get("items", []):
                c = item["snippet"]["topLevelComment"]["snippet"]
                text = c.get("textDisplay", "").strip()
                if text and len(text) > 15:
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
    """
    Full NLP analysis on YouTube videos + comments.
    Returns structured dict for all visualizations.
    """
    videos   = data.get("videos", [])
    comments = data.get("comments", [])

    # Sentiment per comment
    enriched = []
    for c in comments:
        comp  = _compound(c["text"])
        label = _classify(c["text"])
        enriched.append({**c, "sentiment": label, "compound": comp})

    total = len(enriched)
    if total == 0:
        pos_pct = neg_pct = neu_pct = 0
        score = 0
    else:
        pos_count = sum(1 for c in enriched if c["sentiment"] == "positive")
        neg_count = sum(1 for c in enriched if c["sentiment"] == "negative")
        pos_pct = round(pos_count / total * 100)
        neg_pct = round(neg_count / total * 100)
        neu_pct = 100 - pos_pct - neg_pct
        avg_comp = sum(c["compound"] for c in enriched) / total
        score = round((avg_comp + 1) / 2 * 100)

    # Aspect scores
    aspect_scores = {}
    texts = [c["text"] for c in enriched]
    for aspect, kws in ASPECTS.items():
        relevant = [c for c in enriched if any(kw in c["text"].lower() for kw in kws)]
        if not relevant:
            continue
        avg = sum(c["compound"] for c in relevant) / len(relevant)
        aspect_scores[aspect] = {
            "score": round((avg + 1) / 2 * 100),
            "count": len(relevant),
        }

    # Top comments
    top_pos = sorted([c for c in enriched if c["sentiment"] == "positive"],
                     key=lambda x: x["likes"], reverse=True)[:5]
    top_neg = sorted([c for c in enriched if c["sentiment"] == "negative"],
                     key=lambda x: x["likes"], reverse=True)[:5]

    # Video sentiment
    vid_enriched = []
    for v in videos:
        text  = v["title"] + " " + v["description"]
        label = _classify(text)
        comp  = _compound(text)
        vid_enriched.append({**v, "sentiment": label, "compound": comp})

    # Channel distribution
    channel_counts = Counter(v["channel"] for v in videos)

    # Compound scores list (for histogram)
    compound_scores = [c["compound"] for c in enriched]

    return {
        "total_videos":        len(videos),
        "total_comments":      total,
        "positive_pct":        pos_pct,
        "negative_pct":        neg_pct,
        "neutral_pct":         neu_pct,
        "overall_score":       score,
        "comments":            enriched,
        "videos":              vid_enriched,
        "aspect_scores":       aspect_scores,
        "top_positive":        top_pos,
        "top_negative":        top_neg,
        "channel_counts":      dict(channel_counts.most_common(8)),
        "compound_scores":     compound_scores,
        "total_views":         sum(v["view_count"] for v in videos),
        "total_likes":         sum(v["like_count"]  for v in videos),
    }
