from fastapi import FastAPI
# Import the new analytics router
from routers import customers, transactions, analytics 

app = FastAPI(
    title="Modular Fintech API",
    description="A multi-module REST app separating core database configurations from API routes.",
    version="2.1.0"
)

# Include modules
app.include_router(customers.router)
app.include_router(transactions.router)
app.include_router(analytics.router)  # Register the analytics endpoints

@app.get("/")
def read_root():
    return {"status": "healthy", "message": "Welcome to the Modular Fintech API"}
