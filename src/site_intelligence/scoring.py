"""Auditable AHP-derived weighted scoring and assumption sensitivity."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from site_intelligence.constants import SCORE_FACTORS


@dataclass(frozen=True)
class ScoreResult:
    candidates: pd.DataFrame
    contributions: pd.DataFrame
    factor_specification: pd.DataFrame
    ahp_matrix: pd.DataFrame
    ahp_consistency_ratio: float
    sensitivity: pd.DataFrame
    one_at_a_time: pd.DataFrame


def minmax(series: pd.Series, *, higher_is_better: bool = True) -> pd.Series:
    """Min-max normalize with explicit direction and constant-column handling."""

    numeric = series.astype(float)
    span = numeric.max() - numeric.min()
    normalized = (
        pd.Series(0.5, index=series.index, dtype=float)
        if span == 0
        else (numeric - numeric.min()) / span
    )
    return normalized if higher_is_better else 1.0 - normalized


def ahp_from_weights(weights: dict[str, float]) -> tuple[pd.DataFrame, pd.Series, float]:
    """Create a fully consistent reciprocal AHP comparison matrix."""

    ordered = pd.Series({factor: float(weights[factor]) for factor in SCORE_FACTORS})
    ordered = ordered / ordered.sum()
    matrix = np.divide.outer(ordered.to_numpy(), ordered.to_numpy())
    eigenvalues, eigenvectors = np.linalg.eig(matrix)
    principal = int(np.argmax(eigenvalues.real))
    vector = np.abs(eigenvectors[:, principal].real)
    vector /= vector.sum()
    n = len(ordered)
    lambda_max = float(eigenvalues[principal].real)
    consistency_index = (lambda_max - n) / (n - 1)
    random_index = {8: 1.41}.get(n, 1.41)
    consistency_ratio = max(0.0, consistency_index / random_index)
    return (
        pd.DataFrame(matrix, index=ordered.index, columns=ordered.index),
        pd.Series(vector, index=ordered.index),
        consistency_ratio,
    )


def _derive_factors(candidates: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    result = candidates.copy()
    result["expected_ebit_try_m"] = np.round(
        result["predicted_sales_try_m"] * 0.205 - result["annual_opex_try_m"],
        3,
    )
    result["roi_3y"] = np.round(
        (result["expected_ebit_try_m"] * 3 - result["opening_cost_try_m"])
        / result["opening_cost_try_m"],
        6,
    )
    result["payback_months"] = np.where(
        result["expected_ebit_try_m"] > 0,
        np.round(result["opening_cost_try_m"] / result["expected_ebit_try_m"] * 12, 2),
        np.nan,
    )
    result["market_potential"] = result["predicted_sales_try_m"]
    result["accessibility"] = (
        result["accessible_pop_drive_10"] * 0.72 + result["accessible_pop_walk_15"] * 0.28
    )
    result["commercial_attraction"] = (
        result["commercial_index"] * 0.35
        + result["transit_index"] * 0.25
        + np.log1p(result["poi_density_2km"]) * 0.18
        + result["huff_capture_demand"] / result["huff_capture_demand"].max() * 0.22
    )
    result["white_space"] = (
        result["huff_capture_demand"]
        / (1.0 + result["competitor_density_3km"])
        * (1.0 - 0.55 * result["huff_diversion_ratio"])
    )
    result["cost_efficiency"] = 1.0 / (
        result["opening_cost_try_m"] + result["annual_opex_try_m"] * 0.55
    )
    result["cannibalization_resilience"] = 1.0 - result["cannibalization_risk"]
    result["profitability"] = result["roi_3y"]
    result["delivery_confidence"] = (1.0 - result["delivery_risk"]) / (
        1.0 + result["prediction_interval_width_try_m"] / result["predicted_sales_try_m"]
    )

    specification = pd.DataFrame(
        [
            ("market_potential", "Predicted annual sales", "higher", "min-max", "TRY million"),
            (
                "accessibility",
                "10-min drive + 15-min walk population",
                "higher",
                "min-max",
                "people",
            ),
            (
                "commercial_attraction",
                "Commercial, transit, POI and Huff pull",
                "higher",
                "min-max",
                "index",
            ),
            (
                "white_space",
                "Capture adjusted for competition and diversion",
                "higher",
                "min-max",
                "index",
            ),
            (
                "cost_efficiency",
                "Inverse opening and operating cost burden",
                "higher",
                "min-max",
                "inverse TRY",
            ),
            (
                "cannibalization_resilience",
                "One minus overlap/diversion risk",
                "higher",
                "min-max",
                "index",
            ),
            ("profitability", "Three-year ROI proxy", "higher", "min-max", "ratio"),
            (
                "delivery_confidence",
                "Execution and prediction certainty",
                "higher",
                "min-max",
                "index",
            ),
        ],
        columns=["factor", "definition", "direction", "normalization", "unit"],
    )
    return result, specification


def score_candidates(
    candidates: pd.DataFrame,
    weights: dict[str, float],
    *,
    sensitivity_draws: int,
    concentration: float,
    seed: int,
) -> ScoreResult:
    """Score candidates, expose factor contributions, and quantify rank stability."""

    result, specification = _derive_factors(candidates)
    matrix, ahp_weights, consistency_ratio = ahp_from_weights(weights)
    normalized = pd.DataFrame(index=result.index)
    for factor in SCORE_FACTORS:
        normalized[factor] = minmax(result[factor], higher_is_better=True)
        result[f"{factor}_normalized"] = np.round(normalized[factor], 6)

    weighted = normalized.mul(ahp_weights, axis=1)
    result["location_score"] = np.round(weighted.sum(axis=1) * 100.0, 3)
    result["location_rank"] = (
        result["location_score"].rank(method="min", ascending=False).astype(int)
    )
    result = result.sort_values(["location_rank", "candidate_id"]).reset_index(drop=True)

    contributions = []
    for _, row in result.iterrows():
        for factor in SCORE_FACTORS:
            normalized_value = float(row[f"{factor}_normalized"])
            weight = float(ahp_weights[factor])
            contributions.append(
                {
                    "candidate_id": row["candidate_id"],
                    "factor": factor,
                    "raw_value": float(row[factor]),
                    "normalized_value": normalized_value,
                    "weight": weight,
                    "score_contribution": normalized_value * weight * 100.0,
                }
            )
    contribution_frame = pd.DataFrame(contributions)
    specification["weight"] = specification["factor"].map(ahp_weights).astype(float)

    norm_by_candidate = result.set_index("candidate_id")[
        [f"{factor}_normalized" for factor in SCORE_FACTORS]
    ]
    norm_by_candidate.columns = SCORE_FACTORS
    rng = np.random.default_rng(seed + 211)
    sampled_weights = rng.dirichlet(ahp_weights.to_numpy() * concentration, size=sensitivity_draws)
    sampled_scores = norm_by_candidate.to_numpy() @ sampled_weights.T
    ranks = np.argsort(np.argsort(-sampled_scores, axis=0), axis=0) + 1
    sensitivity_rows = []
    for candidate_index, candidate_id in enumerate(norm_by_candidate.index):
        candidate_ranks = ranks[candidate_index, :]
        sensitivity_rows.append(
            {
                "candidate_id": candidate_id,
                "mean_rank": float(candidate_ranks.mean()),
                "rank_p05": float(np.quantile(candidate_ranks, 0.05)),
                "rank_p95": float(np.quantile(candidate_ranks, 0.95)),
                "top_3_probability": float(np.mean(candidate_ranks <= 3)),
                "top_5_probability": float(np.mean(candidate_ranks <= 5)),
                "rank_1_probability": float(np.mean(candidate_ranks == 1)),
            }
        )
    sensitivity = pd.DataFrame(sensitivity_rows).sort_values("mean_rank")

    base_weights = ahp_weights.to_dict()
    one_at_a_time_rows = []
    for factor in SCORE_FACTORS:
        for change in (-0.20, 0.20):
            adjusted = base_weights.copy()
            adjusted[factor] *= 1.0 + change
            total = sum(adjusted.values())
            adjusted = {key: value / total for key, value in adjusted.items()}
            scores = norm_by_candidate @ pd.Series(adjusted)
            winner = str(scores.idxmax())
            one_at_a_time_rows.append(
                {
                    "factor": factor,
                    "weight_change": change,
                    "winner_candidate_id": winner,
                    "winner_score": float(scores.max() * 100.0),
                    "top_5_overlap_with_base": len(
                        set(scores.nlargest(5).index)
                        & set(result.nsmallest(5, "location_rank")["candidate_id"])
                    )
                    / 5.0,
                }
            )
    return ScoreResult(
        candidates=result,
        contributions=contribution_frame,
        factor_specification=specification,
        ahp_matrix=matrix,
        ahp_consistency_ratio=consistency_ratio,
        sensitivity=sensitivity,
        one_at_a_time=pd.DataFrame(one_at_a_time_rows),
    )
