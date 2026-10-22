import streamlit as st
import requests

# Base URL pointing to your running FastAPI backend
BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Fintech AI Dashboard", layout="wide", page_icon="🪙")

# --- SESSION STATE INITIALIZATION ---
if "token" not in st.session_state:
    st.session_state.token = None
if "customer_id" not in st.session_state:
    st.session_state.customer_id = None
if "customer_name" not in st.session_state:
    st.session_state.customer_name = None

# Helper headers function
def get_auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


# --- CONTAINER 1: AUTHENTICATION GATEWAY ---
if st.session_state.token is None:
    st.title(" Secure Fintech Sign-In")
    st.markdown("Use your mock registered email credentials (e.g., `alice.smith@example.com` or `ian.m@example.com`) with the password `password123`.")
    
    with st.form("login_form"):
        email = st.text_input("Email Address", value="alice.smith@example.com")
        password = st.text_input("Password", type="password", value="password123")
        submit_login = st.form_submit_button("Sign In")
        
        if submit_login:
            try:
                # 1. Exchange credentials for a token via FastAPI Auth
                login_payload = {"username": email, "password": password}
                response = requests.post(f"{BACKEND_URL}/auth/login", data=login_payload)
                
                if response.status_code == 200:
                    token_data = response.json()
                    st.session_state.token = token_data["access_token"]
                    
                    # 2. Derive user details from current session metadata context
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
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.session_state.customer_id = None
        st.session_state.customer_name = None
        st.rerun()

    # Main dashboard header tabs
    tab1, tab2, tab3 = st.tabs([" Balances & Transactions", " Gemini AI Advisor", " Statistical Anomalies"])

    # --- TAB 1: FINANCIAL OVERVIEW LEDGER ---
    with tab1:
        st.title(" Financial Statement Overview")
        
        # Load Analytics Summary Matrix
        summary_res = requests.get(f"{BACKEND_URL}/analytics/customer/{st.session_state.customer_id}", headers=get_auth_headers())
        if summary_res.status_code == 200:
            summary = summary_res.json()
            col1, col2, col3 = st.columns(3)
            
            # FIXED: Converted to raw f-strings (rf"...") to safely format currency symbols without warnings
            col1.metric("Total Income Deposits", rf"\${summary['total_income']:,}")
            col2.metric("Total Categorized Expenses", rf"-\${summary['total_expenses']:,}")
            col3.metric("Net Account Balance", rf"\${summary['net_balance']:,}")
            
            # Categories spending card list blocks
            if summary.get("spending_by_category"):
                st.subheader("Spending Breakdown by Category")
                cat_cols = st.columns(len(summary["spending_by_category"]))
                for i, item in enumerate(summary["spending_by_category"]):
                    # FIXED: Converted to raw f-string to prevent illegal string escape warnings
                    cat_cols[i].info(rf"**{item['category']}**\n\n\${item['total_spent']}")
        
        # Load Transaction History Lists
        st.subheader("Recent Account Transactions")
        tx_res = requests.get(f"{BACKEND_URL}/transactions/customer/{st.session_state.customer_id}", headers=get_auth_headers())
        if tx_res.status_code == 200:
            st.dataframe(tx_res.json(), width='stretch', hide_index=True)


    # --- TAB 2: CHAT HUB FOR GEMINI ADVISOR ---
    with tab2:
        st.title(" Chat with your Gemini AI Advisor")
        st.markdown("Ask natural questions about your transactions, spending habits, or request financial guidance.")

        user_prompt = st.text_input("Ask your Advisor:", placeholder="Am I spending too much money on movie tickets?")
        if st.button("Submit Inquiry"):
            if user_prompt:
                with st.spinner("Gemini is analyzing your financial history..."):
                    advisor_res = requests.post(
                        f"{BACKEND_URL}/advisor/customer/{st.session_state.customer_id}",
                        json={"query": user_prompt},
                        headers=get_auth_headers()
                    )
                    if advisor_res.status_code == 200:
                        advice_payload = advisor_res.json()
                        st.chat_message("assistant").write(advice_payload["advice"])
                        st.caption(f"Processed via core engine: `{advice_payload['engine_used']}`")
                    else:
                        st.error("AI Advisor generation pipeline failed.")

    # --- TAB 3: LIVE ANTI-FRAUD ANOMALY TRACKING ---
    with tab3:
        st.title(" Live Z-Score Anomaly Detector")
        st.markdown("Scans your transaction categories dynamically for deviations outside your normal historical limits.")
        
        if st.button("Trigger Global Security Scan"):
            with st.spinner("Computing standard deviations and calling Gemini notification engine..."):
                # Call our POST AI alert routine
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
