from datetime import date
from typing import Optional
from pydantic import BaseModel, Field

# --- CUSTOMER SCHEMAS ---
class CustomerBase(BaseModel):
    name: str = Field(..., example="Alice Smith")
    email: str = Field(..., example="alice@example.com")

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: int

# --- TRANSACTION SCHEMAS ---
class TransactionBase(BaseModel):
    title: str = Field(..., example="Coffee Shop")
    amount: float = Field(..., description="Positive for income, negative for expense")
    category: str = Field(..., example="Food & Dining")
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

