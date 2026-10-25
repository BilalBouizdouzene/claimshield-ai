from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_and_models():
    client = TestClient(app)
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/models").status_code == 200


def test_evaluation_score_endpoint_returns_measured_metrics():
    client = TestClient(app)
    response = client.post("/api/evaluation/score", json={"examples": [{
        "reference": "bonjour Alice",
        "hypothesis": "bonjour Alice",
        "reference_entities": [{"category": "PERSON", "text": "Alice"}],
        "predicted_entities": [{"category": "PERSON", "text": "Alice"}],
    }]})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "evaluated"
    assert payload["metrics"]["wer"] == 0
    assert payload["metrics"]["pii"]["f1"] == 1


def test_batch_returns_per_file_validation_errors_without_persisting_a_job():
    client = TestClient(app)
    response = client.post(
        "/api/audio/batch?model=whisper-base-int8",
        files=[("files", ("not-audio.txt", b"not audio", "text/plain"))],
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["completed"] == 0
    assert payload["failed"] == 1
    assert payload["results"][0]["status"] == "failed"

