"""
Fetches Reddit opinions about a product using PRAW (Reddit API).
Falls back to mock data if credentials not set.
"""

import os
import streamlit as st

REDDIT_CLIENT_ID     = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT    = "BuySmartAI/1.0"


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
    Uses PRAW if credentials are set, else returns mock data.
    """
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        return _mock_reddit(query)

    try:
        import praw
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )
        results = []
        for submission in reddit.subreddit("all").search(
            f"{query} review", limit=15, sort="relevance"
        ):
            text = submission.title
            if submission.selftext:
                text += " " + submission.selftext[:200]
            results.append({"text": text.strip()})

        return results[:10] if results else _mock_reddit(query)

    except Exception as e:
        st.warning(f"Reddit fetch failed: {e}. Using sample data.")
        return _mock_reddit(query)
