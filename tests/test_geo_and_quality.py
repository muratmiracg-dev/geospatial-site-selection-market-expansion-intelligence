from __future__ import annotations

import geopandas as gpd
from shapely.geometry import Point

from site_intelligence.data_generation import (
    generate_candidates,
    generate_existing_stores,
    metropolitan_footprint,
)
from site_intelligence.geo import haversine_km, sigmoid
from site_intelligence.quality import quality_summary, validate_geodataframe


def test_deterministic_candidate_generation() -> None:
    first = generate_candidates(20260729)
    second = generate_candidates(20260729)
    assert first.drop(columns="geometry").equals(second.drop(columns="geometry"))
    assert len(first) == 24
    assert first.crs.to_epsg() == 4326


def test_reference_entities_and_footprint() -> None:
    footprint = metropolitan_footprint()
    stores = generate_existing_stores(20260729)
    assert footprint.geometry.is_valid.all()
    assert stores["store_id"].is_unique
    assert stores.geometry.within(footprint.geometry.iloc[0]).all()


def test_geodesic_and_sigmoid_helpers() -> None:
    assert 2.0 < haversine_km(41.0433, 29.0059, 41.0610, 28.9870) < 3.0
    assert sigmoid(0) == 0.5
    assert sigmoid(100) > 0.999
    assert sigmoid(-100) < 0.001


def test_quality_check_detects_duplicate_geometry() -> None:
    frame = gpd.GeoDataFrame(
        {"id": ["A", "B"], "value": [1, 2]},
        geometry=[Point(29.0, 41.0), Point(29.0, 41.0)],
        crs="EPSG:4326",
    )
    checks = validate_geodataframe("sample", frame, id_column="id")
    duplicate = next(check for check in checks if check.check == "duplicate_geometry")
    assert duplicate.status == "WARN"
    summary = quality_summary(__import__("pandas").DataFrame([check.__dict__ for check in checks]))
    assert summary["critical_failures"] == 0
