import streamlit as st
import requests
import json
import os

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Fintech AI Dashboard", layout="wide", page_icon="🪙")

# --- 1. FILE-BACKED PERSISTENCE CONTROLLER ---
SESSION_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".session_cache.json")

def load_cached_session():
    """Reads persistent session data and chat histories from disk on startup."""
    if os.path.exists(SESSION_CACHE_FILE):
        try:
            with open(SESSION_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_session_cache(token: str, email: str, chat_history: list):
    """Writes token, email, and conversation history records safely to disk."""
    try:
        with open(SESSION_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"token": token, "email": email, "chat_history": chat_history}, f)
    except Exception:
        pass

def clear_session_cache():
    """Removes the persistent file layer entirely upon customer logout."""
    if os.path.exists(SESSION_CACHE_FILE):
        try:
            os.remove(SESSION_CACHE_FILE)
        except Exception:
            pass


# Execute cache check immediately at top-to-bottom script startup
cached_data = load_cached_session()

# Initialize or restore Streamlit session state parameters
if "token" not in st.session_state:
    st.session_state.token = cached_data.get("token")
if "customer_id" not in st.session_state:
    st.session_state.customer_id = None
if "customer_name" not in st.session_state:
    st.session_state.customer_name = None
if "chat_history" not in st.session_state:
    # RESTORE: Pull previous chat logs out of the disk layer on reload
    st.session_state.chat_history = cached_data.get("chat_history", [])

# Automatically re-map customer profile attributes if the token is present on browser refresh
if st.session_state.token and not st.session_state.customer_id and cached_data.get("email"):
    email = cached_data["email"]
    if "alice" in email: 
        st.session_state.customer_id = 1
        st.session_state.customer_name = "Alice Smith"
    elif "bob" in email: 
        st.session_state.customer_id = 2
        st.session_state.customer_name = "Bob Jones"
    else: 
        st.session_state.customer_id = 9
        st.session_state.customer_name = "Ian Malcolm"

def get_auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


# --- CONTAINER 1: AUTHENTICATION GATEWAY ---
if st.session_state.token is None:
    st.title(" Secure Fintech Sign-In")
    st.markdown("Use your mock registered email credentials (e.g., `alice.smith@example.com`) with the password `password123`.")
    
    with st.form("login_form"):
        email = st.text_input("Email Address", value="alice.smith@example.com")
        password = st.text_input("Password", type="password", value="password123")
        submit_login = st.form_submit_button("Sign In")
        
        if submit_login:
            try:
                login_payload = {"username": email, "password": password}
                response = requests.post(f"{BACKEND_URL}/auth/login", data=login_payload)
                
                if response.status_code == 200:
                    token_data = response.json()
                    st.session_state.token = token_data["access_token"]
                    
                    # Persist the login token to disk file cache immediately
                    save_session_cache(token_data["access_token"], email, [])
                    
                    if "alice" in email: 
                        st.session_state.customer_id = 1
                        st.session_state.customer_name = "Alice Smith"
                    elif "bob" in email: 
                        st.session_state.customer_id = 2
                        st.session_state.customer_name = "Bob Jones"
                    else: 
                        st.session_state.customer_id = 9
                        st.session_state.customer_name = "Ian Malcolm"
                    
                    st.success(f"Welcome back, {st.session_state.customer_name}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please verify your email and password.")
            except Exception as e:
                st.error(f"Cannot connect to FastAPI server backend: {str(e)}")

