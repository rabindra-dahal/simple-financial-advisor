import csv
import os
from datetime import datetime
from typing import List
from core.schemas import Customer, Transaction

# Find absolute file paths relative to this file's position
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CUSTOMERS_CSV = os.path.join(BASE_DIR, "data", "customers.csv")
TRANSACTIONS_CSV = os.path.join(BASE_DIR, "data", "transactions.csv")

# Core datasets used across routers
customers_db: List[Customer] = []
transactions_db: List[Transaction] = []

def load_initial_data():
    """Parses raw CSV data tables into typed Pydantic models on application bootup."""
    global customers_db, transactions_db
    
    # 1. Load and parse Customers CSV
    if os.path.exists(CUSTOMERS_CSV):
        with open(CUSTOMERS_CSV, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            customers_db = [
                Customer(
                    id=int(row["id"]),
                    name=row["name"],
                    email=row["email"]
                ) for row in reader
            ]

    # 2. Load and parse Transactions CSV
    if os.path.exists(TRANSACTIONS_CSV):
        with open(TRANSACTIONS_CSV, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            transactions_db = [
                Transaction(
                    id=int(row["id"]),
                    customer_id=int(row["customer_id"]),
                    title=row["title"],
                    amount=float(row["amount"]),
                    category=row["category"],
                    transaction_date=datetime.strptime(row["transaction_date"], "%Y-%m-%d").date(),
                    is_completed=row["is_completed"].strip().lower() == "true"
                ) for row in reader
            ]

# Execute parsing sequence immediately upon engine import
load_initial_data()
