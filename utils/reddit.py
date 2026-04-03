"""
Fetches Reddit opinions about a product using Pushshift API (no API key needed).
Falls back to mock data if request fails.
"""

import requests
import streamlit as st


def _mock_reddit(query: str) -> list[dict]:
    """Realistic mock Reddit opinions."""
    posts = [
        {"text": f"Just bought {query} and honestly it's pretty decent for the price. Build quality is solid."},
        {"text": f"Anyone else had issues with {query}? Mine started heating up after 2 months of use."},
        {"text": f"Compared {query} with alternatives - this one wins on display quality easily."},
        {"text": f"Don't buy {query} from third-party sellers, got a fake one. Always buy from official store."},
        {"text": f"{query} is overrated imo. You can get better value elsewhere."},
        {"text": f"Battery on {query} is disappointing. Expected much better at this price point."},
        {"text": f"Customer service for {query} was surprisingly helpful when I had an issue."},
        {"text": f"Using {query} for 6 months now — zero complaints. Solid purchase."},
    ]
    return posts


def fetch_reddit_opinions(query: str) -> list[dict]:
    """
    Fetch Reddit posts mentioning the product.
    Uses Reddit's JSON API (no API key needed).
    """
    try:
        url = "https://www.reddit.com/search.json"
        params = {
            "q": f"{query} review",
            "sort": "relevance",
            "limit": 15,
            "type": "link"
        }
        headers = {"User-Agent": "BuySmartAI/1.0"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for post in data.get("data", {}).get("children", []):
            post_data = post.get("data", {})
            text = post_data.get("title", "")
            if post_data.get("selftext"):
                text += " " + post_data.get("selftext", "")[:200]
            results.append({"text": text.strip()})
        
        return results[:10] if results else _mock_reddit(query)
    except Exception as e:
        print(f"Error: {e}")  # For debugging
        return _mock_reddit(query)
