"""H3-adjacency travel network and 5/10/15-minute service areas."""

from __future__ import annotations

from dataclasses import dataclass

import geopandas as gpd
import h3
import networkx as nx
import numpy as np
import pandas as pd
from shapely.geometry import Point

from site_intelligence.catalog import BRIDGE_CONNECTIONS
from site_intelligence.constants import METRIC_CRS
from site_intelligence.geo import WGS84_TO_METRIC, service_geometry


@dataclass(frozen=True)
class Reachability:
    source_cell: str
    mode: str
    minutes: int
    cells: frozenset[str]
    accessible_population: int
    accessible_demand: float


def _nearest_cell(grid: gpd.GeoDataFrame, latitude: float, longitude: float) -> str:
    dx = (grid["longitude"].to_numpy() - longitude) * 82.0
    dy = (grid["latitude"].to_numpy() - latitude) * 111.0
    index = int(np.argmin(dx * dx + dy * dy))
    return str(grid.iloc[index]["h3_cell"])


def build_transport_graph(
    grid: gpd.GeoDataFrame,
    *,
    drive_speed_kph: float,
    walk_speed_kph: float,
    bridge_penalty_minutes: float,
) -> nx.Graph:
    """Build a deterministic network from H3 adjacency plus explicit Bosphorus links."""

    graph = nx.Graph()
    indexed = grid.set_index("h3_cell", drop=False)
    projected = grid.to_crs(METRIC_CRS).set_index("h3_cell")
    projected_centroids = projected.geometry.centroid
    cells = set(indexed.index)
    for cell, row in indexed.iterrows():
        graph.add_node(
            cell, population=int(row["population"]), demand_weight=float(row["demand_weight"])
        )

    for cell in sorted(cells):
        for neighbor in h3.grid_disk(cell, 1):
            if neighbor not in cells or neighbor <= cell:
                continue
            distance_km = float(
                projected_centroids.loc[cell].distance(projected_centroids.loc[neighbor]) / 1000.0
            )
            road = float(
                (indexed.loc[cell, "road_index"] + indexed.loc[neighbor, "road_index"]) / 2
            )
            congestion = float(
                (indexed.loc[cell, "congestion_index"] + indexed.loc[neighbor, "congestion_index"])
                / 2
            )
            walkability = float(
                (
                    indexed.loc[cell, "walkability_index"]
                    + indexed.loc[neighbor, "walkability_index"]
                )
                / 2
            )
            effective_drive_speed = (
                drive_speed_kph * (0.62 + 0.48 * road) * (1.0 - 0.42 * congestion)
            )
            effective_walk_speed = walk_speed_kph * (0.82 + 0.22 * walkability)
            graph.add_edge(
                cell,
                neighbor,
                distance_km=distance_km,
                drive_minutes=distance_km / max(effective_drive_speed, 8.0) * 60.0,
                walk_minutes=distance_km / max(effective_walk_speed, 3.5) * 60.0,
                edge_type="h3_adjacency",
            )

    for west, east, bridge_name in BRIDGE_CONNECTIONS:
        west_cell = _nearest_cell(grid, west[0], west[1])
        east_cell = _nearest_cell(grid, east[0], east[1])
        if west_cell == east_cell or graph.has_edge(west_cell, east_cell):
            continue
        distance_km = float(
            projected_centroids.loc[west_cell].distance(projected_centroids.loc[east_cell]) / 1000.0
        )
        graph.add_edge(
            west_cell,
            east_cell,
            distance_km=distance_km,
            drive_minutes=distance_km / 42.0 * 60.0 + bridge_penalty_minutes,
            walk_minutes=distance_km / 4.2 * 60.0 + 8.0,
            edge_type=bridge_name,
        )
    return graph


def reachable(
    graph: nx.Graph,
    grid: gpd.GeoDataFrame,
    source_cell: str,
    *,
    mode: str,
    minutes: int,
) -> Reachability:
    """Return cells and population reachable within a network-time cutoff."""

    weight = f"{mode}_minutes"
    lengths = nx.single_source_dijkstra_path_length(
        graph,
        source_cell,
        cutoff=float(minutes),
        weight=weight,
    )
    cells = frozenset(lengths)
    indexed = grid.set_index("h3_cell")
    selected = indexed.loc[list(cells)]
    return Reachability(
        source_cell=source_cell,
        mode=mode,
        minutes=minutes,
        cells=cells,
        accessible_population=int(selected["population"].sum()),
        accessible_demand=float(selected["demand_weight"].sum()),
    )


def calculate_location_reachability(
    locations: gpd.GeoDataFrame,
    grid: gpd.GeoDataFrame,
    graph: nx.Graph,
    *,
    id_column: str,
    thresholds: list[int],
    include_geometries: bool = True,
) -> tuple[pd.DataFrame, gpd.GeoDataFrame, dict[tuple[str, str, int], Reachability]]:
    """Calculate drive/walk reachability for every location and threshold."""

    records: list[dict[str, int | float | str]] = []
    geometry_records: list[dict[str, int | float | str]] = []
    geometries = []
    cache: dict[tuple[str, str, int], Reachability] = {}
    for _, location in locations.iterrows():
        location_id = str(location[id_column])
        source_cell = _nearest_cell(grid, float(location["latitude"]), float(location["longitude"]))
        for mode in ("drive", "walk"):
            for minutes in thresholds:
                result = reachable(graph, grid, source_cell, mode=mode, minutes=minutes)
                cache[(location_id, mode, minutes)] = result
                record = {
                    id_column: location_id,
                    "source_h3_cell": source_cell,
                    "mode": mode,
                    "minutes": minutes,
                    "accessible_population": result.accessible_population,
                    "accessible_demand": round(result.accessible_demand, 3),
                    "reachable_cells": len(result.cells),
                }
                records.append(record)
                if include_geometries:
                    geometry_records.append(record.copy())
                    geometries.append(service_geometry(grid, result.cells))
    geometry_frame = gpd.GeoDataFrame(geometry_records, geometry=geometries, crs=grid.crs)
    return pd.DataFrame(records), geometry_frame, cache


def euclidean_population(
    grid: gpd.GeoDataFrame,
    latitude: float,
    longitude: float,
    radius_km: float,
) -> int:
    """Population inside a projected straight-line radius."""

    projected = grid.to_crs(METRIC_CRS)
    x, y = WGS84_TO_METRIC.transform(longitude, latitude)
    point = Point(x, y)
    mask = projected.geometry.distance(point) <= radius_km * 1000.0
    return int(grid.loc[mask, "population"].sum())
