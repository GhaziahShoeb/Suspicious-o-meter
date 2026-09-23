from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch


client = TestClient(app)

def test_scan_returns_complete_status():
    response = client.post("/scan", json={
        "url": "https://example.com/test-job",
        "text": "We are hiring a Software Engineer. Competitive salary, remote work available."
    })

    assert response.status_code == 200
    data = response.json()
    assert "suspicion_score" in data
    assert "verdict" in data

def test_scan_handles_llm_failure_gracefully():
    with patch("verdict_engine.analyze_with_llm", side_effect=Exception("Simulated LLM failure")):
        response = client.post("/scan", json={
            "url": "https://example.com/test-job",
            "text": "Some job posting text"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["verdict"] == "ERROR"

def test_scan_rejects_empty_text():
    response = client.post("/scan", json={
        "url": "https://example.com/test-job",
        "text": ""
    })

    assert response.status_code == 422