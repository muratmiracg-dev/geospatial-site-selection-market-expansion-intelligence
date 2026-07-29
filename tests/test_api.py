from __future__ import annotations

from fastapi.testclient import TestClient

from site_intelligence.api.app import create_app
from site_intelligence.constants import SCORE_FACTORS


def test_health_and_candidates(project_root) -> None:
    client = TestClient(create_app(project_root))
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["data_ready"] is True
    response = client.get("/v1/candidates", params={"limit": 3})
    assert response.status_code == 200
    assert len(response.json()) == 3
    assert response.headers["X-Decision-Support-Only"] == "true"


def test_candidate_detail_and_not_found(project_root) -> None:
    client = TestClient(create_app(project_root))
    assert client.get("/v1/candidates/C24").status_code == 200
    assert client.get("/v1/candidates/C99").status_code == 404


def test_custom_weight_scoring(project_root) -> None:
    client = TestClient(create_app(project_root))
    weights = dict.fromkeys(SCORE_FACTORS, 1.0)
    response = client.post("/v1/score", json={"candidate_id": "C24", "weights": weights})
    assert response.status_code == 200
    payload = response.json()
    assert 0 <= payload["score"] <= 100
    assert len(payload["contributions"]) == len(SCORE_FACTORS)
    assert client.post("/v1/score", json={"candidate_id": "C99"}).status_code == 404


def test_scenario_and_metrics(project_root) -> None:
    client = TestClient(create_app(project_root))
    response = client.post("/v1/scenarios/evaluate", json={"scenario": "base"})
    assert response.status_code == 200
    assert response.json()["summary"]["solver_status"] == "Optimal"
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "site_intelligence_http_requests_total" in metrics.text
