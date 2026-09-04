from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from site_intelligence.constants import SCORE_FACTORS
from site_intelligence.scoring import ahp_from_weights, minmax, score_candidates


def _candidate_frame() -> pd.DataFrame:
    rows = []
    for index in range(6):
        rows.append(
            {
                "candidate_id": f"C{index + 1:02d}",
                "predicted_sales_try_m": 90 + index * 4,
                "annual_opex_try_m": 11 + index,
                "opening_cost_try_m": 18 + index,
                "accessible_pop_drive_10": 100_000 + index * 20_000,
                "accessible_pop_walk_15": 15_000 + index * 2_000,
                "commercial_index": 0.4 + index * 0.05,
                "transit_index": 0.5 + index * 0.03,
                "poi_density_2km": 4 + index,
                "huff_capture_demand": 1_000 + index * 90,
                "competitor_density_3km": 3 + index,
                "huff_diversion_ratio": 0.20 + index * 0.02,
                "cannibalization_risk": 0.35 - index * 0.04,
                "delivery_risk": 0.30 - index * 0.02,
                "prediction_interval_width_try_m": 12 - index,
            }
        )
    return pd.DataFrame(rows)


def test_minmax_direction_and_constant() -> None:
    series = pd.Series([2, 4, 6])
    assert minmax(series).tolist() == [0.0, 0.5, 1.0]
    assert minmax(series, higher_is_better=False).tolist() == [1.0, 0.5, 0.0]
    assert minmax(pd.Series([5, 5])).tolist() == [0.5, 0.5]


def test_ahp_consistency() -> None:
    weights = {factor: 1 / len(SCORE_FACTORS) for factor in SCORE_FACTORS}
    matrix, derived, consistency = ahp_from_weights(weights)
    assert matrix.shape == (8, 8)
    assert derived.sum() == pytest.approx(1.0)
    assert consistency < 0.10


def test_ahp_rejects_missing_or_unexpected_factors() -> None:
    weights = dict.fromkeys(SCORE_FACTORS, 1.0)
    weights.pop(SCORE_FACTORS[0])
    weights["unsupported_factor"] = 1.0

    with pytest.raises(
        ValueError,
        match=r"missing: .*; unexpected: unsupported_factor",
    ):
        ahp_from_weights(weights)


@pytest.mark.parametrize("invalid_weight", [0.0, -0.1, np.nan, np.inf])
def test_ahp_rejects_non_positive_or_non_finite_weights(invalid_weight: float) -> None:
    weights = dict.fromkeys(SCORE_FACTORS, 1.0)
    weights[SCORE_FACTORS[0]] = invalid_weight

    with pytest.raises(ValueError, match="finite and strictly positive"):
        ahp_from_weights(weights)


def test_scoring_contributions_reconcile() -> None:
    weights = {factor: 1 / len(SCORE_FACTORS) for factor in SCORE_FACTORS}
    result = score_candidates(
        _candidate_frame(),
        weights,
        sensitivity_draws=80,
        concentration=60,
        seed=42,
    )
    assert sorted(result.candidates["location_rank"]) == list(range(1, 7))
    totals = result.contributions.groupby("candidate_id")["score_contribution"].sum()
    scores = result.candidates.set_index("candidate_id")["location_score"]
    for candidate_id in totals.index:
        assert totals[candidate_id] == pytest.approx(scores[candidate_id], abs=0.002)
    assert set(result.sensitivity["candidate_id"]) == set(_candidate_frame()["candidate_id"])
