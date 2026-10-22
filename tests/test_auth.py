def test_login_success(client, mock_in_memory_db):
    """Verifies that correct credentials receive a valid JWT access token format."""
    response = client.post("/auth/login", data={"username": "test@example.com", "password": "password123"})
    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert json_data["token_type"] == "bearer"

def test_login_bad_credentials(client, mock_in_memory_db):
    """Verifies login refusal on invalid entry values."""
    response = client.post("/auth/login", data={"username": "test@example.com", "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

def test_endpoint_unauthorized_without_token(client):
    """Ensures that protected routes block users who don't provide a token."""
    response = client.get("/anomalies/customer/1")
    assert response.status_code == 401
