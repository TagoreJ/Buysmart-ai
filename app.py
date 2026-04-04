import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

from utils.sentiment import analyze_sentiment, get_combined_score
from utils.search import fetch_products
from utils.reddit import fetch_reddit_opinions
from utils.youtube import fetch_youtube_reviews, analyze_youtube_sentiment
from utils.ecommerce_reviews import fetch_ecommerce_reviews
from utils.nlp_deep import run_deep_nlp

def get_ai_verdict(product_name, best_price, ov_score, yt_score, reddit_sc, aspect_scores):
    import requests
    import os
    api_key = st.secrets.get("OPENROUTER_API_KEY", "")
    if not api_key:
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        return "⚠️ OpenRouter API Key missing. Please configure secrets.toml."
        
    prompt = f"""
    You are an expert AI shopping assistant for BuySmart. Based on the following intelligence data, write a short, punchy paragraph (max 50 words) summarizing whether the user should buy '{product_name}'.
    - Overall Score: {ov_score}/100 
    - YouTube Reviews Score: {yt_score}/100
    - Reddit Opinions Score: {reddit_sc}/100
    - Best Price: ₹{best_price}
    - Aspect Ratings: {aspect_scores}
    
    Give a brief summary of the sentiment and explicitly end with:
    "Verdict: Strong Buy", "Verdict: Buy", "Verdict: Wait/Consider", or "Verdict: Avoid".
    """
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://buysmart.ai",
                "X-Title": "BuySmart AI"
            },
            json={
                "model": "arcee-ai/trinity-large-preview:free",
                "messages": [
                    {"role": "system", "content": "You are a concise, direct e-commerce analyst. Give highly actionable concise advice."},
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=15
        )
        data = r.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"AI summary currently unavailable. Error: {e}"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BuySmart AI",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS Design System ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; }
body, .stApp { font-family: 'Inter', sans-serif !important; }
h1,h2,h3,h4 { font-family: 'Outfit', sans-serif !important; }

.stApp {
    background: #07090f;
    color: #e2e8f0;
    min-height: 100vh;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; max-width: 1200px; }

/* BG orbs */
.orb-1 {
    position:fixed; width:700px; height:700px; border-radius:50%;
    background:radial-gradient(circle,rgba(99,102,241,0.18) 0%,transparent 70%);
    top:-200px; right:-150px; pointer-events:none; z-index:0;
}
.orb-2 {
    position:fixed; width:600px; height:600px; border-radius:50%;
    background:radial-gradient(circle,rgba(245,158,11,0.14) 0%,transparent 70%);
    bottom:-200px; left:-100px; pointer-events:none; z-index:0;
}

/* Hero */
.hero {
    text-align:center; padding:3.5rem 1rem 2rem;
    position:relative; z-index:1;
}
.hero-badge {
    display:inline-block;
    background:rgba(99,102,241,0.12);
    border:1px solid rgba(99,102,241,0.3);
    color:#818cf8; padding:5px 16px; border-radius:50px;
    font-size:0.75rem; font-weight:600; letter-spacing:0.1em;
    text-transform:uppercase; margin-bottom:1.2rem;
}
.hero-title {
    font-family:'Outfit',sans-serif !important;
    font-size:3.8rem; font-weight:800; line-height:1.1;
    background:linear-gradient(130deg,#ffffff 0%,#a5b4fc 45%,#f59e0b 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    margin-bottom:0.8rem;
}
.hero-sub {
    color:#475569; font-size:1.05rem; max-width:520px;
    margin:0 auto 1.8rem; line-height:1.65;
}

/* Search */
.stTextInput input {
    background:rgba(255,255,255,0.04) !important;
    border:1.5px solid rgba(255,255,255,0.09) !important;
    border-radius:14px !important; color:#f1f5f9 !important;
    font-size:1.05rem !important; padding:0.85rem 1.2rem !important;
}
.stTextInput input:focus {
    border-color:rgba(99,102,241,0.55) !important;
    box-shadow:0 0 0 3px rgba(99,102,241,0.12) !important;
}
.stButton > button {
    background:linear-gradient(135deg,#6366f1,#8b5cf6) !important;
    color:#fff !important; font-weight:600 !important;
    border:none !important; border-radius:14px !important;
    padding:0.85rem 1.5rem !important; font-size:1rem !important;
    width:100%; box-shadow:0 4px 20px rgba(99,102,241,0.35) !important;
    transition:transform 0.15s,box-shadow 0.15s !important;
}
.stButton > button:hover {
    transform:translateY(-2px) !important;
    box-shadow:0 6px 28px rgba(99,102,241,0.5) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background:rgba(255,255,255,0.03);
    border-radius:14px; padding:5px; gap:4px;
    border:1px solid rgba(255,255,255,0.06);
}
.stTabs [data-baseweb="tab"] {
    border-radius:10px; color:#64748b;
    font-weight:500; padding:0.6rem 1.2rem;
}
.stTabs [aria-selected="true"] {
    background:linear-gradient(135deg,#6366f1,#8b5cf6) !important;
    color:#fff !important; font-weight:700 !important;
}

/* Cards */
.card {
    background:rgba(255,255,255,0.03);
    border:1px solid rgba(255,255,255,0.07);
    border-radius:18px; padding:1.4rem 1.5rem;
    margin-bottom:1rem; position:relative;
    transition:border-color 0.2s;
}
.card:hover { border-color:rgba(99,102,241,0.3); }
.card-top-bar {
    position:absolute; top:0; left:0; right:0; height:3px;
    background:linear-gradient(90deg,#6366f1,#f59e0b);
    border-radius:18px 18px 0 0;
}

/* Metric cards */
.metric-card {
    background:rgba(255,255,255,0.03);
    border:1px solid rgba(255,255,255,0.07);
    border-radius:14px; padding:1.1rem;
    text-align:center; height:100%;
}
.metric-val {
    font-family:'Outfit',sans-serif;
    font-size:1.9rem; font-weight:800; line-height:1;
}
.metric-lbl {
    font-size:0.73rem; color:#475569;
    text-transform:uppercase; letter-spacing:0.05em; margin-top:5px;
}

/* Badges */
.badge {
    display:inline-block; padding:3px 12px; border-radius:50px;
    font-size:0.76rem; font-weight:700; letter-spacing:0.03em;
}
.b-amazon  { background:rgba(255,153,0,0.12);  color:#FF9900; border:1px solid rgba(255,153,0,0.3); }
.b-flipkart{ background:rgba(40,116,240,0.12); color:#5b9eff; border:1px solid rgba(40,116,240,0.3); }
.b-reddit  { background:rgba(255,69,0,0.12);   color:#ff6534; border:1px solid rgba(255,69,0,0.3); }
.b-yt      { background:rgba(255,0,0,0.12);    color:#ff4444; border:1px solid rgba(255,0,0,0.3); }
.b-best    { background:rgba(16,185,129,0.12); color:#10b981; border:1px solid rgba(16,185,129,0.3); }
.b-other   { background:rgba(99,102,241,0.12); color:#818cf8; border:1px solid rgba(99,102,241,0.3); }

/* Price */
.price-tag { font-family:'Outfit',sans-serif; font-size:1.55rem; font-weight:800; }
.c-green { color:#10b981; }
.c-red   { color:#ef4444; }
.c-amber { color:#f59e0b; }
.c-indigo{ color:#818cf8; }
.c-muted { color:#475569; }

/* Comment items */
.cci {
    background:rgba(255,255,255,0.02);
    border:1px solid rgba(255,255,255,0.06);
    border-radius:10px;
    padding:0.85rem 1.1rem;
    margin-bottom:0.6rem;
    font-size:0.87rem; color:#94a3b8; line-height:1.6;
}
.cci.pos { border-left:3px solid #10b981; }
.cci.neg { border-left:3px solid #ef4444; }
.cci.neu { border-left:3px solid #f59e0b; }

/* Section label */
.sec-lbl {
    font-family:'Outfit',sans-serif;
    font-size:1.15rem; font-weight:700; color:#f1f5f9;
    margin-bottom:0.8rem; margin-top:1.5rem;
}

/* YT video row */
.yt-row {
    display:flex; gap:12px; align-items:flex-start;
    background:rgba(255,255,255,0.025);
    border:1px solid rgba(255,255,255,0.065);
    border-radius:13px; padding:0.9rem; margin-bottom:0.7rem;
}
.yt-row img { width:110px; height:62px; border-radius:7px; object-fit:cover; flex-shrink:0; }
.yt-meta { font-size:0.76rem; color:#475569; margin-top:3px; }

/* Landing */
.landing { text-align:center; padding:5rem 2rem; }
.landing-icon { font-size:5rem; opacity:0.08; }
</style>

<div class="orb-1"></div>
<div class="orb-2"></div>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_num(n: int) -> str:
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000:     return f"{n/1_000:.1f}K"
    return str(n)


def score_color(s: int) -> str:
    if s >= 65: return "#10b981"
    if s >= 40: return "#f59e0b"
    return "#ef4444"


def verdict(s: int) -> tuple[str, str]:
    if s >= 65: return "✅", "Worth Buying"
    if s >= 40: return "⚠️", "Mixed Feelings"
    return  "❌", "Think Twice"


def platform_badge(p: str) -> str:
    pl = p.lower()
    cls = ("b-amazon" if "amazon" in pl else
           "b-flipkart" if "flipkart" in pl else
           "b-reddit" if "reddit" in pl else
           "b-yt" if "youtube" in pl else "b-other")
    return f'<span class="badge {cls}">{p}</span>'


def dark_chart(fig, title="", height=None):
    kw = dict(height=height) if height else {}
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", family="Inter"),
        title=dict(text=title, font=dict(color="#e2e8f0", family="Outfit")),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.05)"),
        legend=dict(font=dict(color="#94a3b8")),
        margin=dict(t=50, l=0, r=0, b=0),
        **kw,
    )
    return fig


def sentiment_stacked_bar(pos, neu, neg, height=110):
    fig = go.Figure()
    for name, val, clr in [("Positive", pos, "#10b981"), ("Neutral", neu, "#f59e0b"), ("Negative", neg, "#ef4444")]:
        fig.add_trace(go.Bar(
            name=name, x=[val], y=[""], orientation="h",
            marker_color=clr,
            text=[f"{val}%"], textposition="inside",
            hovertemplate=f"<b>{name}</b>: {val}%<extra></extra>",
        ))
    fig.update_layout(
        barmode="stack",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8"),
        showlegend=True,
        legend=dict(orientation="h", x=0, y=1.4, font=dict(color="#94a3b8")),
        height=height,
        margin=dict(t=35, l=0, r=0, b=0),
        xaxis=dict(showticklabels=False, showgrid=False, range=[0, 100]),
        yaxis=dict(showticklabels=False, showgrid=False),
    )
    return fig


# ── Hero + Search ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-badge">🤖 AI-Powered Product Intelligence</div>
    <div class="hero-title">BuySmart AI</div>
    <div class="hero-sub">Real prices · Live community reviews · YouTube analysis · Make smarter buying decisions</div>
</div>
""", unsafe_allow_html=True)

col_q, col_btn = st.columns([5, 1])
with col_q:
    product_query = st.text_input(
        "Product Query", placeholder="Search any product — iPhone 15, Sony WH-1000XM5, Nike Air Max...",
        label_visibility="collapsed", key="q"
    )
with col_btn:
    go_btn = st.button("🔍 Analyse", use_container_width=True)


# ── Main ──────────────────────────────────────────────────────────────────────
if go_btn and product_query.strip():

    errs = {}

    with st.spinner("⚡ Fetching live data from all sources..."):
        try:
            products = fetch_products(product_query)
        except Exception as e:
            products = []
            errs["prices"] = str(e)

        try:
            reddit_data = fetch_reddit_opinions(product_query)
        except Exception as e:
            reddit_data = []
            errs["reddit"] = str(e)

        try:
            yt_raw      = fetch_youtube_reviews(product_query)
            yt_anal     = analyze_youtube_sentiment(yt_raw)
        except Exception as e:
            yt_raw  = {}
            yt_anal = None
            errs["youtube"] = str(e)

    if not products:
        st.error(f"❌ Price fetch failed: {errs.get('prices', 'No results found.')}")
        st.stop()

    # ── Fetch ecommerce reviews (background, non-blocking) ──
    amazon_asin    = ""
    flipkart_url   = ""
    for p in products:
        if p["platform"] == "Amazon" and "amazon.in/dp/" in p.get("url", ""):
            amazon_asin = p["url"].split("/dp/")[1].split("/")[0].split("?")[0]
            break
    for p in products:
        if p["platform"] == "Flipkart":
            flipkart_url = p.get("url", "")
            break

    with st.spinner("🛍️ Mining e-commerce reviews..."):
        try:
            eco_reviews = fetch_ecommerce_reviews(
                product_query, amazon_asin=amazon_asin, flipkart_url=flipkart_url
            )
        except Exception as e:
            eco_reviews = {"amazon": [], "flipkart": [], "web": [], "all_texts": []}
            errs["eco_reviews"] = str(e)

    # Gather all text for Deep NLP across all sources
    all_review_texts = []
    for op in reddit_data:
        all_review_texts.append(op.get("text", ""))
    if yt_anal:
        for c in yt_anal.get("comments", []):
            all_review_texts.append(c.get("text", ""))
    all_review_texts.extend(eco_reviews.get("all_texts", []))
    all_review_texts = [t for t in all_review_texts if len(t.strip()) > 20]

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "💰 Price Comparison",
        "⭐ E-com Reviews",
        "🌐 Community Reviews",
        "🎥 YouTube Reviews",
        "🧠 Deep NLP",
        "📊 Intelligence Dashboard",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — PRICE COMPARISON
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        df = pd.DataFrame(products).sort_values("price").reset_index(drop=True)
        best_price = df.iloc[0]["price"]
        max_price  = df.iloc[-1]["price"]
        savings    = max_price - best_price

        st.markdown('<div class="sec-lbl">💰 Live Price Comparison</div>', unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        for col, val, lbl, clr in [
            (c1, f"₹{best_price:,}",  "Best Price",      "#10b981"),
            (c2, f"₹{savings:,}",     "Max Savings",     "#f59e0b"),
            (c3, str(len(df)),         "Listings Found",  "#818cf8"),
            (c4, f"₹{max_price:,}",   "Highest Price",   "#ef4444"),
        ]:
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val" style="color:{clr}">{val}</div>
                    <div class="metric-lbl">{lbl}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        PLATFORM_COLORS = {
            "Amazon": "#FF9900", "Flipkart": "#4d90fe",
            "Meesho": "#f43f5e", "Croma": "#16a34a",
            "Reliance Digital": "#0ea5e9", "Snapdeal": "#f97316",
            "Myntra": "#d946ef", "JioMart": "#2563eb",
            "Tata Cliq": "#dc2626", "Other": "#6366f1",
        }

        for idx, (_, row) in enumerate(df.iterrows()):
            is_best  = row["price"] == best_price
            pl       = row["platform"]
            pl_lower = pl.lower()
            b_cls    = ("b-amazon"   if "amazon"   in pl_lower else
                        "b-flipkart" if "flipkart" in pl_lower else "b-other")
            best_tag = ' <span class="badge b-best">🏆 Best Price</span>' if is_best else ""
            p_cls    = "c-green" if is_best else ""

            # Product image
            thumb    = row.get("thumbnail", "")
            img_html = (
                f'<img src="{thumb}" style="width:90px;height:90px;object-fit:contain;'
                f'border-radius:12px;background:rgba(255,255,255,0.05);'
                f'padding:6px;float:right;margin:0 0 8px 14px;">'
            ) if thumb else ""

            # Rating
            rating = row.get("rating", 0)
            stars  = ""
            if rating > 0:
                full = int(rating)
                stars = "★" * full + ("½" if rating - full >= 0.5 else "") + "☆" * (5 - full - (1 if rating - full >= 0.5 else 0))
                r_html = f'<span style="color:#f59e0b">{stars}</span> <span style="color:#94a3b8;font-size:0.82rem">{rating}</span>'
            else:
                r_html = ""

            rc      = row.get("reviews_count", 0)
            rc_html = f' <span class="c-muted" style="font-size:0.8rem">· {fmt_num(rc)} reviews</span>' if rc else ""

            # Prime / seller badge
            badge_str = row.get("badge", "")
            prime_html = ' <span class="badge" style="background:rgba(0,168,225,0.15);color:#00a8e1;border:1px solid rgba(0,168,225,0.3)">Prime</span>' if badge_str == "Prime" else ""

            # Safe URL (ensure external)
            url = row["url"]
            if not url.startswith("http"):
                url = "https://" + url

            # Savings marker
            if is_best and savings > 0:
                save_html = f'<span style="background:rgba(16,185,129,0.12);color:#10b981;border-radius:6px;padding:2px 8px;font-size:0.75rem;margin-left:8px">Save ₹{savings:,} vs highest</span>'
            else:
                save_html = ""

            st.markdown(f"""
            <div class="card">
                <div class="card-top-bar"></div>
                {img_html}
                <span class="badge {b_cls}">{pl}</span>{best_tag}{prime_html}{save_html}
                <br>
                <b style="font-size:0.97rem;color:#e2e8f0;line-height:1.4">{row['title'][:100]}</b>
                <br>
                <span class="price-tag {p_cls}">₹{row['price']:,}</span>
                &nbsp;&nbsp;{r_html}{rc_html}
                <br>
                <a href="{url}"
                   target="_blank"
                   rel="noopener noreferrer"
                   onclick="window.open('{url}','_blank','noopener,noreferrer');return false;"
                   style="color:#818cf8;font-size:0.84rem;text-decoration:none;
                          margin-top:8px;display:inline-flex;align-items:center;gap:4px;
                          border:1px solid rgba(129,140,248,0.3);padding:4px 12px;
                          border-radius:8px;">
                   🛒 Buy on {pl} <span style="font-size:0.9rem">↗</span>
                </a>
            </div>""", unsafe_allow_html=True)

        # Price bar chart — use title+platform as x-label for uniqueness
        bar_labels  = [f"{row['platform']}\n₹{row['price']:,}" for _, row in df.iterrows()]
        bar_colors  = [PLATFORM_COLORS.get(row["platform"], "#6366f1") for _, row in df.iterrows()]
        fig_price   = go.Figure(go.Bar(
            x=bar_labels,
            y=df["price"].tolist(),
            text=[f"₹{p:,}" for p in df["price"]],
            textposition="outside",
            marker_color=bar_colors,
            hovertemplate="<b>%{x}</b><br>₹%{y:,}<extra></extra>",
        ))
        st.plotly_chart(
            dark_chart(fig_price, "Live Price Comparison — All Platforms"),
            use_container_width=True
        )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — COMMUNITY REVIEWS (REDDIT)
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown('<div class="sec-lbl">⭐ E-Commerce User Reviews</div>', unsafe_allow_html=True)
        if "eco_reviews" in errs:
            st.warning(f"Note: {errs['eco_reviews']}")
        amz_reviews = eco_reviews.get("amazon", [])
        fk_reviews  = eco_reviews.get("flipkart", [])
        web_reviews = eco_reviews.get("web", [])
        total_eco   = len(amz_reviews) + len(fk_reviews) + len(web_reviews)
        if total_eco == 0:
            st.info("🧹 No scraped reviews yet. Amazon/Flipkart may have served a CAPTCHA. Try a different query.")
        else:
            st.markdown(f"""
            <div class="card">
                <div class="card-top-bar"></div>
                <span style="color:#818cf8;font-size:0.85rem;font-weight:600">📈 Review Sources</span><br>
                <span class="badge b-amazon">Amazon.in</span> <b style="color:#FF9900">{len(amz_reviews)}</b> reviews
                &nbsp;&nbsp;
                <span class="badge b-flipkart">Flipkart</span> <b style="color:#4d90fe">{len(fk_reviews)}</b> reviews
                &nbsp;&nbsp;
                <span class="badge b-other">Web</span> <b style="color:#6366f1">{len(web_reviews)}</b> results
            </div>""", unsafe_allow_html=True)
        eco_stabs = st.tabs(["🟡 Amazon.in", "🔵 Flipkart", "🌐 Web Reviews"])
        with eco_stabs[0]:
            if not amz_reviews:
                st.info("Amazon reviews not available. Amazon may have served a CAPTCHA page.")
            else:
                from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as _VDREC
                _vdr = _VDREC()
                for rev in amz_reviews:
                    _cp  = _vdr.polarity_scores(rev)["compound"]
                    _lbl = "pos" if _cp >= 0.05 else ("neg" if _cp <= -0.05 else "")
                    _ico = "✅" if _lbl == "pos" else ("❌" if _lbl == "neg" else "🔵")
                    st.markdown(f'<div class="cci {_lbl}">{_ico} {rev}</div>', unsafe_allow_html=True)
        with eco_stabs[1]:
            if not fk_reviews:
                st.info("Flipkart reviews not scraped (CSS selectors may have changed).")
            else:
                for rev in fk_reviews:
                    st.markdown(f'<div class="cci">🔵 {rev}</div>', unsafe_allow_html=True)
        with eco_stabs[2]:
            if not web_reviews:
                st.info("No web reviews found for this product.")
            else:
                for _item in web_reviews:
                    _tx  = _item["text"] if isinstance(_item, dict) else _item
                    _src = _item.get("source", "") if isinstance(_item, dict) else ""
                    _st  = f'<span style="color:#64748b;font-size:0.75rem">({_src})</span>' if _src else ""
                    st.markdown(f'<div class="cci">🌐 {_tx} {_st}</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="sec-lbl">🌐 Community Reviews — Reddit</div>', unsafe_allow_html=True)

        if "reddit" in errs:
            st.error(f"Reddit unavailable: {errs['reddit']}")
        elif not reddit_data:
            st.warning("No Reddit discussions found.")
        else:
            texts   = [r["text"] for r in reddit_data]
            sent    = analyze_sentiment(texts)
            sc      = sent["score"]
            col_   = score_color(sc)

            col_sc, col_bar = st.columns([1, 2])
            with col_sc:
                st.markdown(f"""
                <div class="card" style="text-align:center;padding:2rem 1rem;">
                    <div class="card-top-bar"></div>
                    <div style="font-size:0.7rem;color:#475569;text-transform:uppercase;letter-spacing:0.08em">Community Score</div>
                    <div style="font-family:'Outfit',sans-serif;font-size:3.5rem;font-weight:800;color:{col_};line-height:1.1;margin:0.3rem 0">{sc}</div>
                    <div style="color:{col_};font-size:0.88rem">/ 100</div>
                    <div style="color:#475569;font-size:0.78rem;margin-top:0.8rem">{len(texts)} discussions analysed</div>
                </div>""", unsafe_allow_html=True)
            with col_bar:
                st.plotly_chart(
                    sentiment_stacked_bar(sent["positive"], sent["neutral"], sent["negative"]),
                    use_container_width=True
                )
                # Compound histogram
                if sent["compound_scores"]:
                    fig_h = px.histogram(
                        x=sent["compound_scores"], nbins=20,
                        color_discrete_sequence=["#6366f1"],
                        labels={"x": "Compound Score", "y": "Count"},
                    )
                    st.plotly_chart(
                        dark_chart(fig_h, "Sentiment Score Distribution", height=180),
                        use_container_width=True
                    )

            # Issues / Positives
            col_i, col_p = st.columns(2)
            with col_i:
                st.markdown('<div class="sec-lbl" style="font-size:1rem">🔴 Top Issues</div>', unsafe_allow_html=True)
                for iss in sent["top_issues"]:
                    st.markdown(f'<div class="cci neg">🔸 {iss}</div>', unsafe_allow_html=True)
            with col_p:
                st.markdown('<div class="sec-lbl" style="font-size:1rem">🟢 What People Love</div>', unsafe_allow_html=True)
                for pos in sent["top_positives"]:
                    st.markdown(f'<div class="cci pos">✨ {pos}</div>', unsafe_allow_html=True)

            # Aspect radar
            asp = sent.get("aspect_scores", {})
            if asp:
                fig_asp = go.Figure(go.Scatterpolar(
                    r=[v["score"] for v in asp.values()],
                    theta=list(asp.keys()),
                    fill="toself",
                    line_color="#6366f1",
                    fillcolor="rgba(99,102,241,0.15)",
                ))
                fig_asp.update_layout(
                    polar=dict(
                        bgcolor="rgba(0,0,0,0)",
                        radialaxis=dict(visible=True, range=[0, 100],
                                        gridcolor="rgba(255,255,255,0.08)",
                                        tickfont=dict(color="#64748b")),
                        angularaxis=dict(gridcolor="rgba(255,255,255,0.08)",
                                         tickfont=dict(color="#94a3b8")),
                    ),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#94a3b8"),
                    title=dict(text="Aspect Sentiment Radar", font=dict(color="#e2e8f0", family="Outfit")),
                    margin=dict(t=60, l=30, r=30, b=30),
                )
                st.plotly_chart(fig_asp, use_container_width=True)

            # Discussions feed
            st.markdown('<div class="sec-lbl">💬 Reddit Discussions</div>', unsafe_allow_html=True)
            for r in reddit_data[:20]:
                from utils.sentiment import classify_text
                lbl = classify_text(r["text"])
                icon = "🟢" if lbl == "positive" else ("🔴" if lbl == "negative" else "🟡")
                t_lbl = "📝 Post" if r.get("type") == "post" else "💬 Comment"
                sub   = f' · r/{r["subreddit"]}' if r.get("subreddit") else ""
                sc_r  = f' · ▲ {fmt_num(r["score"])}' if r.get("score", 0) > 0 else ""
                link  = f'<a href="{r["url"]}" target="_blank" style="color:#818cf8;font-size:0.76rem">View →</a>' if r.get("url") else ""
                preview = r["text"][:240] + ("…" if len(r["text"]) > 240 else "")
                st.markdown(f"""
                <div class="cci {lbl}">
                    {icon} <span style="font-size:0.73rem;color:#475569">{t_lbl}{sub}{sc_r}</span><br>
                    {preview}<br>{link}
                </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — YOUTUBE REVIEWS
    # ══════════════════════════════════════════════════════════════════════════
    with tab4:
        st.markdown('<div class="sec-lbl">🎥 YouTube Review Intelligence</div>', unsafe_allow_html=True)

        if "youtube" in errs:
            st.error(f"YouTube unavailable: {errs['youtube']}")
        elif not yt_anal:
            st.warning("No YouTube reviews found.")
        else:
            ya = yt_anal
            sc_yt  = ya["overall_score"]
            col_yt = score_color(sc_yt)

            # Metric row
            c1, c2, c3, c4, c5 = st.columns(5)
            for col, val, lbl, clr in [
                (c1, str(sc_yt),                   "YouTube Score",     col_yt),
                (c2, fmt_num(ya["total_views"]),    "Total Views",       "#818cf8"),
                (c3, fmt_num(ya["total_likes"]),    "Total Likes",       "#10b981"),
                (c4, str(ya["total_videos"]),       "Videos Analysed",  "#f59e0b"),
                (c5, str(ya["total_comments"]),     "Comments Analysed","#06b6d4"),
            ]:
                with col:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-val" style="color:{clr}">{val}</div>
                        <div class="metric-lbl">{lbl}</div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Row 1: Sentiment donut + Aspect radar
            col_d, col_r = st.columns(2)
            with col_d:
                fig_donut = go.Figure(go.Pie(
                    labels=["Positive", "Neutral", "Negative"],
                    values=[ya["positive_pct"], ya["neutral_pct"], ya["negative_pct"]],
                    hole=0.62,
                    marker_colors=["#10b981", "#f59e0b", "#ef4444"],
                    textinfo="label+percent",
                    textfont=dict(color="#e2e8f0"),
                    hovertemplate="%{label}: %{value}%<extra></extra>",
                ))
                fig_donut.add_annotation(
                    text=f"<b>{sc_yt}</b>", x=0.5, y=0.5,
                    font_size=32, font_color=col_yt, showarrow=False
                )
                fig_donut.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#94a3b8"),
                    title=dict(text="Overall Comment Sentiment", font=dict(color="#e2e8f0", family="Outfit")),
                    legend=dict(font=dict(color="#94a3b8"), orientation="h", x=0.1, y=-0.05),
                    margin=dict(t=50, l=0, r=0, b=30),
                )
                st.plotly_chart(fig_donut, use_container_width=True)

            with col_r:
                asp_yt = ya.get("aspect_scores", {})
                if asp_yt:
                    fig_asp_yt = go.Figure(go.Scatterpolar(
                        r=[v["score"] for v in asp_yt.values()],
                        theta=list(asp_yt.keys()),
                        fill="toself",
                        line_color="#f59e0b",
                        fillcolor="rgba(245,158,11,0.12)",
                    ))
                    fig_asp_yt.update_layout(
                        polar=dict(
                            bgcolor="rgba(0,0,0,0)",
                            radialaxis=dict(visible=True, range=[0,100],
                                            gridcolor="rgba(255,255,255,0.08)",
                                            tickfont=dict(color="#64748b")),
                            angularaxis=dict(gridcolor="rgba(255,255,255,0.08)",
                                             tickfont=dict(color="#94a3b8")),
                        ),
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#94a3b8"),
                        title=dict(text="Aspect Scores from Comments", font=dict(color="#e2e8f0", family="Outfit")),
                        margin=dict(t=60, l=30, r=30, b=30),
                    )
                    st.plotly_chart(fig_asp_yt, use_container_width=True)

            # Row 2: Comment sentiment distribution histogram
            if ya["compound_scores"]:
                fig_hist = px.histogram(
                    x=ya["compound_scores"], nbins=25,
                    color_discrete_sequence=["#6366f1"],
                    labels={"x": "Compound Sentiment Score", "y": "Comment Count"},
                )
                st.plotly_chart(
                    dark_chart(fig_hist, "Comment Sentiment Distribution"),
                    use_container_width=True
                )

            # Row 3: Engagement bar chart (views per video)
            if ya["videos"]:
                top_vids = sorted(ya["videos"], key=lambda x: x["view_count"], reverse=True)[:8]
                vid_titles = [v["title"][:35] + "…" for v in top_vids]
                fig_eng = go.Figure()
                fig_eng.add_trace(go.Bar(
                    name="Views", x=vid_titles,
                    y=[v["view_count"] for v in top_vids],
                    marker_color="#6366f1",
                    hovertemplate="<b>%{x}</b><br>Views: %{y:,}<extra></extra>",
                ))
                fig_eng.add_trace(go.Bar(
                    name="Likes", x=vid_titles,
                    y=[v["like_count"] for v in top_vids],
                    marker_color="#10b981",
                    hovertemplate="<b>%{x}</b><br>Likes: %{y:,}<extra></extra>",
                ))
                fig_eng.update_layout(barmode="group")
                st.plotly_chart(
                    dark_chart(fig_eng, "Video Engagement (Top Videos by Views)"),
                    use_container_width=True
                )

            # Row 4: Channel distribution pie
            if ya["channel_counts"]:
                ch_names = list(ya["channel_counts"].keys())
                ch_vals  = list(ya["channel_counts"].values())
                fig_ch = go.Figure(go.Pie(
                    labels=ch_names, values=ch_vals,
                    textinfo="label+percent",
                    textfont=dict(color="#e2e8f0"),
                    marker=dict(colors=px.colors.qualitative.Set2),
                    hole=0.45,
                ))
                fig_ch.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#94a3b8"),
                    title=dict(text="Review Channel Distribution", font=dict(color="#e2e8f0", family="Outfit")),
                    legend=dict(font=dict(color="#94a3b8")),
                    margin=dict(t=50, l=0, r=0, b=20),
                )
                st.plotly_chart(fig_ch, use_container_width=True)

            # Top positive / negative comments
            col_tp, col_tn = st.columns(2)
            with col_tp:
                st.markdown('<div class="sec-lbl" style="font-size:1rem">🟢 Top Positive Comments</div>', unsafe_allow_html=True)
                for c in ya["top_positive"]:
                    likes_html = f'<span style="color:#10b981;font-size:0.76rem">👍 {c["likes"]}</span>' if c.get("likes") else ""
                    st.markdown(f"""
                    <div class="cci pos">
                        <span style="font-size:0.73rem;color:#475569">{c.get("author","")} · {c.get("video_title","")[:40]}…</span><br>
                        {c["text"][:200]}<br>{likes_html}
                    </div>""", unsafe_allow_html=True)

            with col_tn:
                st.markdown('<div class="sec-lbl" style="font-size:1rem">🔴 Top Critical Comments</div>', unsafe_allow_html=True)
                for c in ya["top_negative"]:
                    likes_html = f'<span style="color:#ef4444;font-size:0.76rem">👍 {c["likes"]}</span>' if c.get("likes") else ""
                    st.markdown(f"""
                    <div class="cci neg">
                        <span style="font-size:0.73rem;color:#475569">{c.get("author","")} · {c.get("video_title","")[:40]}…</span><br>
                        {c["text"][:200]}<br>{likes_html}
                    </div>""", unsafe_allow_html=True)

            # Video cards
            st.markdown('<div class="sec-lbl">📺 Review Videos</div>', unsafe_allow_html=True)
            for v in sorted(ya["videos"], key=lambda x: x["view_count"], reverse=True)[:10]:
                lbl = v.get("sentiment", "neutral")
                icon = "🟢" if lbl == "positive" else ("🔴" if lbl == "negative" else "🟡")
                thumb_html = f'<img src="{v["thumbnail"]}" alt="">' if v.get("thumbnail") else ""
                st.markdown(f"""
                <div class="yt-row">
                    {thumb_html}
                    <div>
                        <a href="{v['url']}" target="_blank"
                           style="font-weight:600;font-size:0.9rem;color:#e2e8f0;text-decoration:none">
                           {icon} {v['title'][:80]}
                        </a>
                        <div class="yt-meta">
                            📺 {v['channel']} &nbsp;·&nbsp;
                            👁 {fmt_num(v['view_count'])} views &nbsp;·&nbsp;
                            👍 {fmt_num(v['like_count'])} likes &nbsp;·&nbsp;
                            💬 {fmt_num(v['comment_count'])} comments
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 — INTELLIGENCE DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════
    # ──────────────────────────────────────────────────────────────────────────
    # TAB 5 — DEEP NLP ANALYSIS
    # ──────────────────────────────────────────────────────────────────────────
    with tab5:
        st.markdown('<div class="sec-lbl">🧠 Deep NLP Text Analytics</div>', unsafe_allow_html=True)

        if not all_review_texts:
            st.info("🔍 Run a search first. Deep NLP combines text from Reddit, YouTube, and E-commerce tabs.")
        else:
            with st.spinner("🧠 Running full NLP pipeline... (20-40 seconds)"):
                try:
                    nlp_result = run_deep_nlp(json.dumps(all_review_texts))
                except Exception as _nlpe:
                    nlp_result = {}
                    st.error(f"NLP error: {_nlpe}")

            if nlp_result:
                vs = nlp_result.get("vocab", {})
                st.markdown("#### 📊 Corpus Statistics")
                _vc1, _vc2, _vc3, _vc4, _vc5, _vc6 = st.columns(6)
                for _col, _val, _lbl, _clr in [
                    (_vc1, vs.get("total_reviews", 0),           "Reviews",          "#818cf8"),
                    (_vc2, vs.get("total_tokens", 0),            "Total Tokens",     "#06b6d4"),
                    (_vc3, vs.get("unique_tokens", 0),           "Unique Words",     "#10b981"),
                    (_vc4, f"{vs.get('vocab_richness_pct', 0)}%","Vocab Richness",   "#f59e0b"),
                    (_vc5, vs.get("avg_words_per_review", 0),    "Avg Words/Review", "#ec4899"),
                    (_vc6, vs.get("total_sentences", 0),         "Sentences",        "#a78bfa"),
                ]:
                    with _col:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-val" style="color:{_clr};font-size:1.5rem">{_val}</div>
                            <div class="metric-lbl">{_lbl}</div>
                        </div>""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # BoW + TF-IDF
                st.markdown("#### 🧺 Bag of Words vs TF-IDF")
                _cbw, _ctf = st.columns(2)
                _bow = nlp_result.get("bow", {})
                if _bow:
                    with _cbw:
                        _fbw = go.Figure(go.Bar(x=list(_bow.values())[:20], y=list(_bow.keys())[:20],
                                                orientation="h", marker_color="#818cf8",
                                                hovertemplate="<b>%{y}</b>: %{x}<extra></extra>"))
                        _fbw.update_layout(yaxis=dict(autorange="reversed"))
                        st.plotly_chart(dark_chart(_fbw, "Bag of Words — Top 20 Tokens", height=420), use_container_width=True)
                _tfi = nlp_result.get("tfidf", {})
                if _tfi:
                    with _ctf:
                        _ftf = go.Figure(go.Bar(x=list(_tfi.values())[:20], y=list(_tfi.keys())[:20],
                                                orientation="h", marker_color="#10b981",
                                                hovertemplate="<b>%{y}</b>: %{x:.4f}<extra></extra>"))
                        _ftf.update_layout(yaxis=dict(autorange="reversed"))
                        st.plotly_chart(dark_chart(_ftf, "TF-IDF — Top Terms by Importance", height=420), use_container_width=True)

                # N-grams
                st.markdown("#### 🔗 N-gram Analysis (Bigrams · Trigrams)")
                _cbi, _ctr = st.columns(2)
                _big = nlp_result.get("bigrams", {})
                if _big:
                    with _cbi:
                        _fbi = go.Figure(go.Bar(x=list(_big.values()), y=list(_big.keys()),
                                                orientation="h", marker_color="#f59e0b"))
                        _fbi.update_layout(yaxis=dict(autorange="reversed"))
                        st.plotly_chart(dark_chart(_fbi, "Top Bigrams", height=380), use_container_width=True)
                _tri = nlp_result.get("trigrams", {})
                if _tri:
                    with _ctr:
                        _ftr = go.Figure(go.Bar(x=list(_tri.values()), y=list(_tri.keys()),
                                                orientation="h", marker_color="#ec4899"))
                        _ftr.update_layout(yaxis=dict(autorange="reversed"))
                        st.plotly_chart(dark_chart(_ftr, "Top Trigrams", height=380), use_container_width=True)

                # LDA Topics
                _topics = [t for t in nlp_result.get("topics", []) if "doc_share" in t]
                if _topics:
                    st.markdown("#### 🛸 Topic Modeling — LDA (Latent Dirichlet Allocation)")
                    _tpal = ["#818cf8", "#10b981", "#f59e0b", "#ec4899", "#06b6d4"]
                    _tc = st.columns(len(_topics))
                    for _i, (_tcc, _tp) in enumerate(zip(_tc, _topics)):
                        _clr = _tpal[_i % len(_tpal)]
                        with _tcc:
                            _kws = _tp["keywords"][:6]
                            st.markdown(f"""
                            <div class="card" style="text-align:center">
                                <div class="card-top-bar" style="background:{_clr}"></div>
                                <b style="color:{_clr};font-family:'Outfit',sans-serif">📂 Topic {_tp['id']}</b><br>
                                <span style="color:#94a3b8;font-size:0.75rem">{_tp['name']}</span><br>
                                <span style="color:#64748b;font-size:0.78rem">{_tp['doc_share']}% of docs</span>
                                <hr style="border-color:rgba(255,255,255,0.07);margin:8px 0">
                                {''.join(f'<span class="badge b-other" style="margin:2px;font-size:0.7rem">{k}</span>' for k in _kws)}
                            </div>""", unsafe_allow_html=True)

                # Clustering
                _cls = nlp_result.get("clusters", {})
                if _cls and _cls.get("labels"):
                    st.markdown("#### 🎯 K-Means Clustering (PCA 2D Projection)")
                    _cpal = ["#818cf8", "#10b981", "#f59e0b", "#ec4899", "#06b6d4"]
                    _labs = _cls["labels"]
                    _tsmp = all_review_texts[:len(_labs)]
                    _fcl  = go.Figure()
                    for _ki in range(_cls["k"]):
                        _kidx = [_ii for _ii, _ll in enumerate(_labs) if _ll == _ki]
                        _kkws = ", ".join(_cls["keywords"].get(_ki, []))
                        _fcl.add_trace(go.Scatter(
                            x=[_cls["x"][_ii] for _ii in _kidx],
                            y=[_cls["y"][_ii] for _ii in _kidx],
                            mode="markers", name=f"Cluster {_ki+1}: {_kkws}",
                            marker=dict(color=_cpal[_ki % len(_cpal)], size=8, opacity=0.75),
                            text=[_tsmp[_ii][:60] if _ii < len(_tsmp) else "" for _ii in _kidx],
                            hovertemplate="%{text}<extra>Cluster " + str(_ki+1) + "</extra>"
                        ))
                    st.plotly_chart(dark_chart(_fcl, "Review Clusters — Similar Reviews Grouped"), use_container_width=True)

                # NER
                _ner = nlp_result.get("ner", {})
                _nc  = _ner.get("counts", {})
                _nex = _ner.get("examples", {})
                if _nc:
                    st.markdown("#### 🔖 Named Entity Recognition (NER)")
                    _cn, _cne = st.columns([1, 1])
                    with _cn:
                        _fn = go.Figure(go.Bar(
                            x=list(_nc.values()),
                            y=[_ner.get("labels", {}).get(k, k) for k in _nc.keys()],
                            orientation="h", marker_color="#a78bfa"))
                        _fn.update_layout(yaxis=dict(autorange="reversed"))
                        st.plotly_chart(dark_chart(_fn, "Entity Type Distribution", height=280), use_container_width=True)
                    with _cne:
                        for _et, _exs in list(_nex.items())[:4]:
                            _nice = _ner.get("labels", {}).get(_et, _et)
                            _ehtml = " · ".join(f"`{e}`" for e in _exs[:4])
                            st.markdown(f"**{_nice}**: {_ehtml}")

                # Naive Bayes
                _nb = nlp_result.get("nb", {})
                if _nb and _nb.get("top_features"):
                    st.markdown("#### 🧠 Naive Bayes — Discriminative Words per Sentiment Class")
                    _nbcols = st.columns(len(_nb["top_features"]))
                    _clsclr = {"positive": "#10b981", "negative": "#ef4444", "neutral": "#f59e0b"}
                    for _nbc, (_cn2, _fts) in zip(_nbcols, _nb["top_features"].items()):
                        _clr2 = _clsclr.get(_cn2, "#818cf8")
                        _cnt  = _nb.get("label_dist", {}).get(_cn2, 0)
                        with _nbc:
                            st.markdown(f"""
                            <div class="card">
                                <div class="card-top-bar" style="background:{_clr2}"></div>
                                <b style="color:{_clr2}">{_cn2.title()}</b>
                                <span style="color:#64748b;font-size:0.75rem"> ({_cnt})</span><br><br>
                                {''.join(f'<div style="color:#cbd5e1;font-size:0.82rem;padding:2px 0">• {f}</div>' for f in _fts[:8])}
                            </div>""", unsafe_allow_html=True)

                # Extractive Summary
                _sum = nlp_result.get("summary", "")
                if _sum:
                    st.markdown("#### 📝 Extractive Summary (TF-IDF Sentence Scoring)")
                    for _s in _sum.split(" … "):
                        st.markdown(f"""
                        <div class="card" style="border-left:3px solid #818cf8;padding-left:16px">
                            <div class="card-top-bar"></div>
                            <span style="color:#e2e8f0;font-size:0.92rem;line-height:1.7;font-style:italic">"{_s}"</span>
                        </div>""", unsafe_allow_html=True)

    with tab6:
        st.markdown('<div class="sec-lbl">📊 Combined Intelligence Dashboard</div>', unsafe_allow_html=True)

        # Combine all text sources
        all_texts = [r["text"] for r in reddit_data]
        if yt_anal:
            all_texts += [c["text"] for c in yt_anal.get("comments", [])]

        combined = get_combined_score(all_texts) if all_texts else {
            "score": 0, "positive": 0, "negative": 0, "neutral": 0,
            "top_issues": [], "top_positives": [], "aspect_scores": {},
        }

        ov_score  = combined["score"]
        yt_score  = yt_anal["overall_score"] if yt_anal else 0
        reddit_sc = analyze_sentiment([r["text"] for r in reddit_data])["score"] if reddit_data else 0

        v_icon, v_text = verdict(ov_score)
        v_color = score_color(ov_score)

        # Top 4 metrics
        c1, c2, c3, c4 = st.columns(4)
        best = min(products, key=lambda x: x["price"])
        for col, val, lbl, clr in [
            (c1, str(ov_score),        "Combined Score",   v_color),
            (c2, str(yt_score),        "YouTube Score",    "#818cf8"),
            (c3, str(reddit_sc),       "Reddit Score",     "#ff6534"),
            (c4, f"₹{best['price']:,}", "Best Price",      "#10b981"),
        ]:
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val" style="color:{clr}">{val}</div>
                    <div class="metric-lbl">{lbl}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Verdict card
        st.markdown(f"""
        <div class="card" style="text-align:center;border-color:{v_color};padding:2rem;">
            <div class="card-top-bar"></div>
            <div style="font-size:3rem">{v_icon}</div>
            <div style="font-family:'Outfit',sans-serif;font-size:2rem;font-weight:800;color:{v_color};margin-top:0.3rem">{v_text}</div>
            <div style="color:#475569;margin-top:0.6rem;font-size:0.9rem">
                Best deal: <b style="color:#f59e0b">{best['platform']}</b> at <b style="color:#f59e0b">₹{best['price']:,}</b>
            </div>
            <div style="color:#475569;font-size:0.8rem;margin-top:0.3rem">Based on {len(all_texts)} real user opinions</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # OpenRouter AI Recommendation
        if product_query.strip():
            with st.spinner("🤖 Generating Trinity AI Advice..."):
                asp_str = ", ".join([f"{k}:{v['score']}" for k, v in combined.get("aspect_scores", {}).items()][:5])
                ai_advice = get_ai_verdict(
                    product_name=product_query,
                    best_price=f"{best['price']:,}",
                    ov_score=ov_score,
                    yt_score=yt_score,
                    reddit_sc=reddit_sc,
                    aspect_scores=asp_str
                )
            
            st.markdown(f"""
            <div class="card" style="border-left: 4px solid #8b5cf6; padding-left: 1.5rem; background: rgba(139, 92, 246, 0.03);">
                <div class="card-top-bar" style="background: #8b5cf6;"></div>
                <h4 style="color: #c4b5fd; margin-top: 0;">✨ AI Purchase Recommendation</h4>
                <div style="color: #e2e8f0; font-size: 0.95rem; line-height: 1.6; font-family: 'Inter', sans-serif;">
                    {ai_advice}
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        # Combined sentiment donut
        col_donut2, col_scores = st.columns(2)
        with col_donut2:
            fig_comb = go.Figure(go.Pie(
                labels=["Positive", "Neutral", "Negative"],
                values=[combined["positive"], combined["neutral"], combined["negative"]],
                hole=0.62,
                marker_colors=["#10b981", "#f59e0b", "#ef4444"],
                textinfo="label+percent",
                textfont=dict(color="#e2e8f0"),
            ))
            fig_comb.add_annotation(
                text=f"<b>{ov_score}</b>", x=0.5, y=0.5,
                font_size=30, font_color=v_color, showarrow=False
            )
            fig_comb.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8"),
                title=dict(text="Combined Sentiment Breakdown", font=dict(color="#e2e8f0", family="Outfit")),
                legend=dict(font=dict(color="#94a3b8"), orientation="h", x=0.1, y=-0.05),
                margin=dict(t=50, l=0, r=0, b=30),
            )
            st.plotly_chart(fig_comb, use_container_width=True)

        with col_scores:
            # Source comparison bar
            sources  = ["Reddit", "YouTube"]
            s_scores = [reddit_sc, yt_score]
            s_colors = ["#ff6534", "#ff4444"]
            fig_src = go.Figure(go.Bar(
                x=sources, y=s_scores,
                marker_color=s_colors,
                text=[f"{s}%" for s in s_scores], textposition="outside",
                hovertemplate="<b>%{x}</b>: %{y}%<extra></extra>",
            ))
            fig_src.update_layout(yaxis=dict(range=[0, 105]))
            st.plotly_chart(
                dark_chart(fig_src, "Score by Data Source"),
                use_container_width=True
            )

        # Aspect radar combining both sources
        all_asp = {}
        for src in [combined.get("aspect_scores", {}),
                    (yt_anal or {}).get("aspect_scores", {})]:
            for asp, val in src.items():
                if asp not in all_asp:
                    all_asp[asp] = []
                all_asp[asp].append(val["score"])
        avg_asp = {k: round(sum(v)/len(v)) for k, v in all_asp.items()}

        if avg_asp:
            fig_final_asp = go.Figure()
            fig_final_asp.add_trace(go.Scatterpolar(
                r=list(avg_asp.values()),
                theta=list(avg_asp.keys()),
                fill="toself",
                name="All Sources",
                line_color="#818cf8",
                fillcolor="rgba(129,140,248,0.15)",
            ))
            fig_final_asp.update_layout(
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(visible=True, range=[0,100],
                                    gridcolor="rgba(255,255,255,0.08)",
                                    tickfont=dict(color="#64748b")),
                    angularaxis=dict(gridcolor="rgba(255,255,255,0.08)",
                                     tickfont=dict(color="#94a3b8")),
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8"),
                title=dict(text="Combined Aspect Intelligence", font=dict(color="#e2e8f0", family="Outfit")),
                margin=dict(t=60, l=30, r=30, b=30),
            )
            st.plotly_chart(fig_final_asp, use_container_width=True)

        # Issues + Highlights
        col_ii, col_hi = st.columns(2)
        with col_ii:
            st.markdown('<div class="sec-lbl" style="font-size:1rem">🔴 Top Issues Across All Sources</div>', unsafe_allow_html=True)
            for iss in combined["top_issues"]:
                st.markdown(f'<div class="cci neg">🔸 {iss}</div>', unsafe_allow_html=True)
        with col_hi:
            st.markdown('<div class="sec-lbl" style="font-size:1rem">🟢 Top Highlights</div>', unsafe_allow_html=True)
            for pos in combined["top_positives"]:
                st.markdown(f'<div class="cci pos">✨ {pos}</div>', unsafe_allow_html=True)

elif go_btn and not product_query.strip():
    st.warning("Please enter a product name to search.")

else:
    st.markdown("""
    <div class="landing">
        <div class="landing-icon">🛒</div>
        <div style="font-family:'Outfit',sans-serif;font-size:1.5rem;font-weight:700;color:#1e293b;margin-top:1rem">
            Search any product to get started
        </div>
        <div style="color:#334155;font-size:0.9rem;margin-top:0.5rem">
            Live prices · Reddit community opinions · YouTube review analysis · AI verdict
        </div>
    </div>
    """, unsafe_allow_html=True)
