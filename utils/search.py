"""
Multi-platform product search strategy:
1. SerpAPI Amazon engine  → Direct Amazon.in results, real images, ASIN-based URLs
2. SerpAPI Google Shopping site:flipkart.com  → Real Flipkart with direct links
3. SerpAPI Google Shopping (general)  → Meesho, Croma, Reliance Digital, etc.
"""
import os
import requests
import streamlit as st

BASE = "https://serpapi.com/search"


def _get_key() -> str:
    try:
        k = st.secrets.get("SERPAPI_KEY", "")
        if k:
            return k
    except Exception:
        pass
    return os.getenv("SERPAPI_KEY", "")


def _classify_platform(source: str) -> str:
    s = source.lower()
    for name, keyword in [
        ("Amazon", "amazon"), ("Flipkart", "flipkart"), ("Meesho", "meesho"),
        ("Croma", "croma"), ("Reliance Digital", "reliance"), ("Snapdeal", "snapdeal"),
        ("Myntra", "myntra"), ("JioMart", "jiomart"), ("Tata Cliq", "tatacliq"),
        ("Vijay Sales", "vijay"), ("Shopsy", "shopsy"), ("Nykaa", "nykaa"),
    ]:
        if keyword in s:
            return name
    return source.strip().title() if source.strip() else "Other"


def _parse_price(raw) -> int:
    """Parse price from any format: int, float, str like '₹12,999.00'"""
    try:
        return int("".join(filter(str.isdigit, str(raw).split(".")[0])))
    except Exception:
        return 0


# ─────────────────────────────────────────────────────────────────────────────
# Amazon.in via SerpAPI Amazon engine
# Returns proper ASIN-based URLs and real product images
# ─────────────────────────────────────────────────────────────────────────────
def _search_amazon(query: str, api_key: str) -> list[dict]:
    params = {
        "engine":        "amazon",
        "k":             query,
        "amazon_domain": "amazon.in",
        "api_key":       api_key,
    }
    try:
        resp = requests.get(BASE, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[Amazon engine] {e}")
        return []

    products = []
    for r in data.get("organic_results", [])[:5]:
        # Price can be a dict {raw, current_price} or a plain string
        price_raw = r.get("price", {})
        if isinstance(price_raw, dict):
            p = price_raw.get("current_price") or price_raw.get("raw", 0)
        else:
            p = price_raw
        price = _parse_price(p)
        if price == 0:
            continue

        asin  = r.get("asin", "")
        url   = f"https://www.amazon.in/dp/{asin}" if asin else r.get("link", "#")

        products.append({
            "platform":      "Amazon",
            "title":         r.get("title", query)[:100],
            "price":         price,
            "rating":        float(r.get("rating") or 0),
            "reviews_count": int(r.get("reviews") or 0),
            "url":           url,
            "thumbnail":     r.get("thumbnail", ""),
            "badge":         "Prime" if r.get("is_prime") else "",
            "source":        "Amazon",
        })
    return products


# ─────────────────────────────────────────────────────────────────────────────
# Flipkart via Google Shopping + site filter
# ─────────────────────────────────────────────────────────────────────────────
def _search_flipkart(query: str, api_key: str) -> list[dict]:
    params = {
        "engine":   "google_shopping",
        "q":        f"{query} site:flipkart.com",
        "api_key":  api_key,
        "gl":       "in",
        "hl":       "en",
        "currency": "INR",
        "num":      "10",
    }
    try:
        resp = requests.get(BASE, params=params, timeout=15)
        resp.raise_for_status()
        raw = resp.json().get("shopping_results", [])
    except Exception as e:
        print(f"[Flipkart search] {e}")
        return []

    products = []
    for r in raw[:4]:
        price = _parse_price(r.get("price", "0"))
        if price == 0:
            continue

        # Extract direct Flipkart link (not Google redirect)
        link = r.get("product_link") or r.get("link", "#")
        if "google.com" in link:
            # Try to extract Flipkart URL from the redirect
            import re
            match = re.search(r"flipkart\.com[^\s\"&]+", link)
            link = "https://www." + match.group(0) if match else link

        products.append({
            "platform":      "Flipkart",
            "title":         r.get("title", query)[:100],
            "price":         price,
            "rating":        float(r.get("rating") or 0),
            "reviews_count": int(r.get("reviews") or 0),
            "url":           link,
            "thumbnail":     r.get("thumbnail", ""),
            "badge":         "",
            "source":        "Flipkart",
        })
    return products


# ─────────────────────────────────────────────────────────────────────────────
# General Google Shopping (other platforms)
# ─────────────────────────────────────────────────────────────────────────────
def _search_general(query: str, api_key: str) -> list[dict]:
    params = {
        "engine":   "google_shopping",
        "q":        query,
        "api_key":  api_key,
        "gl":       "in",
        "hl":       "en",
        "currency": "INR",
        "num":      "20",
    }
    try:
        resp = requests.get(BASE, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json().get("shopping_results", [])
    except Exception as e:
        print(f"[General shopping] {e}")
        return []


@st.cache_data(show_spinner=False, ttl=1800)
def fetch_products(query: str) -> list[dict]:
    """
    Triple-strategy product search:
    1. Amazon.in (engine=amazon) — real ASINs, images, Prime badge
    2. Flipkart (Google Shopping + site filter) — direct URLs
    3. General Google Shopping — all other Indian stores

    Returns list sorted by price, no duplicates, no mock data.
    """
    api_key = _get_key()
    if not api_key:
        raise ValueError("SERPAPI_KEY not configured in .streamlit/secrets.toml")

    products     = []
    seen_prices  = set()
    seen_platforms = {}

    def _add(p: dict):
        pl    = p["platform"]
        price = p["price"]
        limit = 2 if pl in ("Amazon", "Flipkart") else 3
        if price == 0 or price in seen_prices:
            return
        if seen_platforms.get(pl, 0) >= limit:
            return
        seen_prices.add(price)
        seen_platforms[pl] = seen_platforms.get(pl, 0) + 1
        products.append(p)

    # 1. Amazon
    for p in _search_amazon(query, api_key):
        _add(p)

    # 2. Flipkart
    for p in _search_flipkart(query, api_key):
        _add(p)

    # 3. General (other platforms)
    for r in _search_general(query, api_key):
        price = _parse_price(r.get("price", "0"))
        if price == 0:
            continue
        source   = r.get("source", "")
        platform = _classify_platform(source)

        # Skip Amazon/Flipkart from general (already done above)
        if platform in ("Amazon", "Flipkart"):
            continue

        # Prefer direct links
        link = r.get("product_link") or r.get("link", "#")
        if link == "#":
            continue

        _add({
            "platform":      platform,
            "title":         r.get("title", query)[:100],
            "price":         price,
            "rating":        float(r.get("rating") or 0),
            "reviews_count": int(r.get("reviews") or 0),
            "url":           link,
            "thumbnail":     r.get("thumbnail", ""),
            "badge":         "",
            "source":        source,
        })

    if not products:
        raise ValueError(
            f"No products found for '{query}'. "
            "Try a different product name or check your SerpAPI key."
        )

    return sorted(products, key=lambda x: x["price"])
