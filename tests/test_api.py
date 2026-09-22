from fastapi.testclient import TestClient


def test_api_recommend_and_feedback(tmp_path, monkeypatch):
    monkeypatch.setenv("STATE_PATH", str(tmp_path / "policy.json"))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "decisions.db"))
    monkeypatch.setenv("POLICY_MODE", "mutable")
    from app.main import create_app

    client = TestClient(create_app())
    payload = {"recency": 3, "history": 350, "mens": 1, "womens": 0, "newbie": 0, "zip_code": "Urban", "channel": "Web"}
    response = client.post("/recommend", json=payload)
    assert response.status_code == 200
    decision_id = response.json()["decision_id"]
    feedback = client.post("/feedback", json={"decision_id": decision_id, "reward": 1})
    assert feedback.status_code == 200
    assert client.get("/health").json()["status"] == "ok"
    assert "adaptive_offers_decisions_total" in client.get("/metrics").text


def test_readonly_api_rejects_feedback(tmp_path, monkeypatch):
    monkeypatch.setenv("STATE_PATH", str(tmp_path / "policy.json"))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "decisions.db"))
    monkeypatch.setenv("POLICY_MODE", "readonly")
    from app.main import create_app

    client = TestClient(create_app())
    payload = {"recency": 3, "history": 350, "mens": 1, "womens": 0, "newbie": 0, "zip_code": "Urban", "channel": "Web"}
    decision = client.post("/recommend", json=payload).json()
    feedback = client.post("/feedback", json={"decision_id": decision["decision_id"], "reward": 1})
    assert feedback.status_code == 403
