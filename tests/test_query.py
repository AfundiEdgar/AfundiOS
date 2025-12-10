from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_query_basic():
    resp = client.post("/query", json={"query": "hello world"})
    assert resp.status_code == 200
