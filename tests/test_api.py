from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_query_empty():
    resp = client.post("/query", json={"query": "test", "top_k": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert "answer" in body
    assert "sources" in body
