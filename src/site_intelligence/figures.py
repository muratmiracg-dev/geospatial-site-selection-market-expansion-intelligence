"""Static analytical figures for reports and quality review."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch

COLORS = {
    "navy": "#0B3954",
    "teal": "#2A9D8F",
    "orange": "#F4A261",
    "red": "#E76F51",
    "cream": "#F7F3E9",
}


def _save(path: str | Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close()


def candidate_rank_map(
    footprint: gpd.GeoDataFrame,
    candidates: gpd.GeoDataFrame,
    existing: gpd.GeoDataFrame,
    output_path: str | Path,
) -> None:
    """Render a clean, tile-free location ranking map."""

    fig, axis = plt.subplots(figsize=(12, 7))
    footprint.to_crs("EPSG:32635").plot(
        ax=axis, color="#EAF2F3", edgecolor="#A9C1C7", linewidth=0.8
    )
    projected_candidates = candidates.to_crs("EPSG:32635")
    projected_existing = existing.to_crs("EPSG:32635")
    points = axis.scatter(
        projected_candidates.geometry.x,
        projected_candidates.geometry.y,
        c=projected_candidates["location_score"],
        cmap="viridis",
        s=np.where(projected_candidates["location_rank"] <= 5, 120, 52),
        edgecolor="white",
        linewidth=0.8,
        zorder=4,
    )
    axis.scatter(
        projected_existing.geometry.x,
        projected_existing.geometry.y,
        marker="s",
        color=COLORS["navy"],
        s=55,
        label="Existing store",
        zorder=5,
    )
    for _, row in projected_candidates.nsmallest(8, "location_rank").iterrows():
        axis.annotate(
            f"#{int(row['location_rank'])} {row['candidate_id']}",
            (row.geometry.x, row.geometry.y),
            xytext=(4, 5),
            textcoords="offset points",
            fontsize=8,
            color=COLORS["navy"],
        )
    plt.colorbar(points, ax=axis, shrink=0.72, label="Location score")
    axis.legend(loc="lower left", frameon=False)
    axis.set_title(
        "Candidate location ranking - Istanbul analytical footprint", loc="left", weight="bold"
    )
    axis.set_axis_off()
    _save(output_path)


def model_validation_figure(out_of_fold: pd.DataFrame, output_path: str | Path) -> None:
    """Render actual-vs-predicted and residual diagnostics."""

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    actual = out_of_fold["annual_sales_try_m"]
    predicted = out_of_fold["predicted_sales_try_m"]
    sns.scatterplot(x=actual, y=predicted, ax=axes[0], color=COLORS["teal"], s=38, alpha=0.72)
    low = min(actual.min(), predicted.min())
    high = max(actual.max(), predicted.max())
    axes[0].plot([low, high], [low, high], linestyle="--", color=COLORS["red"], linewidth=1.2)
    axes[0].set_title("Spatial block CV: actual vs predicted", loc="left", weight="bold")
    axes[0].set_xlabel("Actual annual sales (TRY m)")
    axes[0].set_ylabel("Out-of-fold prediction (TRY m)")
    sns.scatterplot(
        x=predicted,
        y=out_of_fold["residual_try_m"],
        ax=axes[1],
        color=COLORS["orange"],
        s=38,
        alpha=0.72,
    )
    axes[1].axhline(0, linestyle="--", color=COLORS["navy"], linewidth=1.1)
    axes[1].set_title("Residual stability", loc="left", weight="bold")
    axes[1].set_xlabel("Predicted annual sales (TRY m)")
    axes[1].set_ylabel("Residual (TRY m)")
    _save(output_path)


def top_candidate_figure(candidates: pd.DataFrame, output_path: str | Path) -> None:
    """Render top-ten scores and uncertainty intervals."""

    top = candidates.nsmallest(10, "location_rank").sort_values("location_score")
    fig, axis = plt.subplots(figsize=(10, 6))
    axis.barh(top["candidate_name"], top["location_score"], color=COLORS["teal"])
    for index, (_, row) in enumerate(top.iterrows()):
        axis.text(
            row["location_score"] + 0.6,
            index,
            f"{row['location_score']:.1f}",
            va="center",
            fontsize=9,
        )
    axis.set_xlim(0, 105)
    axis.set_xlabel("Auditable location score (0-100)")
    axis.set_title("Prioritized candidate locations", loc="left", weight="bold")
    axis.spines[["top", "right", "left"]].set_visible(False)
    _save(output_path)


def scenario_figure(summaries: pd.DataFrame, output_path: str | Path) -> None:
    """Render scenario budget and impact comparisons."""

    frame = summaries.copy()
    frame["scenario"] = pd.Categorical(
        frame["scenario"],
        categories=["pessimistic", "base", "optimistic"],
        ordered=True,
    )
    frame = frame.sort_values("scenario")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].bar(frame["scenario"].astype(str), frame["budget_used_try_m"], color=COLORS["navy"])
    axes[0].plot(
        frame["scenario"].astype(str),
        frame["budget_try_m"],
        marker="o",
        color=COLORS["orange"],
        label="Budget",
    )
    axes[0].set_ylabel("TRY million")
    axes[0].set_title("Investment envelope", loc="left", weight="bold")
    axes[0].legend(frameon=False)
    axes[1].bar(
        frame["scenario"].astype(str),
        frame["incremental_covered_population"] / 1_000_000,
        color=COLORS["teal"],
    )
    axes[1].set_ylabel("Incremental population (millions)")
    axes[1].set_title("Incremental network coverage", loc="left", weight="bold")
    _save(output_path)


def contribution_figure(
    contributions: pd.DataFrame,
    candidates: pd.DataFrame,
    output_path: str | Path,
) -> None:
    """Render factor contribution mix for the top-five candidates."""

    top_ids = candidates.nsmallest(5, "location_rank")["candidate_id"].tolist()
    pivot = (
        contributions[contributions["candidate_id"].isin(top_ids)]
        .pivot(index="candidate_id", columns="factor", values="score_contribution")
        .loc[top_ids]
    )
    figure = pivot.plot(
        kind="barh", stacked=True, figsize=(12, 6), colormap="Spectral"
    ).get_figure()
    axis = figure.axes[0]
    axis.set_xlabel("Score contribution")
    axis.set_ylabel("Candidate")
    axis.set_title("Why the top candidates score highly", loc="left", weight="bold")
    axis.legend(title="Factor", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
    _save(output_path)


def white_space_figure(
    grid: gpd.GeoDataFrame,
    candidates: gpd.GeoDataFrame,
    output_path: str | Path,
) -> None:
    """Render the H3 white-space surface and leading candidates."""

    fig, axis = plt.subplots(figsize=(12, 7))
    projected_grid = grid.to_crs("EPSG:32635")
    projected_candidates = candidates.to_crs("EPSG:32635")
    projected_grid.plot(
        ax=axis,
        column="white_space_index",
        cmap="YlGnBu",
        linewidth=0,
        legend=True,
        legend_kwds={"label": "White-space opportunity index", "shrink": 0.72},
    )
    top = projected_candidates.nsmallest(8, "location_rank")
    axis.scatter(
        top.geometry.x,
        top.geometry.y,
        color=COLORS["red"],
        edgecolor="white",
        linewidth=0.9,
        s=72,
        zorder=5,
    )
    for _, row in top.iterrows():
        axis.annotate(
            f"{row['candidate_id']}",
            (row.geometry.x, row.geometry.y),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=8,
            color=COLORS["navy"],
        )
    axis.set_title("White-space opportunity across H3 microzones", loc="left", weight="bold")
    axis.set_axis_off()
    _save(output_path)


def isochrone_figure(
    footprint: gpd.GeoDataFrame,
    isochrones: gpd.GeoDataFrame,
    candidates: gpd.GeoDataFrame,
    output_path: str | Path,
) -> None:
    """Render drive-time isochrones for the top three candidates."""

    top_ids = candidates.nsmallest(3, "location_rank")["candidate_id"].astype(str)
    subset = isochrones[
        (isochrones["candidate_id"].isin(top_ids)) & (isochrones["mode"] == "drive")
    ].copy()
    fig, axis = plt.subplots(figsize=(12, 7))
    footprint.to_crs("EPSG:32635").plot(
        ax=axis,
        color="#EEF4F4",
        edgecolor="#A9C1C7",
        linewidth=0.7,
    )
    color_by_minutes = {15: "#E76F51", 10: "#F4A261", 5: "#2A9D8F"}
    for minutes in (15, 10, 5):
        subset[subset["minutes"] == minutes].to_crs("EPSG:32635").plot(
            ax=axis,
            color=color_by_minutes[minutes],
            edgecolor="white",
            linewidth=0.5,
            alpha=0.30,
            label=f"{minutes} min",
        )
    top = candidates[candidates["candidate_id"].isin(top_ids)].to_crs("EPSG:32635")
    axis.scatter(
        top.geometry.x,
        top.geometry.y,
        color=COLORS["navy"],
        edgecolor="white",
        s=85,
        zorder=5,
    )
    for _, row in top.iterrows():
        axis.annotate(
            f"{row['candidate_id']}",
            (row.geometry.x, row.geometry.y),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=9,
            weight="bold",
        )
    axis.legend(
        handles=[
            Patch(facecolor=color_by_minutes[minutes], alpha=0.30, label=f"{minutes} min")
            for minutes in (5, 10, 15)
        ],
        loc="lower left",
        frameon=False,
        title="Drive-time band",
    )
    axis.set_title("Network-time catchments reveal non-circular reach", loc="left", weight="bold")
    axis.set_axis_off()
    _save(output_path)


def scenario_portfolio_figure(
    footprint: gpd.GeoDataFrame,
    candidates: gpd.GeoDataFrame,
    existing: gpd.GeoDataFrame,
    selections: pd.DataFrame,
    output_path: str | Path,
) -> None:
    """Render the optimized base portfolio against the existing estate."""

    base_ids = set(selections.loc[selections["scenario"] == "base", "candidate_id"])
    fig, axis = plt.subplots(figsize=(12, 7))
    footprint.to_crs("EPSG:32635").plot(
        ax=axis,
        color="#EEF4F4",
        edgecolor="#A9C1C7",
        linewidth=0.7,
    )
    projected_existing = existing.to_crs("EPSG:32635")
    projected_candidates = candidates.to_crs("EPSG:32635")
    base = projected_candidates[projected_candidates["candidate_id"].isin(base_ids)]
    axis.scatter(
        projected_existing.geometry.x,
        projected_existing.geometry.y,
        marker="s",
        color=COLORS["navy"],
        edgecolor="white",
        s=62,
        label="Existing",
    )
    axis.scatter(
        base.geometry.x,
        base.geometry.y,
        marker="o",
        color=COLORS["teal"],
        edgecolor="white",
        linewidth=1.2,
        s=120,
        label="Base scenario recommendation",
        zorder=5,
    )
    for _, row in base.iterrows():
        axis.annotate(
            f"{row['candidate_id']}",
            (row.geometry.x, row.geometry.y),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=9,
            weight="bold",
        )
    axis.legend(loc="lower left", frameon=False)
    axis.set_title("Base scenario adds four complementary locations", loc="left", weight="bold")
    axis.set_axis_off()
    _save(output_path)
