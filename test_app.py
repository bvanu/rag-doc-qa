# test_app.py
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health():
    assert client.get("/").status_code == 200

def test_query_rejects_empty():
    assert client.post("/query", json={"question": "   "}).status_code == 400

def test_query_runs():
    r = client.post("/query", json={"question": "test"})
    assert r.status_code in (200, 404)