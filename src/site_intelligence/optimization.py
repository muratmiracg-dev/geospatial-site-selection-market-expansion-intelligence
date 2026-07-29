"""Scenario-based maximum coverage and constrained portfolio optimization."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import pulp

from site_intelligence.accessibility import Reachability
from site_intelligence.geo import projected_distance_km


@dataclass(frozen=True)
class OptimizationResult:
    selections: pd.DataFrame
    summaries: pd.DataFrame
    conflicts: pd.DataFrame


def optimize_portfolios(
    candidates: pd.DataFrame,
    candidate_geodata,
    existing: pd.DataFrame,
    grid: pd.DataFrame,
    candidate_cache: dict[tuple[str, str, int], Reachability],
    existing_cache: dict[tuple[str, str, int], Reachability],
    scenarios: dict[str, dict[str, float]],
    *,
    minimum_distance_km: float,
    coverage_minutes: int,
) -> OptimizationResult:
    """Solve budgeted incremental population coverage with distance conflicts."""

    candidate_ids = candidates["candidate_id"].astype(str).tolist()
    grid_indexed = grid.set_index("h3_cell")
    total_population = float(grid["population"].sum())
    existing_covered: set[str] = set()
    for store_id in existing["store_id"].astype(str):
        existing_covered.update(existing_cache[(store_id, "drive", coverage_minutes)].cells)

    coverage = {
        candidate_id: set(candidate_cache[(candidate_id, "drive", coverage_minutes)].cells)
        for candidate_id in candidate_ids
    }
    relevant_cells = sorted(set().union(*coverage.values()) - existing_covered)
    covering_candidates = {
        cell: [candidate_id for candidate_id in candidate_ids if cell in coverage[candidate_id]]
        for cell in relevant_cells
    }

    distances = projected_distance_km(candidate_geodata, candidate_geodata)
    conflicts = []
    for left in range(len(candidate_ids)):
        for right in range(left + 1, len(candidate_ids)):
            if distances[left, right] < minimum_distance_km:
                conflicts.append(
                    {
                        "candidate_a": candidate_ids[left],
                        "candidate_b": candidate_ids[right],
                        "distance_km": float(distances[left, right]),
                        "minimum_km": minimum_distance_km,
                    }
                )
    conflict_frame = pd.DataFrame(conflicts)
    indexed_candidates = candidates.set_index("candidate_id")

    selection_rows = []
    summary_rows = []
    for scenario_name, assumptions in scenarios.items():
        problem = pulp.LpProblem(f"market_expansion_{scenario_name}", pulp.LpMaximize)
        select = {
            candidate_id: pulp.LpVariable(f"x_{candidate_id}", cat=pulp.LpBinary)
            for candidate_id in candidate_ids
        }
        covered = {
            cell: pulp.LpVariable(f"y_{cell.replace('-', '_')}", cat=pulp.LpBinary)
            for cell in relevant_cells
        }

        demand_multiplier = float(assumptions["demand_multiplier"])
        cost_multiplier = float(assumptions["cost_multiplier"])
        candidate_value = {}
        for candidate_id in candidate_ids:
            row = indexed_candidates.loc[candidate_id]
            expected_ebit = (
                float(row["predicted_sales_try_m"]) * demand_multiplier * 0.205
                - float(row["annual_opex_try_m"]) * cost_multiplier
            )
            candidate_value[candidate_id] = (
                expected_ebit
                + float(row["location_score"]) * 0.09
                - float(row["cannibalization_risk"]) * 3.0
            )
        coverage_value = {
            cell: float(grid_indexed.loc[cell, "population"]) / 1_000_000.0 * 7.0
            for cell in relevant_cells
        }
        problem += pulp.lpSum(
            candidate_value[candidate_id] * select[candidate_id] for candidate_id in candidate_ids
        ) + pulp.lpSum(coverage_value[cell] * covered[cell] for cell in relevant_cells)
        problem += pulp.lpSum(
            float(indexed_candidates.loc[candidate_id, "opening_cost_try_m"])
            * cost_multiplier
            * select[candidate_id]
            for candidate_id in candidate_ids
        ) <= float(assumptions["budget_try_m"])
        problem += pulp.lpSum(select.values()) <= int(assumptions["max_stores"])
        for conflict in conflicts:
            problem += select[conflict["candidate_a"]] + select[conflict["candidate_b"]] <= 1
        for cell, candidate_list in covering_candidates.items():
            problem += covered[cell] <= pulp.lpSum(
                select[candidate_id] for candidate_id in candidate_list
            )

        solver = pulp.PULP_CBC_CMD(msg=False, threads=1, options=["randomSeed 20260729"])
        status_code = problem.solve(solver)
        status = pulp.LpStatus[status_code]
        selected = [
            candidate_id for candidate_id in candidate_ids if pulp.value(select[candidate_id]) > 0.5
        ]
        selected_coverage = (
            set().union(*(coverage[candidate_id] for candidate_id in selected))
            if selected
            else set()
        )
        total_covered = existing_covered | selected_coverage
        incremental_cells = selected_coverage - existing_covered
        incremental_population = (
            int(grid_indexed.loc[list(incremental_cells), "population"].sum())
            if incremental_cells
            else 0
        )
        budget_used = sum(
            float(indexed_candidates.loc[candidate_id, "opening_cost_try_m"]) * cost_multiplier
            for candidate_id in selected
        )
        scenario_sales = sum(
            float(indexed_candidates.loc[candidate_id, "predicted_sales_try_m"]) * demand_multiplier
            for candidate_id in selected
        )
        scenario_ebit = sum(
            float(indexed_candidates.loc[candidate_id, "predicted_sales_try_m"])
            * demand_multiplier
            * 0.205
            - float(indexed_candidates.loc[candidate_id, "annual_opex_try_m"]) * cost_multiplier
            for candidate_id in selected
        )
        for priority, candidate_id in enumerate(
            sorted(selected, key=lambda item: indexed_candidates.loc[item, "location_rank"]),
            start=1,
        ):
            row = indexed_candidates.loc[candidate_id]
            selection_rows.append(
                {
                    "scenario": scenario_name,
                    "priority": priority,
                    "candidate_id": candidate_id,
                    "candidate_name": row["candidate_name"],
                    "location_rank": int(row["location_rank"]),
                    "location_score": float(row["location_score"]),
                    "scenario_sales_try_m": float(row["predicted_sales_try_m"]) * demand_multiplier,
                    "scenario_opening_cost_try_m": float(row["opening_cost_try_m"])
                    * cost_multiplier,
                    "cannibalization_risk": float(row["cannibalization_risk"]),
                }
            )
        summary_rows.append(
            {
                "scenario": scenario_name,
                "solver_status": status,
                "selected_store_count": len(selected),
                "selected_candidate_ids": ",".join(selected),
                "budget_try_m": float(assumptions["budget_try_m"]),
                "budget_used_try_m": budget_used,
                "budget_utilization": budget_used / float(assumptions["budget_try_m"]),
                "incremental_covered_population": incremental_population,
                "market_coverage_rate": sum(
                    float(grid_indexed.loc[cell, "population"]) for cell in total_covered
                )
                / total_population,
                "portfolio_sales_try_m": scenario_sales,
                "portfolio_expected_ebit_try_m": scenario_ebit,
                "objective_value": float(pulp.value(problem.objective)),
            }
        )
    return OptimizationResult(
        selections=pd.DataFrame(selection_rows),
        summaries=pd.DataFrame(summary_rows),
        conflicts=conflict_frame,
    )
