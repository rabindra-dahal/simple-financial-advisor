from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load all variables from the .env file immediately at bootup
load_dotenv()

from fastapi import FastAPI
from routers import customers, transactions, analytics, advisor
from core.vector_db import index_transactions_to_vector_store

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing components and loading data structures...")
    index_transactions_to_vector_store()
    yield
    print("Cleaning up app resources...")

app = FastAPI(
    title="Modular Fintech AI Backend",
    version="3.1.0",
    lifespan=lifespan
)

app.include_router(customers.router)
app.include_router(transactions.router)
app.include_router(analytics.router)
app.include_router(advisor.router)
