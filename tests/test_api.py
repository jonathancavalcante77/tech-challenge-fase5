import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def test_home_presents_localized_examples_without_changing_dataset_values(
    tmp_path, snapshot_path, monkeypatch
):
    from datathon.golden import GOLDEN_SET, case_context

    monkeypatch.setenv("STATE_PATH", str(tmp_path / "policy.json"))
    monkeypatch.setenv("SNAPSHOT_PATH", str(snapshot_path))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "decisions.db"))
    from app.main import create_app

    with TestClient(create_app()) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert 'value="Surburban">Suburbana<' in response.text
    assert 'value="Phone">Telefone<' in response.text
    assert "Não entram na escolha atual" in response.text
    assert "Dados técnicos da decisão" in response.text
    assert 'id="theme-toggle"' in response.text
    assert 'type="checkbox" value="1" checked' in response.text
    assert response.text.count('data-example="') == 5
    match = re.search(r"window\.examples = (\[.*?\]);", response.text)
    assert match is not None
    examples = json.loads(match.group(1))
    assert [item["context"] for item in examples] == [case_context(case) for case in GOLDEN_SET]


def test_api_recommend_and_feedback(tmp_path, snapshot_path, monkeypatch):
    monkeypatch.setenv("STATE_PATH", str(tmp_path / "policy.json"))
    monkeypatch.setenv("SNAPSHOT_PATH", str(snapshot_path))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "decisions.db"))
    monkeypatch.setenv("POLICY_MODE", "mutable")
    from app.main import create_app

    client = TestClient(create_app())
    payload = {
        "recency": 3,
        "history": 350,
        "mens": 1,
        "womens": 0,
        "newbie": 0,
        "zip_code": "Urban",
        "channel": "Web",
    }
    response = client.post("/recommend", json=payload)
    assert response.status_code == 200
    assert response.json()["policy_version"] == "test-snapshot"
    decision_id = response.json()["decision_id"]
    feedback = client.post("/feedback", json={"decision_id": decision_id, "reward": 1})
    assert feedback.status_code == 200
    assert client.get("/health").json()["status"] == "ok"
    metrics = client.get("/metrics").text
    assert "adaptive_offers_http_requests_total" in metrics
    assert "adaptive_offers_recommendations_total" in metrics


def test_readonly_api_rejects_feedback(tmp_path, snapshot_path, monkeypatch):
    monkeypatch.setenv("STATE_PATH", str(tmp_path / "policy.json"))
    monkeypatch.setenv("SNAPSHOT_PATH", str(snapshot_path))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "decisions.db"))
    monkeypatch.setenv("POLICY_MODE", "readonly")
    from app.main import create_app

    client = TestClient(create_app())
    payload = {
        "recency": 3,
        "history": 350,
        "mens": 1,
        "womens": 0,
        "newbie": 0,
        "zip_code": "Urban",
        "channel": "Web",
    }
    decision = client.post("/recommend", json=payload).json()
    feedback = client.post("/feedback", json={"decision_id": decision["decision_id"], "reward": 1})
    assert feedback.status_code == 403


def test_api_rejects_invalid_context(tmp_path, snapshot_path, monkeypatch):
    monkeypatch.setenv("STATE_PATH", str(tmp_path / "policy.json"))
    monkeypatch.setenv("SNAPSHOT_PATH", str(snapshot_path))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "decisions.db"))
    monkeypatch.setenv("POLICY_MODE", "mutable")
    from app.main import create_app

    client = TestClient(create_app())
    response = client.post(
        "/recommend",
        json={
            "recency": 0,
            "history": -1,
            "mens": 2,
            "womens": 0,
            "newbie": 0,
            "zip_code": "Urban",
            "channel": "Web",
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "field,value",
    [("channel", "Unknown"), ("zip_code", "12345"), ("history", "inf"), ("name", "Cliente")],
)
def test_api_rejects_unsupported_or_personal_fields(
    field, value, tmp_path, snapshot_path, context, monkeypatch
):
    monkeypatch.setenv("STATE_PATH", str(tmp_path / "policy.json"))
    monkeypatch.setenv("SNAPSHOT_PATH", str(snapshot_path))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "decisions.db"))
    monkeypatch.setenv("POLICY_MODE", "mutable")
    from app.main import create_app

    with TestClient(create_app()) as client:
        response = client.post("/recommend", json={**context, field: value})
        assert response.status_code == 422
        assert client.get("/metadata").json()["store"]["decisions"] == 0


def test_five_golden_inputs_work_through_api(tmp_path, monkeypatch):
    from datathon.golden import CASE_EXPECTATIONS, GOLDEN_SET, case_context

    monkeypatch.setenv("STATE_PATH", str(tmp_path / "policy.json"))
    monkeypatch.setenv("SNAPSHOT_PATH", str(Path("config/policy_snapshot.json").resolve()))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "decisions.db"))
    monkeypatch.setenv("POLICY_MODE", "readonly")
    from app.main import create_app

    with TestClient(create_app()) as client:
        for case in GOLDEN_SET:
            response = client.post("/recommend", json=case_context(case))
            assert response.status_code == 200
            result = response.json()
            assert result["segment"] == CASE_EXPECTATIONS[case["case_id"]]["segment"]
            assert result["action"] in {"mens_email", "womens_email", "no_email"}
        assert client.get("/metadata").json()["store"]["decisions"] == 0


@pytest.mark.parametrize("mode", ["mutable", "readonly"])
@pytest.mark.parametrize("recency", [2, 5, 9])
def test_api_rejects_untrained_segments_without_changing_state(
    mode, recency, tmp_path, context, monkeypatch
):
    monkeypatch.setenv("STATE_PATH", str(tmp_path / "policy.json"))
    monkeypatch.setenv("SNAPSHOT_PATH", str(Path("config/policy_snapshot.json").resolve()))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "decisions.db"))
    monkeypatch.setenv("POLICY_MODE", mode)
    from app.main import create_app

    application = create_app()
    service = application.state.service
    before = service.policy.to_json()
    with TestClient(application) as client:
        response = client.post(
            "/recommend", json={**context, "recency": recency, "mens": 0, "womens": 0}
        )
        assert response.status_code == 422
        assert "Não há dados de treino" in response.json()["detail"]
        assert service.policy.to_json() == before
        assert service.store.stats() == {"decisions": 0, "feedbacks": 0}
        assert client.post("/recommend", json=context).status_code == 200
