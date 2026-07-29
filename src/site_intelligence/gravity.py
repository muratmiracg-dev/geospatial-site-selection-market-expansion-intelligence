"""Huff/gravity customer-share and diversion estimates."""

from __future__ import annotations

import networkx as nx
import numpy as np
import pandas as pd

from site_intelligence.accessibility import Reachability


def _travel_times(graph: nx.Graph, source_cell: str, cutoff: float = 35.0) -> dict[str, float]:
    return nx.single_source_dijkstra_path_length(
        graph,
        source_cell,
        cutoff=cutoff,
        weight="drive_minutes",
    )


def candidate_huff_metrics(
    candidates: pd.DataFrame,
    existing: pd.DataFrame,
    grid: pd.DataFrame,
    graph: nx.Graph,
    candidate_cache: dict[tuple[str, str, int], Reachability],
    existing_cache: dict[tuple[str, str, int], Reachability],
    *,
    distance_decay: float = 1.65,
) -> pd.DataFrame:
    """Estimate candidate capture and incumbent diversion one candidate at a time."""

    cells = grid["h3_cell"].astype(str).tolist()
    demand = grid.set_index("h3_cell")["demand_weight"].astype(float)
    baseline_utility = pd.Series(0.0, index=cells)
    for _, store in existing.iterrows():
        store_id = str(store["store_id"])
        source = existing_cache[(store_id, "drive", 10)].source_cell
        times = _travel_times(graph, source)
        attractiveness = float(store["store_area_sqm"]) * (
            0.75 + float(store.get("ebit_margin", 0.10)) * 2.0
        )
        for cell, minutes in times.items():
            baseline_utility.loc[cell] += attractiveness / (minutes + 2.0) ** distance_decay

    rows = []
    for _, candidate in candidates.iterrows():
        candidate_id = str(candidate["candidate_id"])
        source = candidate_cache[(candidate_id, "drive", 10)].source_cell
        times = _travel_times(graph, source)
        attractiveness = float(candidate["store_area_sqm"]) * (
            0.60
            + 0.30 * float(candidate["commercial_index"])
            + 0.10 * float(candidate["capacity_index"])
        )
        utility = pd.Series(0.0, index=cells)
        for cell, minutes in times.items():
            utility.loc[cell] = attractiveness / (minutes + 2.0) ** distance_decay
        denominator = baseline_utility + utility
        share = utility.divide(denominator.where(denominator > 0, np.nan)).fillna(0.0)
        captured_demand = float((share * demand).sum())
        existing_served = baseline_utility > 0
        diverted_demand = float((share.loc[existing_served] * demand.loc[existing_served]).sum())
        rows.append(
            {
                "candidate_id": candidate_id,
                "huff_capture_demand": captured_demand,
                "huff_diverted_demand": diverted_demand,
                "huff_diversion_ratio": diverted_demand / max(captured_demand, 1.0),
                "distance_decay": distance_decay,
            }
        )
    return pd.DataFrame(rows)
