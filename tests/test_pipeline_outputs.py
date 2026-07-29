from __future__ import annotations

import json

import pandas as pd
import pytest

from site_intelligence.pipeline import run_pipeline


@pytest.mark.integration
def test_checked_in_pipeline_outputs(project_root) -> None:
    summary = json.loads(
        (project_root / "artifacts" / "metrics" / "pipeline_summary.json").read_text(
            encoding="utf-8"
        )
    )
    assert summary["run_status"] == "SUCCESS"
    assert summary["h3_cells"] > 5_000
    assert summary["quality"]["critical_failures"] == 0
    assert summary["model_metrics"]["r2"] > 0.75
    assert summary["base_incremental_covered_population"] > 0

    candidates = pd.read_csv(project_root / "artifacts" / "data" / "candidate_scores.csv")
    assert len(candidates) == 24
    assert candidates["location_rank"].is_unique
    assert candidates["location_score"].between(0, 100).all()
    assert (candidates["accessible_pop_drive_15"] >= candidates["accessible_pop_drive_10"]).all()
    assert (candidates["accessible_pop_drive_10"] >= candidates["accessible_pop_drive_5"]).all()

    scenarios = pd.read_csv(project_root / "artifacts" / "data" / "scenario_summaries.csv")
    assert set(scenarios["solver_status"]) == {"Optimal"}
    assert (scenarios["budget_utilization"] <= 1.0 + 1e-9).all()


@pytest.mark.integration
def test_end_to_end_pipeline_is_reproducible(project_root, tmp_path) -> None:
    summary = run_pipeline(tmp_path, project_root / "configs" / "base.yaml")

    assert summary["run_status"] == "SUCCESS"
    assert summary["seed"] == 20260729
    assert summary["h3_cells"] == 5965
    assert summary["top_candidate_id"] == "C24"
    assert summary["base_selected_store_count"] == 4
    assert summary["quality"]["critical_failures"] == 0

    generated = pd.read_csv(tmp_path / "artifacts" / "data" / "candidate_scores.csv")
    checked_in = pd.read_csv(project_root / "artifacts" / "data" / "candidate_scores.csv")
    pd.testing.assert_frame_equal(generated, checked_in, check_dtype=False, atol=1e-10)

    for relative in (
        "artifacts/maps/candidate_portfolio_map.html",
        "artifacts/maps/network_isochrones_map.html",
        "artifacts/figures/model_validation.png",
        "artifacts/models/demand_model.joblib",
    ):
        assert (tmp_path / relative).stat().st_size > 0
