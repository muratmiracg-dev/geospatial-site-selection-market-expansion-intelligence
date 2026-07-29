"""Fail-fast data and geometry quality gates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import geopandas as gpd
import pandas as pd

from site_intelligence.constants import STORAGE_CRS


@dataclass(frozen=True)
class QualityCheck:
    dataset: str
    check: str
    status: str
    observed: int | float | str
    threshold: int | float | str
    severity: str


def validate_geodataframe(
    name: str,
    frame: gpd.GeoDataFrame,
    *,
    id_column: str | None = None,
) -> list[QualityCheck]:
    """Run core geometry, coordinate, duplicate, missing, and CRS checks."""

    checks: list[QualityCheck] = []
    missing = int(frame.drop(columns="geometry").isna().sum().sum())
    checks.append(
        QualityCheck(
            name, "missing_values", "PASS" if missing == 0 else "FAIL", missing, 0, "critical"
        )
    )

    empty = int(frame.geometry.is_empty.sum())
    checks.append(
        QualityCheck(name, "empty_geometry", "PASS" if empty == 0 else "FAIL", empty, 0, "critical")
    )

    invalid = int((~frame.geometry.is_valid).sum())
    checks.append(
        QualityCheck(
            name, "invalid_geometry", "PASS" if invalid == 0 else "FAIL", invalid, 0, "critical"
        )
    )

    expected_crs = str(gpd.GeoSeries([], crs=STORAGE_CRS).crs)
    observed_crs = str(frame.crs)
    checks.append(
        QualityCheck(
            name,
            "crs_is_wgs84",
            "PASS" if observed_crs == expected_crs else "FAIL",
            observed_crs,
            expected_crs,
            "critical",
        )
    )

    bounds = frame.total_bounds
    coordinate_ok = bool(
        -180 <= bounds[0] <= 180
        and -90 <= bounds[1] <= 90
        and -180 <= bounds[2] <= 180
        and -90 <= bounds[3] <= 90
    )
    checks.append(
        QualityCheck(
            name,
            "coordinate_range",
            "PASS" if coordinate_ok else "FAIL",
            ",".join(f"{value:.4f}" for value in bounds),
            "valid_lon_lat",
            "critical",
        )
    )

    duplicate_geometry = int(frame.geometry.to_wkb().duplicated().sum())
    checks.append(
        QualityCheck(
            name,
            "duplicate_geometry",
            "PASS" if duplicate_geometry == 0 else "WARN",
            duplicate_geometry,
            0,
            "warning",
        )
    )
    if id_column:
        duplicate_id = int(frame[id_column].duplicated().sum())
        checks.append(
            QualityCheck(
                name,
                "duplicate_identifier",
                "PASS" if duplicate_id == 0 else "FAIL",
                duplicate_id,
                0,
                "critical",
            )
        )
    return checks


def validate_spatial_coverage(
    name: str,
    points: gpd.GeoDataFrame,
    grid: gpd.GeoDataFrame,
) -> QualityCheck:
    """Ensure every point can be assigned to an H3 microzone."""

    joined = gpd.sjoin(points, grid[["h3_cell", "geometry"]], how="left", predicate="within")
    unmatched = int(joined["h3_cell"].isna().sum())
    return QualityCheck(
        name,
        "spatial_join_unmatched",
        "PASS" if unmatched == 0 else "WARN",
        unmatched,
        0,
        "warning",
    )


def run_quality_suite(datasets: dict[str, gpd.GeoDataFrame]) -> pd.DataFrame:
    """Run all quality checks and raise when critical gates fail."""

    id_columns = {
        "grid": "h3_cell",
        "candidates": "candidate_id",
        "existing_stores": "store_id",
        "competitors": "competitor_id",
        "pois": "poi_id",
        "footprint": "area_id",
    }
    checks: list[QualityCheck] = []
    for name, frame in datasets.items():
        checks.extend(validate_geodataframe(name, frame, id_column=id_columns.get(name)))
    for name in ("candidates", "existing_stores", "competitors", "pois"):
        checks.append(validate_spatial_coverage(name, datasets[name], datasets["grid"]))
    frame = pd.DataFrame([asdict(check) for check in checks])
    critical_failures = frame[(frame["severity"] == "critical") & (frame["status"] == "FAIL")]
    if not critical_failures.empty:
        raise ValueError(
            f"Critical data-quality failures: {critical_failures.to_dict(orient='records')}"
        )
    return frame


def quality_summary(frame: pd.DataFrame) -> dict[str, Any]:
    """Summarize quality statuses for reports and API health."""

    return {
        "checks": len(frame),
        "passed": int((frame["status"] == "PASS").sum()),
        "warnings": int((frame["status"] == "WARN").sum()),
        "failed": int((frame["status"] == "FAIL").sum()),
        "critical_failures": int(
            ((frame["status"] == "FAIL") & (frame["severity"] == "critical")).sum()
        ),
    }
