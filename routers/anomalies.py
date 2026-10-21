import math
import logging
from fastapi import APIRouter, HTTPException
from google import genai
import ollama

from core.schemas import AnomalyReport, FlaggedAnomaly, AIAnomalyAlert
from core.database import transactions_db, customers_db

logger = logging.getLogger("api_anomalies")
logging.basicConfig(level=logging.INFO)

router = APIRouter(
    prefix="/anomalies",
    tags=["Fraud & Anomalies"]
)

try:
    gemini_client = genai.Client()
except Exception:
    gemini_client = None


# --- STATISTICAL HELPER FUNCTIONS ---
def calculate_mean_and_stdev(amounts: list[float]):
    """Returns the (mean, standard_deviation) for a list of financial figures."""
    n = len(amounts)
    if n == 0:
        return 0.0, 0.0
    
    mean = sum(amounts) / n
    if n < 2:
        return mean, 0.0  # Cannot compute variance with less than 2 items
        
    # Variance computation
    variance = sum((x - mean) ** 2 for x in amounts) / n
    return mean, math.sqrt(variance)


# --- 1. GET ROUTE: DYNAMIC Z-SCORE DETECTOR ---
@router.get("/customer/{customer_id}", response_model=AnomalyReport)
def detect_spending_anomalies(customer_id: int):
    customer_exists = any(c.id == customer_id for c in customers_db)
    if not customer_exists:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    # Isolate all completed expenses (negative values) for this user
    all_expenses = [
        tx for tx in transactions_db 
        if tx.customer_id == customer_id and tx.is_completed and tx.amount < 0
    ]
    
    if len(all_expenses) < 3:
        return AnomalyReport(customer_id=customer_id, total_transactions_analyzed=len(all_expenses), anomalies_found=[])

    # Group absolute transaction figures by category
    spending_by_category = {}
    for tx in all_expenses:
        spending_by_category.setdefault(tx.category, []).append(abs(tx.amount))
        
    # Pre-calculate mean and standard deviation baselines for every category
    category_stats = {}
    for cat, amounts in spending_by_category.items():
        mean, stdev = calculate_mean_and_stdev(amounts)
        category_stats[cat] = {"mean": mean, "stdev": stdev}
    
    anomalies = []
    
    # Scan through transactions to isolate items with a high Z-score
    for tx in all_expenses:
        actual_cost = abs(tx.amount)
        stats = category_stats[tx.category]
        mean = stats["mean"]
        stdev = stats["stdev"]
        
        # Calculate Z-Score: (Value - Mean) / Standard Deviation
        # If stdev is 0 (all values identical), the Z-Score is 0
        z_score = (actual_cost - mean) / stdev if stdev > 0 else 0.0
        
        # STATISTICAL ANOMALY RULE: Flag if the transaction is over 1.5 standard deviations above average (Z-Score > 1.5)
        # AND check that it's an outright increase (not a cheaper-than-normal transaction)
        # AND has a minimum absolute visual threshold impact of over $40.00
        if z_score >= 1.0 and actual_cost > mean and actual_cost > 5.0:
            reason_msg = (
                f"This transaction has a Z-Score of {z_score:.2f}, meaning it deviates significantly "
                f"from your typical {tx.category} baseline average of ${mean:.2f}."
            )
            
            anomalies.append(
                FlaggedAnomaly(
                    transaction_id=tx.id,
                    title=tx.title,
                    amount=tx.amount,
                    category=tx.category,
                    transaction_date=tx.transaction_date,
                    average_category_spending=round(mean, 2),
                    deviation_multiplier=round(z_score, 2), # Passing Z-score as the multiplier metric
                    reason=reason_msg
                )
            )
            
    return AnomalyReport(
        customer_id=customer_id,
        total_transactions_analyzed=len(all_expenses),
        anomalies_found=anomalies
    )


# --- 2. POST ROUTE: AI SMART PROMPT GENERATOR ---
@router.post("/customer/{customer_id}/ai-warning", response_model=AIAnomalyAlert)
def generate_ai_anomaly_warning(customer_id: int):
    anomaly_report = detect_spending_anomalies(customer_id=customer_id)
    
    customer_name = "Valued Customer"
    for c in customers_db:
        if c.id == customer_id:
            customer_name = c.name
            break

    if not anomaly_report.anomalies_found:
        return AIAnomalyAlert(
            customer_id=customer_id,
            anomalies_detected=0,
            ai_warning_message=f"Hi {customer_name.split()[0]}, we reviewed your recent account history and everything looks completely normal.",
            engine_used="system-static"
        )

    anomaly_details = ""
    for item in anomaly_report.anomalies_found:
        anomaly_details += (
            f"- Transaction: '{item.title}' in the '{item.category}' category.\n"
            f"  Amount Flagged: ${abs(item.amount):.2f}\n"
            f"  Your Normal Category Average: ${item.average_category_spending:.2f}\n"
            f"  Z-Score (Standard Deviations Away): {item.deviation_multiplier}\n"
            f"  Transaction Date: {item.transaction_date}\n\n"
        )

    llm_prompt = (
        f"You are a helpful, professional personal banking AI coach. "
        f"We have detected unusual spending irregularities in customer {customer_name}'s recent history ledger. "
        f"Write a friendly warning notification alert email explaining this occurrence.\n\n"
        f"--- CONTEXT OF DETECTED STATISTICAL SPIKES ---\n{anomaly_details}"
        f"Instructions:\n"
        f"- Greet the customer warmly by their first name ({customer_name.split()[0]}).\n"
        f"- Explain the anomaly clearly using the provided data points without sounding alarmist.\n"
        f"- Do not use technical statistics terms like 'Z-Score' or 'Standard Deviation' in the final response. Translate them into plain language (e.g., 'way higher than your typical range').\n"
        f"- Keep the message clean, under 4 sentences, and avoid raw markdown tags."
    )

    # --- GEMINI ROUTE ---
    if gemini_client is not None:
        try:
            logger.info("Generating advice text via Gemini 3.5 Flash-Lite...")
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
            logger.warning(f"Gemini API issue occurred: {str(gemini_err)}. Falling back to Ollama...")

    # --- OLLAMA FALLBACK ROUTE ---
    try:
        logger.info("Generating advice text via local Ollama container (llama3)...")
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
        raise HTTPException(
            status_code=503,
            detail=f"Financial Notification System failure. Error trace: {str(ollama_err)}"
        )
