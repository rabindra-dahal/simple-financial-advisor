# 🪙 Secure AI Financial Advisor & Anomaly Detector

A modular, production-ready **Fintech REST API & Interactive Dashboard** built using **Python, FastAPI, Streamlit, and ChromaDB**. This application leverages **Gemini 3.5 Flash-Lite** as a primary RAG engine to deliver context-aware financial advisory chats and conversational fraud/anomaly alerts, backed by a local **Ollama (Llama3)** failover mechanism.

---

## 🏗️ Project Architecture & Layout

The project separates core data loading, vector indexing, and business logic from the routing and representation layers:

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
│   ├── advisor.py            # Core RAG Advisor chat prompt engine (Gemini/Ollama)
│   ├── anomalies.py          # Statistical Z-Score abnormality detector & AI generator
│   ├── analytics.py          # Categorized ledger metrics aggregator
│   ├── auth.py               # Credentials authentication gateway & JWT token provider
│   ├── customers.py          # Customer profile registry endpoints
│   └── transactions.py       # Financial ledger statement endpoints
│
├── .env                      # Secure private keys & configurations (git-ignored)
├── app.py                    # Streamlit responsive multi-tab frontend interface
├── main.py                   # FastAPI core entry point & lifespan scheduler
└── requirements.txt          # Python dependency checklist
```

---

## ✨ Features Accomplished

1. **Modular Architecture:** Complete isolation of concerns between layout directories (`core/`), routing clusters (`routers/`), app configurations, and client presentation layers.
2. **Stateless CSV Ingestion:** Clean parsing engine that extracts, maps, and loads plain text files into active operational dictionary memories at server bootstrap.
3. **Statistical Anomaly Monitoring:** Real-time Z-Score engine computing personal standard deviations per category. Flags spending irregularities exceeding 1.0σ dynamically.
4. **Resilient AI Pipeline (Dual Engine):** Advanced prompting that attempts token evaluation using **Gemini 3.5 Flash-Lite** first and gracefully slips down into **Ollama (Llama3)** locally during API outages.
5. **Secure Token Locking (JWT):** Full implementation of OAuth2 password request protocols issuing secure, time-locked (`30m`) signed keys protecting downstream endpoints from unauthorized access.
6. **Polished Dashboard Frontend:** Responsive Streamlit tabs rendering interactive transaction dataframes, balance summary cards, alert logs, and contextual chat boxes without escape sequence string leaks.

---

## 🛠️ Installation & Setup

### 1. Clone & Set Up Your Environment
Ensure you have **Python 3.10+** installed on your workstation machine:

```bash
# Navigate to the workspace directory
cd simple-financial-advisor

# Initialize virtual environment containers
python -m venv .venv
source .venv/bin/activate  # Windows user: .venv\Scripts\activate

# Install required system packages
pip install fastapi[standard] streamlit requests pyjwt[crypto] passlib[bcrypt] google-genai chromadb sentence-transformers ollama python-dotenv
```

### 2. Configure Local Secrets (`.env`)
Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_actual_google_gemini_api_key_here
JWT_SECRET=supersecretfintechkey12345!
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
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
```bash
fastapi dev main.py
```
* Interactive Swagger UI documentation pages compile directly at `http://127.0.0`.

### Terminal 2: Launch Streamlit Web UI Dashboard
```bash
streamlit run app.py
```
* The user dashboard interface opens automatically inside your favorite default browser environment at `http://localhost:8501`.

---

## 🧪 Validated Testing Profiles

Use these mock account profiles to test permissions segregation, financial summaries, and anomaly alert notifications:

| Account Identity Name | Sign-In Mock Email | Secure Default Password | Context Behavior Expected |
| :--- | :--- | :--- | :--- |
| **Alice Smith** | `alice.smith@example.com` | `password123` | Flags small anomalies (Movie Tickets) with `Z-Score >= 1.0`. |
| **Ian Malcolm** | `ian.m@example.com` | `password123` | High overall net income. Flags structural utility spikes. |

---

## 🛡️ Core Security Implementations

* **OAuth2 Bearer Flow:** Tokens generated at `/auth/login` require validating an email string paired to a password hash context.
* **Cross-Tenant Guard Rails:** Every request verified by the `get_current_user` dependency automatically asserts that `current_user.id == requested_customer_id`, preventing authenticated profiles from viewing other users' financial statements.
