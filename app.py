import streamlit as st
import pandas as pd
from utils.sentiment import analyze_sentiment, get_combined_score
from utils.search import fetch_products
from utils.reddit import fetch_reddit_opinions
import plotly.express as px
import plotly.graph_objects as go

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BuySmart AI",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');

* { font-family: 'DM Sans', sans-serif; }
h1, h2, h3, .big-title { font-family: 'Syne', sans-serif !important; }

/* Background */
.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    color: #f0f0f0;
}

/* Hide default Streamlit elements */
#MainMenu, footer, header { visibility: hidden; }

/* Hero */
.hero {
    text-align: center;
    padding: 3rem 1rem 2rem;
}
.hero h1 {
    font-size: 3.5rem;
    font-weight: 800;
    background: linear-gradient(90deg, #f7971e, #ffd200);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.3rem;
}
.hero p {
    color: #aaa;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}

/* Cards */
.card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    backdrop-filter: blur(10px);
}

/* Platform badge */
.platform-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}
.amazon  { background: #FF9900; color: #000; }
.flipkart{ background: #2874f0; color: #fff; }
.reddit  { background: #FF4500; color: #fff; }
.combined{ background: linear-gradient(90deg,#f7971e,#ffd200); color:#000; }

/* Metric box */
.metric-box {
    background: rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.1);
}
.metric-box .value {
    font-size: 2rem;
    font-weight: 700;
    font-family: 'Syne', sans-serif;
}
.metric-box .label {
    font-size: 0.8rem;
    color: #aaa;
    margin-top: 4px;
}

/* Search bar */
.stTextInput input {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 12px !important;
    color: white !important;
    font-size: 1.1rem !important;
    padding: 0.8rem 1rem !important;
}
.stButton > button {
    background: linear-gradient(90deg, #f7971e, #ffd200) !important;
    color: #000 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.7rem 2rem !important;
    font-size: 1rem !important;
    width: 100%;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    color: #aaa;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(90deg, #f7971e, #ffd200) !important;
    color: #000 !important;
    font-weight: 700 !important;
}

/* Sentiment color helpers */
.pos { color: #4ade80; font-weight: 600; }
.neg { color: #f87171; font-weight: 600; }
.neu { color: #facc15; font-weight: 600; }

/* Review item */
.review-item {
    border-left: 3px solid rgba(255,255,255,0.15);
    padding: 0.6rem 1rem;
    margin-bottom: 0.5rem;
    background: rgba(255,255,255,0.03);
    border-radius: 0 8px 8px 0;
    font-size: 0.9rem;
    color: #ccc;
}

/* Price table */
.price-best { color: #4ade80; font-weight: 700; }
.price-tag {
    font-size: 1.4rem;
    font-weight: 800;
    font-family: 'Syne', sans-serif;
}
</style>
""", unsafe_allow_html=True)


# ── Hero Section ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🛒 BuySmart AI</h1>
    <p>Compare prices · Analyse reviews · Make smarter decisions</p>
</div>
""", unsafe_allow_html=True)

# ── Search Bar ────────────────────────────────────────────────────────────────
col1, col2 = st.columns([5, 1])
with col1:
    product_query = st.text_input("", placeholder="e.g. iPhone 15, Nike Air Max, Samsung TV...", label_visibility="collapsed")
with col2:
    search_clicked = st.button("🔍 Search")

# ── Main Logic ────────────────────────────────────────────────────────────────
if search_clicked and product_query.strip():
    with st.spinner("🔎 Fetching prices & reviews..."):
        products   = fetch_products(product_query)
        reddit_data = fetch_reddit_opinions(product_query)

    if not products:
        st.error("No results found. Try a different product name.")
        st.stop()

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["💰 Price Comparison", "💬 Review Intelligence", "📊 Combined Dashboard"])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1 — Price Comparison
    # ════════════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown("### 💰 Price Comparison")

        df = pd.DataFrame(products)[["platform", "title", "price", "rating", "url"]]
        df = df.sort_values("price")
        best_price = df.iloc[0]["price"]

        for _, row in df.iterrows():
            is_best = row["price"] == best_price
            badge_class = row["platform"].lower().replace(" ", "")
            badge_class = "amazon" if "amazon" in badge_class else ("flipkart" if "flipkart" in badge_class else "combined")

            price_class = "price-best" if is_best else ""
            best_tag = " 🏆 Best Price" if is_best else ""

            st.markdown(f"""
            <div class="card">
                <span class="platform-badge {badge_class}">{row['platform']}</span>{best_tag}<br>
                <b style="font-size:1rem">{row['title'][:80]}</b><br>
                <span class="price-tag {price_class}">₹{row['price']:,}</span>
                &nbsp;&nbsp;<span style="color:#aaa;font-size:0.9rem">⭐ {row['rating']}</span>
                <br><a href="{row['url']}" target="_blank" style="color:#ffd200;font-size:0.85rem;text-decoration:none;">View Product →</a>
            </div>
            """, unsafe_allow_html=True)

        # Bar chart
        fig = px.bar(
            df, x="platform", y="price", color="platform",
            text="price",
            color_discrete_sequence=["#FF9900", "#2874f0", "#4ade80"],
            template="plotly_dark"
        )
        fig.update_traces(texttemplate="₹%{text:,}", textposition="outside")
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            title="Price Comparison Across Platforms",
            yaxis_title="Price (₹)",
            xaxis_title=""
        )
        st.plotly_chart(fig, use_container_width=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2 — Review Intelligence
    # ════════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown("### 💬 Review Intelligence by Platform")

        for p in products:
            if not p.get("reviews"):
                continue

            sentiment_result = analyze_sentiment(p["reviews"])
            pos = sentiment_result["positive"]
            neg = sentiment_result["negative"]
            neu = sentiment_result["neutral"]
            score = sentiment_result["score"]

            badge_class = "amazon" if "amazon" in p["platform"].lower() else "flipkart"
            color = "#4ade80" if score >= 60 else ("#f87171" if score < 40 else "#facc15")

            st.markdown(f"""
            <div class="card">
                <span class="platform-badge {badge_class}">{p['platform']}</span>
                <span style="float:right;font-size:1.6rem;font-weight:800;color:{color};">{score}% 😊</span>
                <br>
                <span class="pos">✅ Positive: {pos}%</span> &nbsp;
                <span class="neg">❌ Negative: {neg}%</span> &nbsp;
                <span class="neu">⚡ Neutral: {neu}%</span>
                <br><br>
                <b style="color:#aaa;font-size:0.85rem;">TOP ISSUES FOUND:</b><br>
            """, unsafe_allow_html=True)

            for issue in sentiment_result["top_issues"]:
                st.markdown(f'<div class="review-item">🔸 {issue}</div>', unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # Reddit Section
        if reddit_data:
            st.markdown("---")
            st.markdown("### 🔴 Reddit Public Opinion")
            reddit_sentiment = analyze_sentiment([r["text"] for r in reddit_data])

            st.markdown(f"""
            <div class="card">
                <span class="platform-badge reddit">Reddit</span>
                <span style="float:right;font-size:1.4rem;font-weight:800;color:#fa8072;">{reddit_sentiment['score']}% 💬</span>
                <br>
                <span class="pos">✅ {reddit_sentiment['positive']}%</span> &nbsp;
                <span class="neg">❌ {reddit_sentiment['negative']}%</span> &nbsp;
                <span class="neu">⚡ {reddit_sentiment['neutral']}%</span>
                <br><br>
                <b style="color:#aaa;font-size:0.85rem;">REDDIT SAYS:</b>
            """, unsafe_allow_html=True)

            for r in reddit_data[:5]:
                st.markdown(f'<div class="review-item">💬 {r["text"][:150]}...</div>', unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 3 — Combined Dashboard
    # ════════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown("### 📊 Combined Intelligence Dashboard")

        all_reviews = []
        for p in products:
            all_reviews.extend(p.get("reviews", []))
        if reddit_data:
            all_reviews.extend([r["text"] for r in reddit_data])

        combined = get_combined_score(all_reviews)
        overall_score = combined["score"]
        verdict_color = "#4ade80" if overall_score >= 65 else ("#f87171" if overall_score < 40 else "#facc15")
        verdict = "✅ Worth Buying" if overall_score >= 65 else ("❌ Think Twice" if overall_score < 40 else "⚠️ Mixed Feelings")

        # Top metrics
        c1, c2, c3, c4 = st.columns(4)
        metrics = [
            ("Overall Score", f"{overall_score}%", verdict_color),
            ("Positive", f"{combined['positive']}%", "#4ade80"),
            ("Negative", f"{combined['negative']}%", "#f87171"),
            ("Neutral",  f"{combined['neutral']}%",  "#facc15"),
        ]
        for col, (label, val, color) in zip([c1, c2, c3, c4], metrics):
            with col:
                st.markdown(f"""
                <div class="metric-box">
                    <div class="value" style="color:{color}">{val}</div>
                    <div class="label">{label}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Verdict
        best_product = min(products, key=lambda x: x["price"])
        st.markdown(f"""
        <div class="card" style="border:1px solid {verdict_color};text-align:center;">
            <div style="font-size:2rem">{verdict}</div>
            <div style="color:#aaa;margin-top:0.5rem;">Best deal: <b style="color:#ffd200">{best_product['platform']}</b> at <b style="color:#ffd200">₹{best_product['price']:,}</b></div>
        </div>
        """, unsafe_allow_html=True)

        # Donut chart
        fig2 = go.Figure(go.Pie(
            labels=["Positive", "Negative", "Neutral"],
            values=[combined["positive"], combined["negative"], combined["neutral"]],
            hole=0.6,
            marker_colors=["#4ade80", "#f87171", "#facc15"],
        ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            title="Overall Sentiment Breakdown",
            legend=dict(font=dict(color="white")),
            annotations=[dict(text=f"{overall_score}%", x=0.5, y=0.5, font_size=26, showarrow=False, font_color="white")]
        )
        st.plotly_chart(fig2, use_container_width=True)

        # Top issues combined
        st.markdown("#### 🔍 Top Issues Across All Platforms")
        for issue in combined["top_issues"]:
            st.markdown(f'<div class="review-item">🔸 {issue}</div>', unsafe_allow_html=True)

elif search_clicked and not product_query.strip():
    st.warning("Please enter a product name to search.")
else:
    # Landing state
    st.markdown("""
    <div style="text-align:center;padding:3rem;color:#666;">
        <div style="font-size:4rem">🛒</div>
        <div style="font-size:1.1rem;margin-top:1rem;">Search for any product to get started</div>
        <div style="font-size:0.9rem;margin-top:0.5rem;color:#555;">Compares prices • Analyses reviews • Gives a final verdict</div>
    </div>
    """, unsafe_allow_html=True)
