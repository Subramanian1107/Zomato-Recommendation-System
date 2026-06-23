# Deployment Plan - Zomato AI Recommendation System

This document outlines the deployment strategy for hosting the **Zomato AI Restaurant Recommendation System** in production.

---

## 1. Architecture Overview

To run this application in production, we have two primary options:

```
Option A: Split Deployment (Recommended for architectural fidelity)
┌─────────────────┐       HTTP Requests       ┌────────────────┐
│ Streamlit Cloud │ ────────────────────────> │   Render/ECS   │
│   (Frontend)    │ <──────────────────────── │ (FastAPI Host) │
└─────────────────┘      JSON Responses       └────────────────┘
                                                      │
                                                      ▼
                                                ┌────────────┐
                                                │  Groq API  │
                                                └────────────┘

Option B: Combined Deployment (Simplest, single-container hosting)
┌──────────────────────────────────────────────┐
│               Streamlit Cloud                │
│                                              │
│  ┌──────────────┐      In-Memory Calls       │
│  │  Streamlit   │ ────────────────────────>  │
│  │  (Frontend)  │                            │
│  └──────────────┘                            │
│         │                                    │
│         ▼ (Bypasses network API layer)       │
│  ┌──────────────┐                            │
│  │ Filter & LLM │ ────────────────────────>  │
│  └──────────────┘                            │
└──────────────────────────────────────────────┘
                                                      │
                                                      ▼
                                                ┌────────────┐
                                                │  Groq API  │
                                                └────────────┘
```

---

## 2. Option A: Split Deployment (FastAPI on Render/Railway + Streamlit Cloud)

In this approach, the FastAPI backend and the Streamlit frontend are hosted on separate platforms.

### Step 1: Deploying the FastAPI Backend (e.g., Render)
1. **Repository**: Push the repository to GitHub.
2. **Platform Creation**: Create a new **Web Service** on [Render](https://render.com/).
3. **Build Settings**:
   - **Environment**: `Python`
   - **Build Command**: `pip install -e .`
   - **Start Command**: `uvicorn zomato_rec.main:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables**:
   - `LLM_PROVIDER=groq`
   - `GROQ_API_KEY=gsk_...` (Your live Groq API key)
   - `LLM_MODEL=llama-3.3-70b-versatile`
   - `DATA_CACHE_PATH=data/processed/restaurants.parquet`

### Step 2: Deploying the Frontend (Streamlit Community Cloud)
1. **Sign-In**: Go to [Streamlit Community Cloud](https://share.streamlit.io/) and log in with your GitHub account.
2. **App Creation**: Click **New App**, select your repository, branch, and set the file path to `ui/streamlit_app.py`.
3. **App Secrets**:
   Under **Settings > Secrets**, add the backend URL:
   ```toml
   API_URL = "https://your-fastapi-backend-url.onrender.com"
   ```
4. **Deploy**: Click **Deploy**. The app will build and spin up at a public `*.streamlit.app` URL.

---

## 3. Option B: Combined Deployment (Embedded Backend)

Since Streamlit Cloud runs python code directly, we can bypass the FastAPI REST network layer entirely and run the preprocessor, index, and Groq client directly inside the Streamlit instance memory.

### Step 1: Modify `ui/streamlit_app.py` for Embedded Mode
If a separated API host is not desired, we can import the engine and builders directly:
```python
from zomato_rec.data.index import build_index
from zomato_rec.filtering.engine import FilterEngine
from zomato_rec.llm.groq_client import GroqClient
from zomato_rec.services.recommendation import RecommendationService
# Instantiated locally using Streamlit caching
```

### Step 2: Deploy to Streamlit Cloud
1. **GitHub**: Push your repository to GitHub.
2. **Deploy**: Connect the repository to [Streamlit Community Cloud](https://share.streamlit.io/).
3. **Secrets configuration**:
   Under **Settings > Secrets**, add the Groq variables:
   ```toml
   LLM_PROVIDER = "groq"
   GROQ_API_KEY = "gsk_..."
   LLM_MODEL = "llama-3.3-70b-versatile"
   DATA_CACHE_PATH = "data/processed/restaurants.parquet"
   ```
4. **Execution**: The instance will automatically download the HuggingFace dataset on startup, compile the Parquet cache, and execute recommendations.

---

## 4. Production Security & Performance Best Practices

1. **API Key Safety**: Never commit `.env` files or hardcode API keys. Always use Render Env Vars or Streamlit Secrets.
2. **Parquet Pre-caching**:
   - The cold start download of the HuggingFace dataset (~570MB) can take 30-40 seconds, which might exceed Streamlit Cloud's default setup timeout or cause UI delays.
   - **Recommendation**: Pre-bake the `restaurants.parquet` file. Run the preprocessing script locally to generate `data/processed/restaurants.parquet`, and upload/commit it using **Git LFS** or upload it to an external host (S3/GCS) and download it during build time.
3. **Async Timeouts**: Set `LLM_TIMEOUT_SECONDS=30` to prevent hanging Streamlit spinner threads in case of Groq API rate limits.
