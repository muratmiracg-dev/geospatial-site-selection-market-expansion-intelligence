"""API request and response contracts."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, model_validator

from site_intelligence.constants import SCORE_FACTORS


class ScoreRequest(BaseModel):
    candidate_id: str = Field(pattern=r"^C\d{2}$")
    weights: dict[str, Annotated[float, Field(ge=0.0, le=1.0)]] | None = None

    @model_validator(mode="after")
    def validate_weights(self) -> ScoreRequest:
        if self.weights is None:
            return self
        if set(self.weights) != set(SCORE_FACTORS):
            raise ValueError(f"weights must contain exactly: {', '.join(SCORE_FACTORS)}")
        if sum(self.weights.values()) <= 0:
            raise ValueError("weight total must be positive")
        return self


class ScenarioRequest(BaseModel):
    scenario: str = Field(pattern=r"^(optimistic|base|pessimistic)$")


class HealthResponse(BaseModel):
    status: str
    data_ready: bool
    model_ready: bool
    version: str
