# 🪙 Secure AI Financial Advisor & Anomaly Detector

A modular, production-ready **Fintech REST API & Interactive Dashboard** built using **Python, FastAPI, Streamlit, and ChromaDB**. This application features dynamic **Z-Score statistical anomaly tracking**, secure **OAuth2 JWT token-based authentication**, and an advanced **Multi-Turn Chat Advisor** powered by **Gemini 3.5 Flash-Lite** with a local **Ollama (Llama3)** failover mechanism.

---

## 🏗️ Project Architecture & Layout

The project separates core configurations, secure authorization dependencies, and analytical parsing logic from presentation containers and testing suites:

```text
simple-financial-advisor/
│
├── core/
│   ├── data/
│   │   ├── customers.csv     # Local ledger registry (20 Mock profiles)
│   │   └── transactions.csv  # 200 granular transaction rows (10 per user)
│   │
│   ├── auth.py               # OAuth2 password hashing & JWT token validation
│   ├── database.py           # On-boot dynamic CSV to Pydantic database parser
│   ├── schemas.py            # Strict Pydantic verification and validation schemas
│   └── vector_db.py          # ChromaDB connection & SentenceTransformers embedder
│
├── routers/
│   ├── advisor.py            # Stateful multi-turn conversational RAG advisor engine
│   ├── anomalies.py          # Statistical Z-Score abnormality detector & AI generator
│   ├── analytics.py          # Categorized ledger metrics aggregator
│   ├── auth.py               # Credentials authentication gateway & JWT token provider
│   ├── customers.py          # Customer profile registry endpoints
│   └── transactions.py       # Financial ledger statement endpoints
│
├── tests/
│   ├── __init__.py           # Declares directory as a Python testing package
│   ├── conftest.py          # Configures global environment mocks & isolated DB fixtures
│   ├── test_anomalies.py    # Validates Z-Score math thresholds & Ollama failovers
│   └── test_auth.py         # Validates JWT tokens & cross-tenant security guardrails
│
├── .env                      # Secure private keys & configurations (git-ignored)
├── .session_cache.json       # Secure disk-persisted session data & conversation threads
├── app.py                    # Streamlit interface with Google AI Studio styling
├── main.py                   # FastAPI core entry point & lifespan scheduler
├── pytest.ini                # Sanitized automated test filtering rules
└── requirements.txt          # Python dependency checklist
```

---

## ✨ Features Accomplished

1. **Modular Architecture:** Complete isolation of concerns between layout directories (`core/`), routing clusters (`routers/`), test workspaces (`tests/`), app configurations, and client presentation layers.
2. **Stateless CSV Ingestion:** Clean parsing engine that extracts, maps, and loads plain text files into active operational dictionary memories at server bootstrap.
3. **Statistical Anomaly Monitoring:** Dynamic Z-Score engine computing personal standard deviations per category. Flags spending irregularities exceeding 1.0σ dynamically.
4. **Stateful Conversation Threads:** The AI Advisor maintains session memory (`chat_history_db`), allowing customers to ask contextual follow-up questions (e.g., *"How much did I spend on tickets?"* followed by *"Was that above my average?"*).
5. **Precision Output Formatting:** Strict system rules that force the AI to return currency tags wrapped in `USD` or text descriptors, preventing formatting glitches or whitespace compression under Streamlit's Markdown/LaTeX parser engines.
6. **Bulletproof Session Permanence:** Self-contained file-backed cache layer (`.session_cache.json`) that saves tokens and conversational logs onto disk. Eliminates data wipeouts and forces persistent sign-ins even on browser **F5** refreshes.
7. **Resilient AI Pipeline (Dual Engine):** Advanced prompting that evaluates queries using **Gemini 3.5 Flash-Lite** first and gracefully slips down into a local **Ollama (Llama3)** container during API outages.
8. **Premium Dashboard UI Design:** Centered bottom-anchored chat input elements mirroring **Google AI Studio** with manual conversation flushing buttons built cleanly into the grid viewport.
9. **Pristine Test Suite Configuration:** High-precision mock unit test pipelines isolated inside `tests/` with optimized regex configuration rules silencing third-party warning alerts during automated verification cycles.

---

## 🛠️ Installation & Setup

### 1. Clone & Set Up Your Environment
Ensure you have **Python 3.10+** installed on your workstation machine:

```bash
# Navigate to the workspace directory
cd simple-financial-advisor

# Initialize virtual environment containers
python -m venv venv
source venv/Scripts/activate  # macOS/Linux user: source venv/bin/activate

# Install required system packages
pip install fastapi[standard] streamlit requests pyjwt[crypto] passlib[bcrypt] google-genai chromadb sentence-transformers ollama python-dotenv pytest httpx pytest-mock
```

### 2. Configure Local Secrets (`.env`)
Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_actual_google_gemini_api_key_here
JWT_SECRET=supersecretfintechkey12345!productionsecured32bytes
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
HF_HUB_DISABLE_SYMLINKS_WARNING=1
```

### 3. Start Local Fallback Models (Optional)
If you want to support local failover runtime functionality, install [Ollama](https://ollama.com) and cache a localized model:

```bash
ollama run llama3
```

---

## 🚀 Running the Application Stack

You must execute the application inside two separate parallel terminal tabs or split-window shell sessions:

### Terminal 1: Launch FastAPI Backend Server
To make the watcher track changes only inside your python code files and ignore frontend logs:
```bash
fastapi dev main.py --reload-dir core --reload-dir routers
```
* Interactive Swagger UI documentation pages compile directly at `http://127.0.0`.

### Terminal 2: Launch Streamlit Web UI Dashboard
```bash
streamlit run app.py
```
* The user dashboard interface opens automatically inside your favorite default browser environment at `http://localhost:8501`.

### Running Automated Test Infrastructure
To execute your mathematical verification rules and endpoint access barriers securely without exhausting real live API tokens:
```bash
pytest -v
```

---

## 🧪 Validated Testing Profiles

Use these mock account profiles to test privileges segregation, financial summaries, and anomaly alert notifications:

| Account Identity Name | Sign-In Mock Email | Secure Default Password | Context Behavior Expected |
| :--- | :--- | :--- | :--- |
| **Alice Smith** | `alice.smith@example.com` | `password123` | Flags small entertainment variations. Supports conversational multi-turn testing. |
| **Ian Malcolm** | `ian.m@example.com` | `password123` | High overall net income. Flags structural utility/rent spikes. |
