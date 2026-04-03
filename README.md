# 🛒 BuySmart AI — Setup & Deployment Guide

## What this app does
- Search any product → get price comparison from Amazon & Flipkart
- Sentiment analysis on reviews per platform
- Reddit public opinion (live, via Reddit's search API)
- Combined score & verdict dashboard

---

## 📁 File Structure
```
buysmart/
├── app.py                  ← Main Streamlit app
├── requirements.txt        ← Python packages
├── utils/
│   ├── sentiment.py        ← Sentiment analysis (VADER)
│   ├── search.py           ← Price fetching (SerpAPI)
│   └── reddit.py           ← Reddit opinions (Reddit JSON API)
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
   ```

---

## 🧪 Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

For local API key usage, create `.streamlit/secrets.toml`:
```toml
SERPAPI_KEY = "your_serpapi_key"
```

---

## ⚠️ Security Notes
- **Never hardcode API keys** in Python source files
- Add `.streamlit/secrets.toml` to `.gitignore` before your first commit
- Use Streamlit Cloud's Secrets Manager for deployed apps