# --- CONTAINER 2: THE FINANCIAL HUB INTERFACE ---
else:
    # Sidebar control station
    st.sidebar.title(f"👤 {st.session_state.customer_name}")
    st.sidebar.caption(f"Customer Profile ID: #{st.session_state.customer_id}")
    
    # CLEAR CHAT BUTTON: Easily clear conversation strings manually from the sidebar
    if st.sidebar.button(" Clear Chat History"):
        st.session_state.chat_history = []
        save_session_cache(st.session_state.token, cached_data.get("email"), [])
        st.rerun()
        
    # Manual Logout wipes disk cache and session variables instantly
    if st.sidebar.button("Logout"):
        clear_session_cache()
        st.session_state.token = None
        st.session_state.customer_id = None
        st.session_state.customer_name = None
        if "chat_history" in st.session_state:
            del st.session_state.chat_history
        st.rerun()

    # Main dashboard header tabs
    tab1, tab2, tab3 = st.tabs([" Balances & Transactions", " Gemini AI Advisor", " Statistical Anomalies"])

    # --- TAB 1: FINANCIAL OVERVIEW LEDGER ---
    with tab1:
        st.title(" Financial Statement Overview")
        
        summary_res = requests.get(f"{BACKEND_URL}/analytics/customer/{st.session_state.customer_id}", headers=get_auth_headers())
        if summary_res.status_code == 200:
            summary = summary_res.json()
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Income Deposits", rf"\${summary['total_income']:,} USD")
            col2.metric("Total Categorized Expenses", rf"-\${summary['total_expenses']:,} USD")
            col3.metric("Net Account Balance", rf"\${summary['net_balance']:,} USD")
            
            if summary.get("spending_by_category"):
                st.subheader("Spending Breakdown by Category")
                cat_cols = st.columns(len(summary["spending_by_category"]))
                for i, item in enumerate(summary["spending_by_category"]):
                    cat_cols[i].info(rf"**{item['category']}**\n\n\${item['total_spent']} USD")
        
        st.subheader("Recent Account Transactions")
        tx_res = requests.get(f"{BACKEND_URL}/transactions/customer/{st.session_state.customer_id}", headers=get_auth_headers())
        if tx_res.status_code == 200:
            st.dataframe(tx_res.json(), width='stretch', hide_index=True)

    # --- TAB 2: STATEFUL CHAT HUB FOR GEMINI ADVISOR ---
    with tab2:
        st.title(" Chat with your Gemini AI Advisor")
        
        if st.session_state.chat_history:
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.write(message["text"])
        else:
            st.info(" Your chat thread is empty. Use the global input field at the base of the viewport to query Gemini!")

    # --- TAB 3: LIVE ANTI-FRAUD ANOMALY TRACKING ---
    with tab3:
        st.title(" Live Z-Score Anomaly Detector")
        st.markdown("Scans your transaction categories dynamically for deviations outside your normal historical limits.")
        
        if st.button("Trigger Global Security Scan"):
            with st.spinner("Computing standard deviations and calling Gemini notification engine..."):
                alert_res = requests.post(f"{BACKEND_URL}/anomalies/customer/{st.session_state.customer_id}/ai-warning", headers=get_auth_headers())
                if alert_res.status_code == 200:
                    alert_data = alert_res.json()
                    st.metric("Flagged Spending Spikes Detected", alert_data["anomalies_detected"])
                    if alert_data["anomalies_detected"] > 0:
                        st.warning(alert_data["ai_warning_message"])
                    else:
                        st.success(alert_data["ai_warning_message"])
                    st.caption(f"Alert compiled dynamically via engine: `{alert_data['engine_used']}`")
                else:
                    st.error("Failed to compile statistical anomaly alerts.")

    # =========================================================================
    # GLOBAL BOTTOM CHAT INPUT ANCHOR (AI STUDIO CENTERING STYLE)
    # =========================================================================
    if user_prompt := st.chat_input("Ask about your finances..."):
        st.session_state.chat_history.append({"role": "user", "text": user_prompt})
        
        try:
            with st.spinner("Gemini is accessing your financial ledger..."):
                advisor_res = requests.post(
                    f"{BACKEND_URL}/advisor/customer/{st.session_state.customer_id}",
                    json={
                        "query": user_prompt,
                        "session_id": "streamlit_session_thread_1"
                    },
                    headers=get_auth_headers()
                )
                
                if advisor_res.status_code == 200:
                    advice_payload = advisor_res.json()
                    ai_answer = advice_payload["advice"]
                    st.session_state.chat_history.append({"role": "assistant", "text": ai_answer})
                    
                    # PERSIST: Write current active thread changes directly to disk cache
                    save_session_cache(st.session_state.token, cached_data.get("email"), st.session_state.chat_history)
                else:
                    st.error("Error: The AI advisor routing pipeline failed to resolve.")
        except Exception as conn_err:
            st.error(f"Frontend connection error: {str(conn_err)}")
        
        st.rerun()
