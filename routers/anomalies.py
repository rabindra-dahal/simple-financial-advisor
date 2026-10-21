import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google import genai
import ollama

from core.schemas import AnomalyReport, FlaggedAnomaly, AIAnomalyAlert
from core.database import transactions_db, customers_db

# Setup dedicated engine console logger
logger = logging.getLogger("api_anomalies")
logging.basicConfig(level=logging.INFO)

router = APIRouter(
    prefix="/anomalies",
    tags=["Fraud & Anomalies"]
)

# Initialize primary Gemini client safely
try:
    gemini_client = genai.Client()
except Exception:
    gemini_client = None


# --- 1. GET ROUTE: MATHEMATICAL DETECTOR ENGINE ---
@router.get("/customer/{customer_id}", response_model=AnomalyReport)
def detect_spending_anomalies(customer_id: int):
    # Verify customer identity exists inside database tables
    customer_exists = any(c.id == customer_id for c in customers_db)
    if not customer_exists:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    # Get all historical completed expenses (negative values)
    all_expenses = [
        tx for tx in transactions_db 
        if tx.customer_id == customer_id and tx.is_completed and tx.amount < 0
    ]
    
    if len(all_expenses) < 3:
        # Insufficient data rows to build a statistical baseline pool safely
        return AnomalyReport(customer_id=customer_id, total_transactions_analyzed=len(all_expenses), anomalies_found=[])

    # Classify absolute expense amounts under specific categories
    spending_by_category = {}
    for tx in all_expenses:
        spending_by_category.setdefault(tx.category, []).append(abs(tx.amount))
        
    # Compute historical category baseline averages
    category_baselines = {
        cat: sum(amounts) / len(amounts) 
        for cat, amounts in spending_by_category.items()
    }
    
    anomalies = []
    
    # Scan historical ledger loop to locate deviations
    for tx in all_expenses:
        actual_cost = abs(tx.amount)
        avg_cost = category_baselines[tx.category]
        
        # ANOMALY CONDITION: Flag if item is over 2.5x the category baseline
        # and carries a minimum absolute value threshold over $100.00
        if actual_cost > (avg_cost * 1.4) and actual_cost > 100.0:
            deviation = actual_cost / avg_cost if avg_cost > 0 else 0
            reason_msg = f"This expense is {deviation:.1f}x higher than your usual {tx.category} average of ${avg_cost:.2f}."
            
            anomalies.append(
                FlaggedAnomaly(
                    transaction_id=tx.id,
                    title=tx.title,
                    amount=tx.amount,
                    category=tx.category,
                    transaction_date=tx.transaction_date,
                    average_category_spending=round(avg_cost, 2),
                    deviation_multiplier=round(deviation, 2),
                    reason=reason_msg
                )
            )
            
    return AnomalyReport(
        customer_id=customer_id,
        total_transactions_analyzed=len(all_expenses),
        anomalies_found=anomalies
    )


# --- 2. POST ROUTE: AI COCHING PROMPT ENGINE ---
@router.post("/customer/{customer_id}/ai-warning", response_model=AIAnomalyAlert)
def generate_ai_anomaly_warning(customer_id: int):
    # Execute standard mathematical detector function directly
    anomaly_report = detect_spending_anomalies(customer_id=customer_id)
    
    # Locate customer matching identity structures
    customer_name = "Valued Customer"
    for c in customers_db:
        if c.id == customer_id:
            customer_name = c.name
            break

    # If account behavior is completely regular, issue static clean alert status code early
    if not anomaly_report.anomalies_found:
        return AIAnomalyAlert(
            customer_id=customer_id,
            anomalies_detected=0,
            ai_warning_message=f"Hi {customer_name.split()[0]}, we reviewed your recent accounts and everything looks completely normal.",
            engine_used="system-static"
        )

    # Format list objects into cleanly indented readable bullet logs
    anomaly_details = ""
    for item in anomaly_report.anomalies_found:
        anomaly_details += (
            f"- Transaction: '{item.title}' inside category '{item.category}'\n"
            f"  Amount Flagged: ${abs(item.amount):.2f}\n"
            f"  Your Normal Category Average: ${item.average_category_spending:.2f}\n"
            f"  Multiplier Jump: {item.deviation_multiplier}x higher than standard baseline\n"
            f"  Logged Date: {item.transaction_date}\n\n"
        )

    # Construct the instruction context payload template for the LLM
    llm_prompt = (
        f"You are a helpful, professional personal banking AI assistant. "
        f"We have detected irregular financial anomalies in user {customer_name}'s recent transaction statement.\n\n"
        f"--- CONTEXT OF DETECTED SPENDING SPIKES ---\n{anomaly_details}"
        f"Instructions:\n"
        f"- Greet the customer warmly by their first name: {customer_name.split()[0]}.\n"
        f"- Explain the detected anomaly clearly and concisely without creating unnecessary panic.\n"
        f"- Playfully or usefully highlight the difference between this transaction and their normal average baseline.\n"
        f"- Keep the alert under 4 short sentences. Do not use raw markdown markup tags or system code keys."
    )

    # --- ATTEMPT 1: CALL GEMINI 3.5 FLASH LITE ---
    if gemini_client is not None:
        try:
            logger.info("Generating conversational text via Gemini 3.5 Flash-Lite...")
            response = gemini_client.models.generate_content(
                model='gemini-3.5-flash-lite',
                contents=llm_prompt,
            )
            return AIAnomalyAlert(
                customer_id=customer_id,
                anomalies_detected=len(anomaly_report.anomalies_found),
                ai_warning_message=response.text.strip(),
                engine_used="gemini-3.5-flash-lite"
            )
        except Exception as gemini_err:
            logger.warning(f"Gemini API issue occurred: {str(gemini_err)}. Redirecting traffic to local fallback container...")

    else:
        logger.warning("Gemini Client uninitialized. Activating immediate local fallback route...")

    # --- ATTEMPT 2: LOCAL OLLAMA ROUTING FALLBACK ---
    try:
        logger.info("Generating conversational text via local Ollama core model (llama3)...")
        ollama_response = ollama.generate(
            model="llama3",
            prompt=llm_prompt
        )
        return AIAnomalyAlert(
            customer_id=customer_id,
            anomalies_detected=len(anomaly_report.anomalies_found),
            ai_warning_message=ollama_response['response'].strip(),
            engine_used="ollama-llama3 (local fallback)"
        )
    except Exception as ollama_err:
        logger.error(f"Both core AI engines failed compilation pipelines: {str(ollama_err)}")
        raise HTTPException(
            status_code=503,
            detail=f"Financial Notification System failure. Diagnostic trace error: {str(ollama_err)}"
        )
