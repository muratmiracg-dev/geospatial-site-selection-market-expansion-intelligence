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
