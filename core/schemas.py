from datetime import date
from typing import Optional
from pydantic import BaseModel, Field

# --- CUSTOMER SCHEMAS ---
class CustomerBase(BaseModel):
    name: str = Field(..., json_schema_extra="Alice Smith")
    email: str = Field(..., json_schema_extra="alice@example.com")

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: int

# --- TRANSACTION SCHEMAS ---
class TransactionBase(BaseModel):
    title: str = Field(..., json_schema_extra="Coffee Shop")
    amount: float = Field(..., description="Positive for income, negative for expense")
    category: str = Field(..., json_schema_extra="Food & Dining")
    transaction_date: date = Field(default_factory=date.today)
    is_completed: bool = True

class TransactionCreate(TransactionBase):
    customer_id: int = Field(..., description="The ID of the customer who owns this transaction")

class Transaction(TransactionBase):
    id: int
    customer_id: int

# Add this at the bottom of core/schemas.py

class CategoryBreakdown(BaseModel):
    category: str
    total_spent: float

class CustomerAnalytics(BaseModel):
    customer_id: int
    total_income: float
    total_expenses: float
    net_balance: float
    spending_by_category: list[CategoryBreakdown]

# Add at the bottom of core/schemas.py

class FlaggedAnomaly(BaseModel):
    transaction_id: int
    title: str
    amount: float
    category: str
    transaction_date: date
    average_category_spending: float
    deviation_multiplier: float  # How many times higher than average this is
    reason: str

class AnomalyReport(BaseModel):
    customer_id: int
    total_transactions_analyzed: int
    anomalies_found: list[FlaggedAnomaly]

# Add at the bottom of core/schemas.py

class AIAnomalyAlert(BaseModel):
    customer_id: int
    anomalies_detected: int
    ai_warning_message: str
    engine_used: str

# Add at the bottom of core/schemas.py

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

