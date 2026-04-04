"""
E-commerce Review Mining
Layered approach (most reliable → least reliable):
  1. Direct Amazon.in scraping via requests + BeautifulSoup (ASIN-based URL)
  2. Direct Flipkart scraping
  3. googlesearch-python → fetch review pages from web
  4. SerpAPI Google organic snippets (fallback)
"""
import re
import os
import requests
import streamlit as st
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language":  "en-IN,en;q=0.9",
    "Accept":           "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding":  "gzip, deflate",
    "Connection":       "keep-alive",
    "DNT":              "1",
}


def _get_key() -> str:
    try:
        k = st.secrets.get("SERPAPI_KEY", "")
        if k:
            return k
    except Exception:
        pass
    return os.getenv("SERPAPI_KEY", "")


# ─────────────────────────────────────────────────────────────────────────────
# Amazon scraper
# ─────────────────────────────────────────────────────────────────────────────
def _scrape_amazon(asin: str) -> list[str]:
    """Scrape review text from amazon.in product-reviews page."""
    url = (
        f"https://www.amazon.in/product-reviews/{asin}/"
        "?reviewerType=all_reviews&sortBy=recent&pageNumber=1"
    )
    try:
        s = requests.Session()
        s.headers.update(HEADERS)
        resp = s.get(url, timeout=15, allow_redirects=True)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        reviews = []

        # Primary selector (Amazon's data-hook attribute)
        for tag in soup.find_all("span", {"data-hook": "review-body"}):
            text = tag.get_text(separator=" ", strip=True)
            if 30 < len(text) < 1000:
                reviews.append(text[:400])

        # Backup CSS class (may change)
        if not reviews:
            for tag in soup.find_all(class_=re.compile(r"review-text")):
                text = tag.get_text(strip=True)
                if 30 < len(text) < 1000:
                    reviews.append(text[:400])

        return reviews[:20]
    except Exception as e:
        print(f"[Amazon scrape] {e}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Flipkart scraper
# ─────────────────────────────────────────────────────────────────────────────
def _scrape_flipkart(url: str) -> list[str]:
    """Try to scrape reviews from a Flipkart product page."""
    if "flipkart.com" not in url:
        return []
    try:
        s = requests.Session()
        s.headers.update(HEADERS)
        resp = s.get(url, timeout=15)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        reviews = []

        # Try several known Flipkart review CSS patterns
        for selector in [
            {"class": re.compile(r"t-ZTKy")},
            {"class": re.compile(r"row")},
        ]:
            for tag in soup.find_all("div", selector):
                text = tag.get_text(separator=" ", strip=True)
                if 30 < len(text) < 600:
                    reviews.append(text[:400])

        # Generic review-like paragraphs
        if not reviews:
            for p in soup.find_all("p"):
                text = p.get_text(strip=True)
                if 40 < len(text) < 500:
                    reviews.append(text[:400])

        return list(dict.fromkeys(reviews))[:20]  # deduplicate
    except Exception as e:
        print(f"[Flipkart scrape] {e}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Google search → review pages
# ─────────────────────────────────────────────────────────────────────────────
def _google_review_search(query: str) -> list[dict]:
    """Search Google for review pages and extract text via BS4."""
    results = []
    try:
        from googlesearch import search
        urls = list(search(
            f"{query} user reviews buy",
            num_results=8,
            pause=2,
        ))
        session = requests.Session()
        session.headers.update(HEADERS)

        for url in urls:
            try:
                resp = session.get(url, timeout=8)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")
                for tag in ("nav", "footer", "script", "style", "header", "aside"):
                    for el in soup.find_all(tag):
                        el.decompose()

                source = re.search(r"(?:https?://)?(?:www\.)?([^/]+)", url)
                domain = source.group(1) if source else "web"

                for p in soup.find_all("p"):
                    text = p.get_text(strip=True)
                    if 50 < len(text) < 600:
                        results.append({"text": text[:400], "source": domain, "url": url})
                        if len(results) >= 40:
                            break
            except Exception:
                continue
    except Exception as e:
        print(f"[Google review search] {e}")
    return results


# ─────────────────────────────────────────────────────────────────────────────
# SerpAPI organic snippets fallback
# ─────────────────────────────────────────────────────────────────────────────
def _serpapi_snippets(query: str) -> list[dict]:
    api_key = _get_key()
    if not api_key:
        return []
    results = []
    for q in [f"{query} amazon review", f"{query} flipkart review"]:
        try:
            resp = requests.get(
                "https://serpapi.com/search",
                params={"engine": "google", "q": q, "api_key": api_key,
                        "gl": "in", "hl": "en", "num": 10},
                timeout=12,
            )
            for r in resp.json().get("organic_results", []):
                snippet = r.get("snippet", "")
                if len(snippet) > 40:
                    link = r.get("link", "")
                    src  = ("Amazon"   if "amazon" in link else
                            "Flipkart" if "flipkart" in link else "Web")
                    results.append({"text": snippet, "source": src, "url": link})
        except Exception:
            pass
    return results[:20]


# ─────────────────────────────────────────────────────────────────────────────
# Master
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def fetch_ecommerce_reviews(query: str, amazon_asin: str = "",
                            flipkart_url: str = "") -> dict:
    """
    Layered ecommerce review mining.
    Returns {amazon, flipkart, web, all_texts}.
    """
    out = {"amazon": [], "flipkart": [], "web": []}

    # Layer 1: Direct scraping
    if amazon_asin:
        out["amazon"] = _scrape_amazon(amazon_asin)
    if flipkart_url:
        out["flipkart"] = _scrape_flipkart(flipkart_url)

    # Layer 2: Google search with BS4
    web_items = _google_review_search(query)
    for item in web_items:
        src = item["source"].lower()
        if "amazon" in src and not out["amazon"]:
            out["amazon"].append(item["text"])
        elif "flipkart" in src and not out["flipkart"]:
            out["flipkart"].append(item["text"])
        else:
            out["web"].append(item)

    # Layer 3: SerpAPI snippets as fallback
    total = len(out["amazon"]) + len(out["flipkart"]) + len(out["web"])
    if total < 5:
        for item in _serpapi_snippets(query):
            src = item["source"].lower()
            if "amazon" in src:
                out["amazon"].append(item["text"])
            elif "flipkart" in src:
                out["flipkart"].append(item["text"])
            else:
                out["web"].append(item)

    # All texts combined (simple list of strings)
    all_texts = (
        out["amazon"] +
        out["flipkart"] +
        [r["text"] if isinstance(r, dict) else r for r in out["web"]]
    )
    out["all_texts"] = all_texts
    return out
