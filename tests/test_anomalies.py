from unittest.mock import MagicMock
import routers.anomalies

def test_z_score_anomaly_detection_math(client, valid_token_headers):
    """Verifies that the Z-Score engine math accurately flags out-of-bounds spikes."""
    # Call the math detection route directly
    response = client.get("/anomalies/customer/1", headers=valid_token_headers)
    assert response.status_code == 200
    
    report = response.json()
    assert report["customer_id"] == 1
    # Only 1 transaction (the $90 Dining spike) should clear the Z-Score >= 1.0 hurdle
    assert len(report["anomalies_found"]) == 1
    
    flagged = report["anomalies_found"][0]
    assert flagged["transaction_id"] == 7
    assert flagged["category"] == "Dining"
    assert flagged["deviation_multiplier"] >= 1.0  # Z-score metric check

def test_ai_warning_fallback_to_ollama_on_gemini_failure(client, valid_token_headers, mocker):
    """Simulates a complete Gemini API crash to verify the Ollama fallback mechanism works."""
    # 1. Force Gemini client call context to throw an Exception error
    mock_gemini = MagicMock()
    mock_gemini.models.generate_content.side_effect = Exception("Google API Quota Exhausted Limit")
    mocker.patch("routers.anomalies.gemini_client", mock_gemini)
    
    # 2. Mock Ollama to successfully return a fake generated fallback text string instead
    mock_ollama_res = {"response": "This is a fallback alert text from Ollama."}
    mocker.patch("ollama.generate", return_value=mock_ollama_res)
    
    # 3. Post to the warning generator route
    response = client.post("/anomalies/customer/1/ai-warning", headers=valid_token_headers)
    assert response.status_code == 200
    
    payload = response.json()
    assert payload["anomalies_detected"] == 1
    # Confirm the app correctly dropped to Ollama rather than crashing with a 500 error
    assert payload["engine_used"] == "ollama-llama3 (local fallback)"
    assert payload["ai_warning_message"] == "This is a fallback alert text from Ollama."
