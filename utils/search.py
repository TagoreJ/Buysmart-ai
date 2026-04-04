"""
Real product price fetching via SerpAPI Google Shopping.
No mock data — raises errors if API fails.
"""
import os
import requests
import streamlit as st


def _get_api_key() -> str:
    try:
        key = st.secrets.get("SERPAPI_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("SERPAPI_KEY", "")


def _classify_platform(source: str) -> str:
    s = source.lower()
    if "amazon" in s:       return "Amazon"
    elif "flipkart" in s:   return "Flipkart"
    elif "meesho" in s:     return "Meesho"
    elif "croma" in s:      return "Croma"
    elif "reliance" in s:   return "Reliance Digital"
    elif "snapdeal" in s:   return "Snapdeal"
    elif "myntra" in s:     return "Myntra"
    elif "jiomart" in s:    return "JioMart"
    else:                   return source.title() if source else "Other"


@st.cache_data(show_spinner=False, ttl=1800)
def fetch_products(query: str) -> list[dict]:
    """
    Fetch live product prices from Google Shopping via SerpAPI.
    Returns list of product dicts — no mock fallback.
    Raises ValueError if API key is missing.
    Raises requests.HTTPError on API failure.
    """
    api_key = _get_api_key()
    if not api_key:
        raise ValueError("SERPAPI_KEY not configured in secrets.")

    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": api_key,
        "gl": "in",
        "hl": "en",
        "currency": "INR",
        "num": "20",
    }
    resp = requests.get("https://serpapi.com/search", params=params, timeout=15)
    resp.raise_for_status()
    results = resp.json().get("shopping_results", [])

    products = []
    seen_prices = set()

    for r in results[:12]:
        price_str = r.get("price", "0")
        try:
            # Handle "₹12,999", "Rs. 12,999.00", etc.
            price = int("".join(filter(str.isdigit, price_str.split(".")[0])))
        except Exception:
            continue

        if price == 0 or price in seen_prices:
            continue
        seen_prices.add(price)

        source = r.get("source", "")
        platform = _classify_platform(source)

        products.append({
            "platform": platform,
            "title":    r.get("title", query)[:100],
            "price":    price,
            "rating":   float(r.get("rating", 0)),
            "reviews_count": r.get("reviews", 0),
            "url":      r.get("link", "#"),
            "thumbnail": r.get("thumbnail", ""),
            "source":   source,
        })

    if not products:
        raise ValueError(f"No results returned by SerpAPI for '{query}'. Try a more specific search.")

    return products
