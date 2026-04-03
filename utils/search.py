"""
Fetches product prices & reviews from Amazon/Flipkart via SerpAPI.
Falls back to realistic mock data if the API key is missing or request fails.

API key must be set via:
  - Streamlit secrets: SERPAPI_KEY = "your_key"       (recommended for cloud)
  - Environment variable: SERPAPI_KEY=your_key         (for local use)
"""

import os
import requests
import streamlit as st


def _get_api_key() -> str:
    """Read SerpAPI key from Streamlit secrets or environment variable."""
    try:
        key = st.secrets.get("SERPAPI_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("SERPAPI_KEY", "")


def _serpapi_search(query: str, engine: str = "google_shopping") -> list[dict]:
    """Call SerpAPI Google Shopping."""
    api_key = _get_api_key()
    if not api_key:
        return []

    params = {
        "engine": engine,
        "q": query,
        "api_key": api_key,
        "gl": "in",
        "hl": "en",
        "currency": "INR",
    }
    try:
        resp = requests.get("https://serpapi.com/search", params=params, timeout=10)
        data = resp.json()
        return data.get("shopping_results", [])
    except Exception:
        return []


def _mock_products(query: str) -> list[dict]:
    """Realistic mock data for demo / when no API key is configured."""
    import random
    base_prices = {"amazon": random.randint(8000, 55000), "flipkart": 0}
    base_prices["flipkart"] = base_prices["amazon"] - random.randint(200, 2000)

    amazon_reviews = [
        "Great product! Very happy with the purchase.",
        "Delivery was a bit slow but quality is excellent.",
        "Exactly as described. Worth every rupee.",
        "Battery life could be better but overall good.",
        "Customer service was helpful when I had an issue.",
        "Build quality feels premium. Impressed.",
        "Slight heating issue after long use.",
        "Packaging was damaged but product is fine.",
        "Great value for money. Would recommend.",
        "Screen is beautiful. Love the display quality.",
        "Not worth the price. Expected better.",
        "Fake product received. Very disappointed.",
    ]
    flipkart_reviews = [
        "Good product at this price range.",
        "Delivery was fast and packaging was good.",
        "Works as expected. No complaints.",
        "Quality is decent but not premium.",
        "Had to return once due to defect, replacement was quick.",
        "Overpriced for what you get.",
        "Great display and performance.",
        "Battery drains too fast.",
        "Customer support was unresponsive.",
        "Overall satisfied with the purchase.",
        "Product looks cheap but works fine.",
        "Late delivery but product quality is good.",
    ]

    return [
        {
            "platform": "Amazon",
            "title": f"{query} - Top Rated",
            "price": base_prices["amazon"],
            "rating": round(random.uniform(3.8, 4.6), 1),
            "url": f"https://www.amazon.in/s?k={query.replace(' ', '+')}",
            "reviews": random.sample(amazon_reviews, 10),
            "reviews_source": "mock",
        },
        {
            "platform": "Flipkart",
            "title": f"{query} - Best Seller",
            "price": base_prices["flipkart"],
            "rating": round(random.uniform(3.5, 4.4), 1),
            "url": f"https://www.flipkart.com/search?q={query.replace(' ', '+')}",
            "reviews": random.sample(flipkart_reviews, 10),
            "reviews_source": "mock",
        },
    ]


@st.cache_data(show_spinner=False)
def fetch_products(query: str) -> tuple[list[dict], bool]:
    """
    Main function called by app.py.
    Returns (products, used_mock_data).

    - Tries SerpAPI for live prices.
    - Falls back to mock if key is missing or API returns nothing.
    - Filters out products with price = 0 (parse failures).
    - Reviews are always labelled with their source ('mock' or 'real').
    """
    results = _serpapi_search(query)

    if not results:
        return _mock_products(query), True   # (products, used_mock)

    products = []
    for r in results[:4]:
        price_str = r.get("price", "0")
        try:
            price = int("".join(filter(str.isdigit, price_str.split(".")[0])))
        except Exception:
            price = 0

        if price == 0:
            continue   # skip unparseable / free listings

        source = r.get("source", "Online Store")
        platform = "Amazon" if "amazon" in source.lower() else (
                   "Flipkart" if "flipkart" in source.lower() else source)

        products.append({
            "platform": platform,
            "title":    r.get("title", query),
            "price":    price,
            "rating":   float(r.get("rating", 4.0)),
            "url":      r.get("link", "#"),
            "reviews":  [],
            "reviews_source": "real",
        })

    if not products:
        return _mock_products(query), True

    # SerpAPI Shopping doesn't return review text — attach mock reviews
    # and mark their source so the UI can display a transparency badge
    mock = _mock_products(query)
    platform_map = {p["platform"]: p["reviews"] for p in mock}
    for p in products:
        p["reviews"] = platform_map.get(p["platform"], mock[0]["reviews"])
        p["reviews_source"] = "mock"   # reviews are always sample data

    return products, False   # prices are real even if reviews are mocked
