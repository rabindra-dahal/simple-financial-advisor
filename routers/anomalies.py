from fastapi import APIRouter, HTTPException
from core.schemas import AnomalyReport, FlaggedAnomaly
from core.database import transactions_db, customers_db

router = APIRouter(
    prefix="/anomalies",
    tags=["Fraud & Anomalies"]
)

@router.get("/customer/{customer_id}", response_model=AnomalyReport)
def detect_spending_anomalies(customer_id: int):
    # 1. Verify customer exists
    customer_exists = any(c.id == customer_id for c in customers_db)
    if not customer_exists:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    # 2. Get all historical completed expenses (negative amounts)
    all_expenses = [
        tx for tx in transactions_db 
        if tx.customer_id == customer_id and tx.is_completed and tx.amount < 0
    ]
    
    if len(all_expenses) < 3:
        # Not enough baseline data to compute anomalies reliably
        return AnomalyReport(customer_id=customer_id, total_transactions_analyzed=len(all_expenses), anomalies_found=[])

    # Convert negative expense amounts to positive absolute values for easier averaging
    spending_by_category = {}
    for tx in all_expenses:
        spending_by_category.setdefault(tx.category, []).append(abs(tx.amount))
        
    # Calculate historical average baseline for each category
    category_baselines = {
        cat: sum(amounts) / len(amounts) 
        for cat, amounts in spending_by_category.items()
    }
    
    anomalies = []
    
    # 3. Scan transactions to find anomalies
    for tx in all_expenses:
        actual_cost = abs(tx.amount)
        avg_cost = category_baselines[tx.category]
        
        # ANOMALY RULE: Flag if a transaction is more than 2.5x the historical average for that category
        # and has a minimum absolute impact value (e.g., spending over $100 to avoid flagging small coffees)
        if actual_cost > (avg_cost * 2.5) and actual_cost > 100.0:
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
