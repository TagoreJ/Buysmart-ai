"""
Real Reddit opinion fetcher.
Fetches post titles + body text + top comments from the Reddit JSON API.
No mock data fallback.
"""
import requests
import streamlit as st


HEADERS = {
    "User-Agent": "BuySmartAI/2.0 (research tool; not commercial)",
    "Accept": "application/json",
}


def _fetch_comments(permalink: str) -> list[dict]:
    """Fetch top comments from a Reddit post via its permalink."""
    comments = []
    try:
        url = f"https://www.reddit.com{permalink}.json"
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code != 200:
            return []
        data = resp.json()
        if len(data) < 2:
            return []
        for child in data[1].get("data", {}).get("children", [])[:15]:
            cd = child.get("data", {})
            body = cd.get("body", "").strip()
            if body and body not in ("[deleted]", "[removed]") and len(body) > 20:
                comments.append({
                    "text":      body[:400],
                    "score":     cd.get("score", 0),
                    "type":      "comment",
                    "url":       "",
                    "subreddit": cd.get("subreddit", ""),
                    "author":    cd.get("author", ""),
                })
    except Exception:
        pass
    return comments


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_reddit_opinions(query: str) -> list[dict]:
    """
    Fetch Reddit posts + comments about the product.
    Returns list of {"text", "score", "type", "url", "subreddit"}.
    Raises requests.HTTPError on network failure.
    """
    params = {
        "q":     f"{query} review",
        "sort":  "relevance",
        "limit": 10,
        "type":  "link",
        "t":     "year",
    }
    resp = requests.get(
        "https://www.reddit.com/search.json",
        params=params,
        headers=HEADERS,
        timeout=12,
    )
    resp.raise_for_status()

    results = []
    permalinks = []

    for post in resp.json().get("data", {}).get("children", []):
        pd = post.get("data", {})
        title = pd.get("title", "").strip()
        selftext = pd.get("selftext", "").strip()
        text = title
        if selftext and selftext not in ("[deleted]", "[removed]"):
            text += " " + selftext[:300]

        if text.strip():
            results.append({
                "text":      text.strip(),
                "score":     pd.get("score", 0),
                "type":      "post",
                "url":       pd.get("url", ""),
                "subreddit": pd.get("subreddit", ""),
                "author":    pd.get("author", ""),
            })
        if pd.get("permalink"):
            permalinks.append(pd["permalink"])

    # Fetch comments from top 3 posts
    for permalink in permalinks[:3]:
        results.extend(_fetch_comments(permalink))

    if not results:
        raise ValueError(f"No Reddit discussions found for '{query}'.")

    return results
