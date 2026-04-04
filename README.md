# 🛒 BuySmart AI — AI-Powered Product Intelligence

**Live App Demo**: [https://buysmart-ai.streamlit.app/](https://buysmart-ai.streamlit.app/)

## ✨ Key Features (6 Multi-Modal Data Tabs)
1. **💰 Live Price Comparison**: Search any product to get live price comparisons, top listings, and highest savings across platforms like Amazon, Flipkart, Croma, Reliance Digital, etc.
2. **⭐ E-com Reviews Mining**: Automated background scraping of Amazon.in, Flipkart, and Web reviews for deep sentiment processing.
3. **🌐 Community Reviews (Reddit)**: Live public opinion from Reddit discussions using Reddit API, including an aspect radar and sentiment breakdown.
4. **🎥 YouTube Reviews**: Video evaluation fetching via YouTube Data API and deep sentiment analysis of video comments (overall score, views/likes metrics, comment distribution).
5. **🧠 Deep NLP**: Advanced natural language processing across all textual data sources for refined entity detection, subjectivity, and automated linguistic insights.
6. **📊 Intelligence Dashboard**: Combined verdict scoring and an AI-driven purchase recommendation engine using `arcee-ai/trinity-large-preview` via OpenRouter to give actionable buying advice!

---

## 📁 File Structure
```
buysmart/
├── app.py                  ← Main Streamlit app
├── requirements.txt        ← Python packages
├── utils/
│   ├── sentiment.py        ← Sentiment analysis (VADER)
│   ├── search.py           ← Price fetching (SerpAPI)
│   ├── reddit.py           ← Reddit opinions (Reddit JSON API)
│   ├── youtube.py          ← YouTube Data API integration
│   ├── ecommerce_reviews.py← Amazon/Flipkart web scraping
│   └── nlp_deep.py         ← Deep NLP analytics
└── .streamlit/
    ├── config.toml         ← Dark theme config
    └── secrets.toml        ← API keys (DO NOT push to GitHub — in .gitignore)
```

---

## 🚀 Steps to Deploy on Streamlit Cloud

### Step 1 — Push to GitHub
1. Create a new GitHub repo (e.g. `buysmart-ai`)
2. Upload ALL these files maintaining the folder structure
3. Make sure `.streamlit/secrets.toml` is **in `.gitignore`** — never commit your API keys

### Step 2 — Deploy on Streamlit Cloud
1. Go to https://streamlit.io/cloud
2. Sign in with GitHub
3. Click **"New App"**
4. Select your repo → branch: `main` → file: `app.py`
5. Click **Deploy**

### Step 3 — Add API Keys (Optional but recommended)
In Streamlit Cloud → Your App → **Settings → Secrets**, paste:
```toml
SERPAPI_KEY = "your_key_here"
YOUTUBE_API_KEY = "your_youtube_key"
OPENROUTER_API_KEY = "your_openrouter_key"
```

> **Without API keys the app runs in Demo Mode with realistic sample data.**
> It still shows all features perfectly for your exam/viva!

---

## 🔑 Getting Free API Keys

### SerpAPI (for real live prices)
1. Go to https://serpapi.com
2. Sign up free → get 100 searches/month free
3. Copy your API key from the dashboard
4. Add it to `.streamlit/secrets.toml` locally:
   ```toml
   SERPAPI_KEY = "your_key_here"
   YOUTUBE_API_KEY = "your_youtube_key"
   OPENROUTER_API_KEY = "your_openrouter_key"
   ```

### YouTube Data API (for video reviews)
1. Go to Google Cloud Console
2. Enable YouTube Data API v3 and generate an API key
3. Add it to `.streamlit/secrets.toml` as `YOUTUBE_API_KEY`

### OpenRouter API (for AI Verdict Generation)
1. Go to [https://openrouter.ai/](https://openrouter.ai/)
2. Create an account and generate an API key for the `arcee-ai/trinity-large-preview` model
3. Add it to `.streamlit/secrets.toml` as `OPENROUTER_API_KEY`

---

## 🧪 Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

For local API key usage, create `.streamlit/secrets.toml`:
```toml
SERPAPI_KEY = "your_serpapi_key"
YOUTUBE_API_KEY = "your_youtube_key"
OPENROUTER_API_KEY = "your_openrouter_key"
```

---

## ⚠️ Security Notes
- **Never hardcode API keys** in Python source files
- Add `.streamlit/secrets.toml` to `.gitignore` before your first commit
- Use Streamlit Cloud's Secrets Manager for deployed apps
