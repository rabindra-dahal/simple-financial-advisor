from typing import List
from fastapi import APIRouter, HTTPException
from core.schemas import Customer, CustomerCreate
from core.database import customers_db, transactions_db

router = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)

@router.get("", response_model=List[Customer])
def get_customers():
    return customers_db

@router.get("/{customer_id}", response_model=Customer)
def get_customer(customer_id: int):
    for c in customers_db:
        if c.id == customer_id:
            return c
    raise HTTPException(status_code=404, detail="Customer not found")

@router.post("", response_model=Customer, status_code=201)
def create_customer(customer_data: CustomerCreate):
    new_id = max([c.id for c in customers_db], default=0) + 1
    new_customer = Customer(id=new_id, **customer_data.model_dump())
    customers_db.append(new_customer)
    return new_customer
