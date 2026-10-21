from fastapi import APIRouter, HTTPException
from core.schemas import CustomerAnalytics, CategoryBreakdown
from core.database import customers_db, transactions_db


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)

@router.get("/customer/{customer_id}", response_model=CustomerAnalytics)
def get_customer_balances(customer_id: int):
    # 1. Validate that the customer exists
    customer_exists = any(c.id == customer_id for c in customers_db)
    if not customer_exists:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    # 2. Filter transactions belonging only to this customer
    user_txs = [tx for tx in transactions_db if tx.customer_id == customer_id and tx.is_completed]
    
    # 3. Calculate financial sums
    total_income = sum(tx.amount for tx in user_txs if tx.amount > 0)
    total_expenses = sum(tx.amount for tx in user_txs if tx.amount < 0)
    net_balance = total_income + total_expenses
    
    # 4. Compute categorical spending breakdown
    category_map = {}
    for tx in user_txs:
        if tx.amount < 0:  # Only track expenses for spending metrics
            # Convert negative amounts to positive for easier-to-read spending metrics
            category_map[tx.category] = category_map.get(tx.category, 0.0) + abs(tx.amount)
            
    spending_breakdown = [
        CategoryBreakdown(category=cat, total_spent=round(amt, 2))
        for cat, amt in category_map.items()
    ]
    
    return CustomerAnalytics(
        customer_id=customer_id,
        total_income=round(total_income, 2),
        total_expenses=round(abs(total_expenses), 2),  # Display as positive total expense
        net_balance=round(net_balance, 2),
        spending_by_category=spending_breakdown
    )
