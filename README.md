# 🛒 BuySmart AI — Setup & Deployment Guide

## What this app does
- Search any product → get price comparison from Amazon & Flipkart
- Sentiment analysis on reviews per platform
- Reddit public opinion
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
│   └── reddit.py           ← Reddit opinions (PRAW)
└── .streamlit/
    ├── config.toml         ← Dark theme config
    └── secrets.toml        ← API keys (DO NOT push to GitHub)
```

---

## 🚀 Steps to Deploy on Streamlit Cloud

### Step 1 — Push to GitHub
1. Create a new GitHub repo (e.g. `buysmart-ai`)
2. Upload ALL these files maintaining the folder structure
3. Make sure `.streamlit/secrets.toml` is in `.gitignore`

### Step 2 — Deploy on Streamlit Cloud
1. Go to https://streamlit.io/cloud
2. Sign in with GitHub
3. Click **"New App"**
4. Select your repo → branch: `main` → file: `app.py`
5. Click **Deploy**

### Step 3 — Add API Keys (Optional but recommended)
In Streamlit Cloud → Your App → **Settings → Secrets**, paste:
```
SERPAPI_KEY = "your_key"
REDDIT_CLIENT_ID = "your_id"
REDDIT_CLIENT_SECRET = "your_secret"
```

> **Without API keys the app works in Demo Mode with realistic sample data.**
> It still shows all features perfectly for your exam/viva!

---

## 🔑 Getting Free API Keys

### SerpAPI (for real prices)
1. Go to https://serpapi.com
2. Sign up free → get 100 searches/month free
3. Copy your API key

### Reddit API (for real Reddit opinions)
1. Go to https://www.reddit.com/prefs/apps
2. Click **"Create App"**
3. Type: `script`
4. Name: `BuySmartAI`
5. Redirect URI: `http://localhost:8080`
6. Copy `client_id` (under app name) and `client_secret`

---

## 🧪 Run Locally (optional)
```bash
pip install -r requirements.txt
streamlit run app.py
```
