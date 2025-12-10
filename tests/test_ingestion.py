from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_ingest_missing_payload():
    resp = client.post("/ingest")
    assert resp.status_code in (400, 422)
