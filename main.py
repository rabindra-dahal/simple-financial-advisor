from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
# Import your new anomalies router module
from routers import customers, transactions, analytics, advisor, anomalies 
from core.vector_db import index_transactions_to_vector_store

@asynccontextmanager
async def lifespan(app: FastAPI):
    index_transactions_to_vector_store()
    yield

app = FastAPI(
    title="Modular Fintech AI Backend",
    version="3.2.0",
    lifespan=lifespan
)

app.include_router(customers.router)
app.include_router(transactions.router)
app.include_router(analytics.router)
app.include_router(advisor.router)
app.include_router(anomalies.router)  # Register anomalies router code
