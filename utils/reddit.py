"""
Real Reddit data via two strategies:
1. DuckDuckGo text search (primary) — no API key, no 403
2. old.reddit.com JSON API (fallback) — simpler endpoint, less blocked
"""
import re
import requests
import streamlit as st


def _extract_subreddit(url: str) -> str:
    m = re.search(r"reddit\.com/r/([^/]+)", url or "")
    return m.group(1) if m else ""


def _ddg_reddit(query: str) -> list[dict]:
    """DuckDuckGo text search filtered to reddit.com — returns snippets."""
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(
                f"{query} review experience opinion site:reddit.com",
                max_results=20,
            ):
                text = r.get("title", "") + " " + r.get("body", "")
                text = text.strip()
                url  = r.get("href", "")
                if len(text) > 30:
                    results.append({
                        "text":      text[:400],
                        "score":     0,
                        "type":      "post",
                        "url":       url,
                        "subreddit": _extract_subreddit(url),
                        "author":    "",
                    })
        return results
    except Exception as e:
        print(f"[DDG Reddit] error: {e}")
        return []


def _old_reddit(query: str) -> list[dict]:
    """Fetch from old.reddit.com search — lower 403 rate than new Reddit."""
    results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        import ssl
        import urllib3
        urllib3.disable_warnings()
        session = requests.Session()
        session.headers.update(headers)
        session.verify = False  # bypass SSL for Reddit
        resp = session.get(
            "https://old.reddit.com/search.json",
            params={"q": f"{query} review", "sort": "relevance",
                    "limit": 10, "type": "link", "t": "year"},
            timeout=12,
        )
        if resp.status_code != 200:
            return []
        for post in resp.json().get("data", {}).get("children", []):
            pd = post.get("data", {})
            title    = pd.get("title", "").strip()
            selftext = pd.get("selftext", "").strip()
            text     = title
            if selftext and selftext not in ("[deleted]", "[removed]"):
                text += " " + selftext[:300]
            if text:
                results.append({
                    "text":      text[:400],
                    "score":     pd.get("score", 0),
                    "type":      "post",
                    "url":       pd.get("url", ""),
                    "subreddit": pd.get("subreddit", ""),
                    "author":    pd.get("author", ""),
                })
    except Exception as e:
        print(f"[old.reddit] error: {e}")
    return results


def _fetch_comments(permalink: str) -> list[dict]:
    """Fetch top comments from a post permalink."""
    comments = []
    headers = {"User-Agent": "Mozilla/5.0 BuySmartAI/2.0"}
    try:
        resp = requests.get(
            f"https://old.reddit.com{permalink}.json",
            headers=headers, timeout=8,
        )
        data = resp.json()
        if len(data) < 2:
            return []
        for child in data[1].get("data", {}).get("children", [])[:12]:
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
    Fetch Reddit discussions with graceful fallback chain:
    DDG search → old.reddit.com API → raise error.
    """
    # Primary: DuckDuckGo (no 403 risk)
    results = _ddg_reddit(query)

    # Supplement with old.reddit API if DDG gave < 5 results
    if len(results) < 5:
        api_posts = _old_reddit(query)
        # Fetch comments from top 2 posts
        for post in api_posts[:2]:
            permalink = re.search(r"reddit\.com(/r/[^?]+)", post.get("url", ""))
            if permalink:
                results.extend(_fetch_comments(permalink.group(1)))
        results.extend(api_posts)

    if not results:
        raise ValueError(
            f"No Reddit discussions found for '{query}'. "
            "Try a shorter or more general product name."
        )

    # Deduplicate by text prefix
    seen, unique = set(), []
    for r in results:
        key = r["text"][:60]
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique[:25]
