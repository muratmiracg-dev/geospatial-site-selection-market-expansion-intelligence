"""FastAPI location-score and scenario service."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from site_intelligence import __version__
from site_intelligence.api.schemas import HealthResponse, ScenarioRequest, ScoreRequest
from site_intelligence.constants import SCORE_FACTORS

REQUESTS = Counter(
    "site_intelligence_http_requests_total",
    "HTTP requests by method, path, and status.",
    ["method", "path", "status"],
)
LATENCY = Histogram(
    "site_intelligence_http_request_duration_seconds",
    "HTTP request duration.",
    ["method", "path"],
)


def create_app(project_root: str | Path | None = None) -> FastAPI:
    """Create a data-backed API without performing analysis at request time."""

    default_root = Path(__file__).resolve().parents[3]
    root = Path(project_root or os.getenv("SITE_INTELLIGENCE_ROOT", default_root)).resolve()
    data_dir = root / "artifacts" / "data"
    model_path = root / "artifacts" / "models" / "demand_model.joblib"
    candidate_path = data_dir / "candidate_scores.csv"
    contribution_path = data_dir / "score_contributions.csv"
    scenario_path = data_dir / "scenario_summaries.csv"
    selection_path = data_dir / "scenario_selections.csv"

    application = FastAPI(
        title="Istanbul Site Intelligence API",
        version=__version__,
        description=(
            "Human-in-the-loop decision-support service backed by deterministic synthetic data. "
            "Outputs are not investment advice."
        ),
    )

    @application.middleware("http")
    async def instrument(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        route = request.url.path
        LATENCY.labels(request.method, route).observe(time.perf_counter() - started)
        REQUESTS.labels(request.method, route, str(response.status_code)).inc()
        response.headers["X-Decision-Support-Only"] = "true"
        return response

    def load_csv(path: Path) -> pd.DataFrame:
        if not path.exists():
            raise HTTPException(
                status_code=503, detail=f"Required artifact unavailable: {path.name}"
            )
        return pd.read_csv(path)

    @application.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok" if candidate_path.exists() and model_path.exists() else "degraded",
            data_ready=candidate_path.exists(),
            model_ready=model_path.exists(),
            version=__version__,
        )

    @application.get("/v1/candidates")
    def candidates(
        min_score: float = Query(default=0.0, ge=0.0, le=100.0),
        limit: int = Query(default=24, ge=1, le=100),
    ) -> list[dict]:
        frame = load_csv(candidate_path)
        columns = [
            "candidate_id",
            "candidate_name",
            "location_rank",
            "location_score",
            "predicted_sales_try_m",
            "accessible_pop_drive_10",
            "cannibalization_risk",
            "opening_cost_try_m",
            "roi_3y",
            "recommendation_tier",
            "decision_status",
        ]
        selected = frame[frame["location_score"] >= min_score].nsmallest(limit, "location_rank")
        return selected[columns].to_dict(orient="records")

    @application.get("/v1/candidates/{candidate_id}")
    def candidate(candidate_id: str) -> dict:
        frame = load_csv(candidate_path)
        selected = frame[frame["candidate_id"] == candidate_id]
        if selected.empty:
            raise HTTPException(status_code=404, detail="Candidate not found")
        return selected.iloc[0].replace({float("nan"): None}).to_dict()

    @application.post("/v1/score")
    def score(request: ScoreRequest) -> dict:
        candidates_frame = load_csv(candidate_path)
        contribution_frame = load_csv(contribution_path)
        selected = candidates_frame[candidates_frame["candidate_id"] == request.candidate_id]
        if selected.empty:
            raise HTTPException(status_code=404, detail="Candidate not found")
        row = selected.iloc[0]
        if request.weights is None:
            factor_rows = contribution_frame[
                contribution_frame["candidate_id"] == request.candidate_id
            ]
            score_value = float(factor_rows["score_contribution"].sum())
            weights = dict(zip(factor_rows["factor"], factor_rows["weight"], strict=True))
            contributions = factor_rows[
                ["factor", "normalized_value", "weight", "score_contribution"]
            ].to_dict(orient="records")
        else:
            total = sum(request.weights.values())
            weights = {factor: request.weights[factor] / total for factor in SCORE_FACTORS}
            contributions = []
            score_value = 0.0
            for factor in SCORE_FACTORS:
                normalized = float(row[f"{factor}_normalized"])
                contribution = normalized * weights[factor] * 100.0
                score_value += contribution
                contributions.append(
                    {
                        "factor": factor,
                        "normalized_value": normalized,
                        "weight": weights[factor],
                        "score_contribution": contribution,
                    }
                )
        return {
            "candidate_id": request.candidate_id,
            "candidate_name": row["candidate_name"],
            "score": round(score_value, 4),
            "weights": weights,
            "contributions": contributions,
            "normalization_scope": "checked-in 24-candidate peer set",
            "decision_status": "Human review required",
        }

    @application.post("/v1/scenarios/evaluate")
    def scenario(request: ScenarioRequest) -> dict:
        summaries = load_csv(scenario_path)
        selections = load_csv(selection_path)
        summary = summaries[summaries["scenario"] == request.scenario]
        if summary.empty:
            raise HTTPException(status_code=404, detail="Scenario not found")
        selected = selections[selections["scenario"] == request.scenario].sort_values("priority")
        return {
            "summary": summary.iloc[0].to_dict(),
            "portfolio": selected.to_dict(orient="records"),
            "execution": "precomputed deterministic optimization artifact",
            "decision_status": "Human review required",
        }

    @application.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return application


app = create_app()
