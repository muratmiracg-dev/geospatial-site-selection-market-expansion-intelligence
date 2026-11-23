from __future__ import annotations

import numpy as np
import pytest

from site_intelligence.optimization import _validate_optimization_controls

VALID = {
    "Base": {
        "demand_multiplier": 1.0,
        "cost_multiplier": 1.0,
        "budget_try_m": 100.0,
        "max_stores": 4,
    }
}


@pytest.mark.parametrize(
    ("scenarios", "distance", "minutes"),
    [
        ({}, 2.0, 10),
        (VALID, -1.0, 10),
        (VALID, np.nan, 10),
        (VALID, 2.0, 0),
        (VALID, 2.0, True),
        ({"Base": {"budget_try_m": 100.0}}, 2.0, 10),
        ({"Base": {**VALID["Base"], "budget_try_m": np.inf}}, 2.0, 10),
        ({"Base": {**VALID["Base"], "max_stores": 2.5}}, 2.0, 10),
    ],
)
def test_optimization_controls_fail_closed(
    scenarios: dict[str, dict[str, float]], distance: float, minutes: int
) -> None:
    with pytest.raises(ValueError):
        _validate_optimization_controls(scenarios, distance, minutes)


def test_optimization_controls_accept_valid_scenario() -> None:
    _validate_optimization_controls(VALID, 2.0, 10)


@pytest.mark.parametrize("floor", [np.nan, np.inf, True])
def test_portfolio_ebit_floor_must_be_finite(floor) -> None:
    with pytest.raises(ValueError, match="minimum_portfolio_ebit_try_m"):
        _validate_optimization_controls(VALID, 2.0, 10, floor)


def _toy_problem():
    import geopandas as gpd
    import pandas as pd
    from shapely.geometry import Point

    from site_intelligence.accessibility import Reachability

    # A loses TRY 1m/year but covers 1m uncovered people (objective +7); B earns TRY 2m.
    candidates = pd.DataFrame(
        {
            "candidate_id": ["A", "B"],
            "candidate_name": ["A", "B"],
            "predicted_sales_try_m": [10.0, 20.0],
            "annual_opex_try_m": [3.05, 2.1],
            "opening_cost_try_m": [10.0, 10.0],
            "location_score": [0.0, 0.0],
            "cannibalization_risk": [0.0, 0.0],
            "location_rank": [1, 2],
        }
    )
    geodata = gpd.GeoDataFrame(
        candidates[["candidate_id"]],
        geometry=[Point(28.9, 41.0), Point(29.2, 41.1)],
        crs="EPSG:4326",
    )
    grid = pd.DataFrame({"h3_cell": ["cA", "cB"], "population": [1_000_000, 10]})

    def reach(cells):
        return Reachability("x", "drive", 10, frozenset(cells), 0, 0.0)

    cache = {("A", "drive", 10): reach({"cA"}), ("B", "drive", 10): reach({"cB"})}
    existing = pd.DataFrame({"store_id": pd.Series([], dtype=str)})
    scenario = {
        "s": {
            "demand_multiplier": 1.0,
            "cost_multiplier": 1.0,
            "budget_try_m": 30.0,
            "max_stores": 2,
        }
    }
    return candidates, geodata, existing, grid, cache, scenario


def test_optimizer_does_not_recommend_a_loss_making_portfolio() -> None:
    from site_intelligence.optimization import optimize_portfolios

    candidates, geodata, existing, grid, cache, scenario = _toy_problem()
    candidates.loc[candidates["candidate_id"] == "B", "annual_opex_try_m"] = 5.0  # B loses 1m
    common = {"minimum_distance_km": 0.0, "coverage_minutes": 10}
    unconstrained = optimize_portfolios(
        candidates,
        geodata,
        existing,
        grid,
        cache,
        {},
        scenario,
        **common,
        minimum_portfolio_ebit_try_m=-1e9,
    )
    assert unconstrained.summaries.loc[0, "portfolio_expected_ebit_try_m"] < 0
    guarded = optimize_portfolios(
        candidates, geodata, existing, grid, cache, {}, scenario, **common
    )
    summary = guarded.summaries.loc[0]
    assert summary["solver_status"] == "Optimal"
    assert summary["portfolio_expected_ebit_try_m"] >= 0


def test_checked_in_scenarios_do_not_lose_money(project_root) -> None:
    import pandas as pd

    summaries = pd.read_csv(project_root / "artifacts" / "data" / "scenario_summaries.csv")
    assert (summaries["portfolio_expected_ebit_try_m"] >= 0).all()
