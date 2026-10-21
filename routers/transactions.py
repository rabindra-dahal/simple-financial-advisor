from typing import List
from fastapi import APIRouter, HTTPException
from core.schemas import Transaction, TransactionCreate
from core.database import customers_db, transactions_db


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)

@router.get("", response_model=List[Transaction])
def get_all_transactions():
    return transactions_db

@router.post("", response_model=Transaction, status_code=201)
def create_transaction(tx_data: TransactionCreate):
    # Core logic check: Ensure the customer exists before attaching a transaction
    customer_exists = any(c.id == tx_data.customer_id for c in customers_db)
    if not customer_exists:
        raise HTTPException(status_code=400, detail="Cannot create transaction: Customer does not exist.")

    new_id = max([tx.id for tx in transactions_db], default=0) + 1
    new_tx = Transaction(id=new_id, **tx_data.model_dump())
    transactions_db.append(new_tx)
    return new_tx

@router.get("/customer/{customer_id}", response_model=List[Transaction])
def get_transactions_by_customer(customer_id: int):
    return [tx for tx in transactions_db if tx.customer_id == customer_id]
