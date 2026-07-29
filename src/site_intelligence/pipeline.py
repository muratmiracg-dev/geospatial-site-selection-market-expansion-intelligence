"""End-to-end deterministic analytics pipeline."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import geopandas as gpd
import h3
import numpy as np
import pandas as pd

from site_intelligence.accessibility import build_transport_graph, calculate_location_reachability
from site_intelligence.config import ProjectPaths, load_config
from site_intelligence.data_generation import generate_all
from site_intelligence.enrichment import build_benchmark_sites, enrich_candidates
from site_intelligence.figures import (
    candidate_rank_map,
    contribution_figure,
    isochrone_figure,
    model_validation_figure,
    scenario_figure,
    scenario_portfolio_figure,
    top_candidate_figure,
    white_space_figure,
)
from site_intelligence.gravity import candidate_huff_metrics
from site_intelligence.maps import (
    create_candidate_map,
    create_isochrone_map,
    create_scenario_map,
    create_white_space_map,
)
from site_intelligence.modeling import (
    predict_candidates,
    save_model,
    spatial_cross_validate,
)
from site_intelligence.optimization import optimize_portfolios
from site_intelligence.quality import quality_summary, run_quality_suite
from site_intelligence.scoring import score_candidates


def _write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def _write_geodata(frame: gpd.GeoDataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_file(path, driver="GeoJSON")


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _add_grid_white_space(
    grid: gpd.GeoDataFrame,
    competitors: gpd.GeoDataFrame,
    existing_cache,
) -> gpd.GeoDataFrame:
    result = grid.copy()
    cell_set = set(result["h3_cell"])
    counts: dict[str, int] = {}
    for _, row in competitors.iterrows():
        cell = h3.latlng_to_cell(float(row["latitude"]), float(row["longitude"]), 8)
        if cell in cell_set:
            counts[cell] = counts.get(cell, 0) + 1
    result["competitor_count"] = result["h3_cell"].map(counts).fillna(0).astype(int)
    existing_covered: set[str] = set()
    for store_id in {key[0] for key in existing_cache if key[1:] == ("drive", 10)}:
        existing_covered.update(existing_cache[(store_id, "drive", 10)].cells)
    result["existing_covered"] = result["h3_cell"].isin(existing_covered)
    demand = result["demand_weight"].astype(float)
    demand_norm = (demand - demand.min()) / max(demand.max() - demand.min(), 1.0)
    competition_headroom = 1.0 - result["competitor_count"] / max(
        result["competitor_count"].max(), 1
    )
    opportunity = (0.72 * demand_norm + 0.28 * competition_headroom) * np.where(
        result["existing_covered"],
        0.35,
        1.0,
    )
    result["white_space_index"] = np.round(opportunity * 100.0, 2)
    return result


def run_pipeline(root: str | Path, config_path: str | Path) -> dict[str, Any]:
    """Execute the complete pipeline and persist every downstream metric."""

    started = time.perf_counter()
    paths = ProjectPaths.from_root(root)
    paths.ensure()
    config = load_config(config_path)
    seed = int(config["project"]["seed"])
    spatial = config["spatial"]

    datasets = generate_all(seed, int(spatial["h3_resolution"]))
    quality = run_quality_suite(datasets)
    _write_csv(quality, paths.artifacts / "qa" / "data_quality_checks.csv")
    _write_json(quality_summary(quality), paths.artifacts / "qa" / "data_quality_summary.json")

    graph = build_transport_graph(
        datasets["grid"],
        drive_speed_kph=float(spatial["drive_speed_kph"]),
        walk_speed_kph=float(spatial["walk_speed_kph"]),
        bridge_penalty_minutes=float(spatial["bridge_penalty_minutes"]),
    )
    thresholds = [int(value) for value in spatial["thresholds_minutes"]]
    candidate_reach, candidate_isochrones, candidate_cache = calculate_location_reachability(
        datasets["candidates"],
        datasets["grid"],
        graph,
        id_column="candidate_id",
        thresholds=thresholds,
    )
    existing_reach, _, existing_cache = calculate_location_reachability(
        datasets["existing_stores"],
        datasets["grid"],
        graph,
        id_column="store_id",
        thresholds=thresholds,
        include_geometries=False,
    )

    enriched = enrich_candidates(
        datasets["candidates"],
        datasets["existing_stores"],
        datasets["competitors"],
        datasets["pois"],
        datasets["grid"],
        candidate_reach,
        candidate_cache,
        existing_cache,
        drive_speed_kph=float(spatial["drive_speed_kph"]),
    )
    huff = candidate_huff_metrics(
        enriched,
        datasets["existing_stores"],
        datasets["grid"],
        graph,
        candidate_cache,
        existing_cache,
    )
    enriched = enriched.merge(huff, on="candidate_id", how="left")

    benchmark = build_benchmark_sites(
        datasets["grid"],
        graph,
        datasets["competitors"],
        datasets["pois"],
        datasets["existing_stores"],
        count=int(config["model"]["benchmark_site_count"]),
        seed=seed,
    )
    model_result = spatial_cross_validate(
        benchmark,
        params=config["model"]["random_forest"],
        seed=seed,
        requested_splits=int(config["model"]["cv_splits"]),
    )
    predicted, shap_contributions = predict_candidates(model_result.model, enriched)
    score_result = score_candidates(
        predicted,
        config["scoring"]["factors"],
        sensitivity_draws=int(config["scoring"]["sensitivity_draws"]),
        concentration=float(config["scoring"]["weight_concentration"]),
        seed=seed,
    )
    scored = score_result.candidates
    scored["recommendation_tier"] = np.select(
        [scored["location_rank"] <= 5, scored["location_rank"] <= 10],
        ["Priority A", "Priority B"],
        default="Monitor",
    )
    scored["decision_status"] = "Human review required"

    if "geometry" in scored.columns:
        scored_geo = gpd.GeoDataFrame(
            scored.copy(),
            geometry="geometry",
            crs=datasets["candidates"].crs,
        )
    else:
        candidate_geometry = datasets["candidates"][["candidate_id", "geometry"]]
        scored_geo = gpd.GeoDataFrame(
            scored.merge(candidate_geometry, on="candidate_id", how="left"),
            geometry="geometry",
            crs=datasets["candidates"].crs,
        )
    optimization = optimize_portfolios(
        scored,
        scored_geo,
        datasets["existing_stores"],
        datasets["grid"],
        candidate_cache,
        existing_cache,
        config["optimization"]["scenarios"],
        minimum_distance_km=float(config["optimization"]["minimum_store_distance_km"]),
        coverage_minutes=int(config["optimization"]["coverage_threshold_minutes"]),
    )

    grid = _add_grid_white_space(datasets["grid"], datasets["competitors"], existing_cache)
    datasets["grid"] = grid

    processed = paths.processed
    _write_geodata(grid, processed / "h3_microzones.geojson")
    _write_geodata(datasets["footprint"], processed / "istanbul_analytical_footprint.geojson")
    _write_geodata(datasets["candidates"], processed / "candidate_locations.geojson")
    _write_geodata(datasets["existing_stores"], processed / "existing_stores.geojson")
    _write_geodata(datasets["competitors"], processed / "competitors.geojson")
    _write_geodata(datasets["pois"], processed / "pois.geojson")
    _write_geodata(candidate_isochrones, paths.artifacts / "data" / "candidate_isochrones.geojson")
    _write_csv(benchmark, processed / "benchmark_site_performance.csv")
    _write_csv(candidate_reach, paths.artifacts / "data" / "candidate_accessibility.csv")
    _write_csv(existing_reach, paths.artifacts / "data" / "existing_store_accessibility.csv")
    _write_csv(
        pd.DataFrame(scored.drop(columns="geometry", errors="ignore")),
        paths.artifacts / "data" / "candidate_scores.csv",
    )
    _write_csv(score_result.contributions, paths.artifacts / "data" / "score_contributions.csv")
    _write_csv(shap_contributions, paths.artifacts / "data" / "shap_contributions.csv")
    _write_csv(
        score_result.factor_specification, paths.artifacts / "data" / "factor_specification.csv"
    )
    _write_csv(
        score_result.ahp_matrix.reset_index(names="factor"),
        paths.artifacts / "data" / "ahp_pairwise_matrix.csv",
    )
    _write_csv(score_result.sensitivity, paths.artifacts / "data" / "weight_sensitivity.csv")
    _write_csv(
        score_result.one_at_a_time, paths.artifacts / "data" / "one_at_a_time_sensitivity.csv"
    )
    _write_csv(
        model_result.out_of_fold, paths.artifacts / "data" / "model_out_of_fold_predictions.csv"
    )
    _write_csv(model_result.fold_metrics, paths.artifacts / "data" / "model_fold_metrics.csv")
    _write_csv(optimization.selections, paths.artifacts / "data" / "scenario_selections.csv")
    _write_csv(optimization.summaries, paths.artifacts / "data" / "scenario_summaries.csv")
    _write_csv(optimization.conflicts, paths.artifacts / "data" / "minimum_distance_conflicts.csv")
    save_model(
        model_result.model,
        model_result.metrics,
        paths.artifacts / "models" / "demand_model.joblib",
    )
    _write_json(model_result.metrics, paths.artifacts / "metrics" / "model_metrics.json")
    _write_json(
        {
            "method": "reciprocal AHP matrix derived from approved factor weights",
            "consistency_ratio": score_result.ahp_consistency_ratio,
            "threshold": 0.10,
            "status": "PASS" if score_result.ahp_consistency_ratio < 0.10 else "FAIL",
        },
        paths.artifacts / "metrics" / "ahp_consistency.json",
    )

    create_candidate_map(
        scored_geo,
        datasets["existing_stores"],
        datasets["competitors"],
        optimization.selections,
        paths.artifacts / "maps" / "candidate_portfolio_map.html",
    )
    create_white_space_map(
        grid,
        scored_geo,
        paths.artifacts / "maps" / "white_space_h3_map.html",
    )
    create_isochrone_map(
        scored_geo,
        candidate_isochrones,
        paths.artifacts / "maps" / "network_isochrones_map.html",
    )
    create_scenario_map(
        scored_geo,
        optimization.selections,
        paths.artifacts / "maps" / "scenario_portfolios_map.html",
    )

    candidate_rank_map(
        datasets["footprint"],
        scored_geo,
        datasets["existing_stores"],
        paths.artifacts / "figures" / "candidate_rank_map.png",
    )
    model_validation_figure(
        model_result.out_of_fold,
        paths.artifacts / "figures" / "model_validation.png",
    )
    top_candidate_figure(scored, paths.artifacts / "figures" / "top_candidates.png")
    scenario_figure(
        optimization.summaries,
        paths.artifacts / "figures" / "scenario_comparison.png",
    )
    contribution_figure(
        score_result.contributions,
        scored,
        paths.artifacts / "figures" / "factor_contributions_top5.png",
    )
    white_space_figure(
        grid,
        scored_geo,
        paths.artifacts / "figures" / "white_space_opportunity_map.png",
    )
    isochrone_figure(
        datasets["footprint"],
        candidate_isochrones,
        scored_geo,
        paths.artifacts / "figures" / "network_isochrones.png",
    )
    scenario_portfolio_figure(
        datasets["footprint"],
        scored_geo,
        datasets["existing_stores"],
        optimization.selections,
        paths.artifacts / "figures" / "base_portfolio_map.png",
    )

    runtime_seconds = time.perf_counter() - started
    base_summary = optimization.summaries.set_index("scenario").loc["base"]
    top = scored.nsmallest(1, "location_rank").iloc[0]
    pipeline_summary = {
        "run_status": "SUCCESS",
        "seed": seed,
        "as_of_date": config["project"]["as_of_date"],
        "runtime_seconds": round(runtime_seconds, 3),
        "h3_cells": len(grid),
        "candidate_count": len(scored),
        "existing_store_count": len(datasets["existing_stores"]),
        "competitor_count": len(datasets["competitors"]),
        "poi_count": len(datasets["pois"]),
        "transport_graph_nodes": graph.number_of_nodes(),
        "transport_graph_edges": graph.number_of_edges(),
        "top_candidate_id": str(top["candidate_id"]),
        "top_candidate_name": str(top["candidate_name"]),
        "top_candidate_score": float(top["location_score"]),
        "top_candidate_predicted_sales_try_m": float(top["predicted_sales_try_m"]),
        "base_selected_store_count": int(base_summary["selected_store_count"]),
        "base_budget_used_try_m": float(base_summary["budget_used_try_m"]),
        "base_incremental_covered_population": int(base_summary["incremental_covered_population"]),
        "base_market_coverage_rate": float(base_summary["market_coverage_rate"]),
        "model_metrics": model_result.metrics,
        "quality": quality_summary(quality),
        "ahp_consistency_ratio": score_result.ahp_consistency_ratio,
        "disclaimer": "Synthetic decision-support output; not investment advice.",
    }
    _write_json(pipeline_summary, paths.artifacts / "metrics" / "pipeline_summary.json")
    return pipeline_summary
