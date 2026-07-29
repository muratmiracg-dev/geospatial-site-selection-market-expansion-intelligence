"""Spatial joins, local densities, accessibility, costs, and cannibalization."""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd

from site_intelligence.accessibility import (
    Reachability,
    euclidean_population,
)
from site_intelligence.constants import METRIC_CRS
from site_intelligence.geo import projected_distance_km


def attach_grid_attributes(
    locations: gpd.GeoDataFrame,
    grid: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Assign every point to a microzone, falling back to nearest cell."""

    attributes = [
        "h3_cell",
        "income_index",
        "purchasing_power_index",
        "commercial_index",
        "transit_index",
        "walkability_index",
        "road_index",
        "congestion_index",
        "rent_try_sqm_month",
        "population",
    ]
    joined = gpd.sjoin(
        locations,
        grid[[*attributes, "geometry"]],
        how="left",
        predicate="within",
    ).drop(columns=["index_right"])
    missing = joined["h3_cell"].isna()
    if missing.any():
        grid_projected = grid.to_crs(METRIC_CRS)
        location_projected = locations.to_crs(METRIC_CRS)
        for index in joined.index[missing]:
            nearest = int(
                grid_projected.distance(location_projected.loc[index, "geometry"]).idxmin()
            )
            for column in attributes:
                joined.loc[index, column] = grid.loc[nearest, column]
    return joined


def _density_count(
    locations: gpd.GeoDataFrame,
    points: gpd.GeoDataFrame,
    radius_m: float,
) -> np.ndarray:
    location_projected = locations.to_crs(METRIC_CRS)
    point_projected = points.to_crs(METRIC_CRS)
    counts = []
    spatial_index = point_projected.sindex
    for geometry in location_projected.geometry:
        candidates = list(spatial_index.query(geometry.buffer(radius_m), predicate="intersects"))
        if not candidates:
            counts.append(0)
            continue
        subset = point_projected.iloc[candidates]
        counts.append(int((subset.geometry.distance(geometry) <= radius_m).sum()))
    return np.asarray(counts, dtype=int)


def add_point_densities(
    locations: gpd.GeoDataFrame,
    competitors: gpd.GeoDataFrame,
    pois: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Add projected local competitor and POI density counts."""

    result = locations.copy()
    result["competitor_density_3km"] = _density_count(result, competitors, 3000.0)
    result["poi_density_2km"] = _density_count(result, pois, 2000.0)
    return result


def pivot_reachability(
    reachability: pd.DataFrame,
    *,
    id_column: str,
) -> pd.DataFrame:
    """Pivot long network-service metrics into auditable feature columns."""

    result = reachability.pivot_table(
        index=id_column,
        columns=["mode", "minutes"],
        values="accessible_population",
        aggfunc="first",
    )
    result.columns = [f"accessible_pop_{mode}_{minutes}" for mode, minutes in result.columns]
    return result.reset_index()


def enrich_candidates(
    candidates: gpd.GeoDataFrame,
    existing: gpd.GeoDataFrame,
    competitors: gpd.GeoDataFrame,
    pois: gpd.GeoDataFrame,
    grid: gpd.GeoDataFrame,
    candidate_reachability: pd.DataFrame,
    candidate_cache: dict[tuple[str, str, int], Reachability],
    existing_cache: dict[tuple[str, str, int], Reachability],
    *,
    drive_speed_kph: float,
) -> gpd.GeoDataFrame:
    """Create the full candidate feature table and transparent investment assumptions."""

    result = attach_grid_attributes(candidates, grid)
    result = add_point_densities(result, competitors, pois)
    reach_pivot = pivot_reachability(candidate_reachability, id_column="candidate_id")
    result = result.merge(reach_pivot, on="candidate_id", how="left")

    existing_union: set[str] = set()
    for store_id in existing["store_id"]:
        existing_union.update(existing_cache[(str(store_id), "drive", 10)].cells)
    indexed_grid = grid.set_index("h3_cell")

    overlap_ratios: list[float] = []
    nearest_distances: list[float] = []
    network_gap_ratios: list[float] = []
    distance_matrix = projected_distance_km(result, existing)
    for row_index, candidate in result.iterrows():
        candidate_id = str(candidate["candidate_id"])
        reach = candidate_cache[(candidate_id, "drive", 10)]
        overlap = set(reach.cells).intersection(existing_union)
        overlap_population = (
            int(indexed_grid.loc[list(overlap), "population"].sum()) if overlap else 0
        )
        overlap_ratio = overlap_population / max(reach.accessible_population, 1)
        nearest_km = float(distance_matrix[row_index].min())
        overlap_ratios.append(
            float(np.clip(0.72 * overlap_ratio + 0.28 * np.exp(-nearest_km / 3.8), 0, 1))
        )
        nearest_distances.append(nearest_km)

        euclidean_radius = drive_speed_kph * (10.0 / 60.0)
        euclidean_pop = euclidean_population(
            grid,
            float(candidate["latitude"]),
            float(candidate["longitude"]),
            euclidean_radius,
        )
        gap = (euclidean_pop - reach.accessible_population) / max(euclidean_pop, 1)
        network_gap_ratios.append(float(gap))

    result["cannibalization_risk"] = np.round(overlap_ratios, 6)
    result["nearest_existing_store_km"] = np.round(nearest_distances, 3)
    result["euclidean_vs_network_population_gap"] = np.round(network_gap_ratios, 6)

    result["monthly_rent_try"] = np.round(
        result["rent_try_sqm_month"] * result["store_area_sqm"], 2
    )
    result["opening_cost_try_m"] = np.round(
        (
            7_500_000
            + result["store_area_sqm"] * 17_500
            + result["monthly_rent_try"] * 4
            + result["permitting_months"] * 115_000
        )
        / 1_000_000,
        3,
    )
    result["annual_opex_try_m"] = np.round(
        (result["monthly_rent_try"] * 12 + result["store_area_sqm"] * 18_000 + 5_200_000)
        / 1_000_000,
        3,
    )
    return result


def build_benchmark_sites(
    grid: gpd.GeoDataFrame,
    graph,
    competitors: gpd.GeoDataFrame,
    pois: gpd.GeoDataFrame,
    existing: gpd.GeoDataFrame,
    *,
    count: int,
    seed: int,
) -> pd.DataFrame:
    """Create deterministic synthetic benchmark sites with network-derived features."""

    from site_intelligence.accessibility import reachable

    rng = np.random.default_rng(seed + 101)
    probabilities = grid["demand_weight"].to_numpy(dtype=float)
    probabilities = probabilities / probabilities.sum()
    sampled_indices = rng.choice(len(grid), size=count, replace=False, p=probabilities)
    sampled = grid.iloc[sampled_indices].copy().reset_index(drop=True)
    sampled["benchmark_id"] = [f"B{index + 1:04d}" for index in range(count)]
    sampled["store_area_sqm"] = rng.integers(480, 821, size=count)
    sampled = add_point_densities(sampled, competitors, pois)

    existing_distance = projected_distance_km(sampled, existing).min(axis=1)
    accessible_population = []
    cannibalization = []
    for _, row in sampled.iterrows():
        access = reachable(graph, grid, str(row["h3_cell"]), mode="drive", minutes=10)
        accessible_population.append(access.accessible_population)
    cannibalization = np.clip(np.exp(-existing_distance / 4.0) * 0.78, 0.02, 0.95)
    sampled["accessible_pop_drive_10"] = accessible_population
    sampled["cannibalization_risk"] = cannibalization

    block_noise: dict[tuple[int, int], float] = {}
    projected = sampled.to_crs(METRIC_CRS)
    projected_centroids = projected.geometry.centroid
    for geometry in projected_centroids:
        block = (int(geometry.x // 12_000), int(geometry.y // 12_000))
        block_noise.setdefault(block, float(rng.normal(0, 3.8)))
    sampled["spatial_block"] = [
        f"{int(geometry.x // 12_000)}_{int(geometry.y // 12_000)}"
        for geometry in projected_centroids
    ]
    local_noise = rng.normal(0, 4.0, size=count)
    spatial_noise = np.array(
        [
            block_noise[(int(geometry.x // 12_000), int(geometry.y // 12_000))]
            for geometry in projected_centroids
        ]
    )
    sales = (
        24.0
        + 0.00031 * sampled["accessible_pop_drive_10"]
        + 0.26 * sampled["income_index"]
        + 19.5 * sampled["commercial_index"]
        + 10.0 * sampled["transit_index"]
        + 2.9 * np.log1p(sampled["poi_density_2km"])
        - 2.0 * sampled["competitor_density_3km"]
        - 0.0050 * sampled["rent_try_sqm_month"]
        - 20.0 * sampled["cannibalization_risk"]
        + 2.2 * np.sin(sampled["longitude"] * 14.0)
        + spatial_noise
        + local_noise
    )
    sampled["annual_sales_try_m"] = np.round(np.clip(sales, 35.0, 185.0), 3)
    return pd.DataFrame(sampled.drop(columns="geometry"))
