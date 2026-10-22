import pytest
from datetime import date
from fastapi.testclient import TestClient
from core.schemas import Customer, Transaction

@pytest.fixture(autouse=True)
def mock_in_memory_db(monkeypatch):
    """Securely patches the database arrays across the core storage and target routing modules."""
    test_customers = [
        Customer(id=1, name="Test User", email="test@example.com")
    ]
    
    test_transactions = [
        Transaction(id=1, customer_id=1, title="Rent 1", amount=-1000.0, category="Rent", transaction_date=date(2026, 10, 1), is_completed=True),
        Transaction(id=2, customer_id=1, title="Rent 2", amount=-1000.0, category="Rent", transaction_date=date(2026, 10, 2), is_completed=True),
        Transaction(id=3, customer_id=1, title="Rent 3", amount=-1000.0, category="Rent", transaction_date=date(2026, 10, 3), is_completed=True),
        Transaction(id=4, customer_id=1, title="Coffee 1", amount=-10.0, category="Dining", transaction_date=date(2026, 10, 4), is_completed=True),
        Transaction(id=5, customer_id=1, title="Coffee 2", amount=-10.0, category="Dining", transaction_date=date(2026, 10, 5), is_completed=True),
        Transaction(id=6, customer_id=1, title="Coffee 3", amount=-10.0, category="Dining", transaction_date=date(2026, 10, 6), is_completed=True),
        Transaction(id=7, customer_id=1, title="Huge Dinner", amount=-90.0, category="Dining", transaction_date=date(2026, 10, 7), is_completed=True),
        Transaction(id=8, customer_id=1, title="Salary", amount=3000.0, category="Income", transaction_date=date(2026, 10, 1), is_completed=True)
    ]
    
    # Patch core layer
    import core.database
    monkeypatch.setattr(core.database, "customers_db", test_customers)
    monkeypatch.setattr(core.database, "transactions_db", test_transactions)
    
    # Patch security auth engine layer
    import core.auth
    monkeypatch.setattr(core.auth, "customers_db", test_customers)

    # Patch routing modules to override localized variable memory imports
    import routers.auth
    import routers.anomalies
    monkeypatch.setattr(routers.auth, "customers_db", test_customers)
    monkeypatch.setattr(routers.anomalies, "customers_db", test_customers)
    monkeypatch.setattr(routers.anomalies, "transactions_db", test_transactions)

@pytest.fixture
def client():
    """Provides a fresh FastAPI test client instance for testing requests."""
    from main import app
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def valid_token_headers(client, mock_in_memory_db):
    """Helper fixture to log in and return authorization bearer token headers."""
    response = client.post("/auth/login", data={"username": "test@example.com", "password": "password123"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
