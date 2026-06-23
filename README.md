# Zomato AI Restaurant Recommendation System

An end-to-end AI-powered restaurant recommendation engine for Bangalore (Bengaluru), India. It filters through over 51,000 listings using deterministic hard filters (neighborhood, cuisine, rating, budget band, online order, book table) and uses the **Groq API** with the **Llama-3.3-70b-versatile** model to rank choices and generate personalized dining recommendations based on soft preferences.

---

## Features

- **Hybrid Recommendation Pipeline**: Hard constraints are filtered programmatically for 100% accuracy, while soft preferences (e.g., family-friendly, rooftop seating, quiet vibes) are reasoned by the LLM.
- **Fast Startup & Parquet Cache**: Cold starts download the ~570MB Hugging Face dataset automatically. Subsequent warm starts load the preprocessed index in under 4.3 seconds using a Parquet cache.
- **Vibrant UI frontend**: A premium Streamlit dashboard with custom CSS, dark mode aesthetics, and glassmorphic card layouts.
- **Dual-Mode Deployment Ready**: Can run in a split API-client architecture (FastAPI backend + Streamlit client) or entirely embedded in a single Streamlit process for zero-configuration hosting on **Streamlit Community Cloud**.
- **Robust Fallbacks & Self-Repair**: Automatic JSON validation self-repairs malformed LLM responses and degrades gracefully to template-driven top-rated candidates on API failures.

---

## Technology Stack

- **Backend**: Python (>= 3.9), FastAPI, Pydantic v2, `pydantic-settings`
- **Data Layer**: Hugging Face `datasets`, `pandas`, `numpy`, `pyarrow` (Parquet)
- **AI Layer**: `groq` SDK (`llama-3.3-70b-versatile` model)
- **Frontend**: Streamlit
- **Testing**: `pytest`, `pytest-asyncio`, FastAPI `TestClient`

---

## Project Structure

```
Zomato/
├── data/
│   └── processed/                  # Cached Parquet file (gitignored)
├── docs/                           # Architecture, edge cases, plans
├── src/
│   └── zomato_rec/
│       ├── api/                    # REST endpoints & dependencies
│       ├── data/                   # Ingestion, preprocessor, index
│       ├── filtering/              # Hard filters & pre-LLM ranker
│       ├── llm/                    # Groq API wrappers & prompt builders
│       ├── models/                 # Shared schemas (Pydantic / Dataclasses)
│       └── services/               # Orchestration service layer
├── ui/
│   └── streamlit_app.py            # Streamlit dashboard
├── tests/                          # Unit and integration test suite
├── pyproject.toml                  # PEP 621 metadata
└── requirements.txt                # Streamlit Cloud build requirements
```

---

## Getting Started

### Prerequisites
- Python 3.9, 3.10, 3.11, or 3.12
- Groq API Key (get one from the [Groq Console](https://console.groq.com/))

### 1. Installation
Clone the repository and set up a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

### 2. Environment Setup
Copy the template and fill in your Groq API Key:
```bash
cp .env.example .env
```
Open `.env` and set:
```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_groq_api_key_here
LLM_MODEL=llama-3.3-70b-versatile
```

### 3. Run the Application

#### Option A: Run API + Frontend separately (Local development)
Start the FastAPI server in one terminal window:
```bash
source .venv/bin/activate
uvicorn zomato_rec.main:app --port 8000 --reload
```

Start the Streamlit frontend in a second terminal window:
```bash
source .venv/bin/activate
streamlit run ui/streamlit_app.py --server.port 8501
```

#### Option B: Run in Embedded Mode (Production / Streamlit Cloud)
To run the application in a single terminal without a separate API server, clear the `API_URL` environment variable and run:
```bash
source .venv/bin/activate
API_URL="" streamlit run ui/streamlit_app.py --server.port 8501
```
The Streamlit app will load the data index and execute the Groq pipeline locally in-memory.

---

## Running Tests

We maintain a high-quality test suite covering preprocessing, filtering, parsing, and API endpoints:
```bash
source .venv/bin/activate
pytest -v
```

---

## Production Deployment

### Deploying to Streamlit Community Cloud
1. Push your code to a GitHub repository.
2. Log in to [Streamlit Share](https://share.streamlit.io/).
3. Connect the repository, set the main branch, and specify the entrypoint file path as `ui/streamlit_app.py`.
4. Under **Settings > Secrets**, paste your `.env` variables in TOML format:
   ```toml
   LLM_PROVIDER = "groq"
   GROQ_API_KEY = "gsk_..."
   LLM_MODEL = "llama-3.3-70b-versatile"
   DATA_CACHE_PATH = "data/processed/restaurants.parquet"
   ```
5. Click **Deploy**.
