"""Deterministic synthetic commercial data on a real-world coordinate frame."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Polygon
from shapely.ops import unary_union

from site_intelligence.catalog import CANDIDATE_LOCATIONS, DISTRICT_ANCHORS, EXISTING_STORES
from site_intelligence.constants import STORAGE_CRS
from site_intelligence.geo import h3_cell_polygon, h3_polygon_cells


def metropolitan_footprint() -> gpd.GeoDataFrame:
    """Create a transparent analytical footprint, not an administrative boundary."""

    european_core = Polygon(
        [
            (28.53, 40.84),
            (28.98, 40.84),
            (29.075, 40.94),
            (29.075, 41.31),
            (28.83, 41.38),
            (28.56, 41.27),
            (28.53, 40.84),
        ]
    )
    western_corridor = Polygon(
        [
            (28.18, 40.94),
            (28.62, 40.91),
            (28.67, 41.15),
            (28.22, 41.20),
            (28.18, 40.94),
        ]
    )
    asian_core = Polygon(
        [
            (29.105, 40.79),
            (29.48, 40.79),
            (29.54, 41.09),
            (29.35, 41.30),
            (29.12, 41.20),
            (29.105, 40.79),
        ]
    )
    geometry = unary_union([european_core, western_corridor, asian_core])
    return gpd.GeoDataFrame(
        [{"area_id": "IST_METRO_SYNTHETIC", "boundary_type": "analytical_footprint"}],
        geometry=[geometry],
        crs=STORAGE_CRS,
    )


def _stable_noise(key: str, scale: float = 1.0) -> float:
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    unit = int.from_bytes(digest[:8], "big") / float(2**64 - 1)
    return (unit * 2.0 - 1.0) * scale


def _anchor_surfaces(latitude: float, longitude: float) -> tuple[float, float, float, float]:
    density = 0.0
    income = 0.0
    commercial = 0.0
    transit = 0.0
    weight_sum = 0.0
    for (
        _,
        anchor_lat,
        anchor_lon,
        anchor_density,
        anchor_income,
        anchor_transit,
    ) in DISTRICT_ANCHORS:
        dx = (longitude - anchor_lon) * 82.0
        dy = (latitude - anchor_lat) * 111.0
        distance_sq = dx * dx + dy * dy
        weight = np.exp(-distance_sq / (2.0 * 7.5**2))
        density += weight * anchor_density
        income += weight * anchor_income
        commercial += weight * (0.55 * anchor_density + 0.45 * anchor_transit)
        transit += weight * anchor_transit
        weight_sum += weight
    if weight_sum == 0:
        return 0.03, 0.4, 0.15, 0.15
    density_surface = min(1.0, density / 1.65)
    return (
        density_surface,
        income / weight_sum,
        commercial / weight_sum,
        transit / weight_sum,
    )


def generate_h3_grid(resolution: int = 8) -> gpd.GeoDataFrame:
    """Generate Istanbul H3 microzones with deterministic synthetic attributes."""

    footprint = metropolitan_footprint()
    cells: set[str] = set()
    for geometry in footprint.geometry.iloc[0].geoms:
        cells.update(h3_polygon_cells(geometry, resolution))

    rows: list[dict[str, float | int | str]] = []
    geometries: list[Polygon] = []
    raw_population: list[float] = []
    for cell in sorted(cells):
        polygon = h3_cell_polygon(cell)
        centroid = polygon.centroid
        latitude = float(centroid.y)
        longitude = float(centroid.x)
        density, income, commercial, transit = _anchor_surfaces(latitude, longitude)
        noise = _stable_noise(cell, 1.0)
        raw_pop = 500.0 + 19_000.0 * density**1.35 + 1_200.0 * max(noise, -0.35)
        raw_population.append(max(raw_pop, 250.0))
        walkability = np.clip(0.28 + 0.50 * density + 0.18 * transit + noise * 0.04, 0.10, 1.0)
        road_index = np.clip(0.40 + 0.34 * transit + 0.18 * commercial - noise * 0.03, 0.20, 1.0)
        congestion = np.clip(0.25 + 0.60 * density + 0.08 * commercial + noise * 0.04, 0.15, 0.96)
        rent = 350 + 1_350 * commercial + 800 * income + 120 * noise
        rows.append(
            {
                "h3_cell": cell,
                "latitude": latitude,
                "longitude": longitude,
                "density_index": round(float(density), 6),
                "income_index": round(float(np.clip(55 + 95 * income + noise * 4, 45, 165)), 3),
                "purchasing_power_index": round(
                    float(np.clip(50 + 75 * income + 30 * commercial + noise * 3, 40, 175)), 3
                ),
                "commercial_index": round(float(np.clip(commercial + noise * 0.03, 0, 1)), 6),
                "transit_index": round(float(np.clip(transit + noise * 0.03, 0, 1)), 6),
                "walkability_index": round(float(walkability), 6),
                "road_index": round(float(road_index), 6),
                "congestion_index": round(float(congestion), 6),
                "rent_try_sqm_month": round(float(np.clip(rent, 400, 2800)), 2),
                "demand_weight": 0.0,
            }
        )
        geometries.append(polygon)

    target_population = 15_700_000
    scale = target_population / sum(raw_population)
    for row, population in zip(rows, raw_population, strict=True):
        scaled = round(population * scale)
        row["population"] = scaled
        row["households"] = round(scaled / 3.15)
        row["demand_weight"] = round(
            scaled
            * (0.55 + float(row["purchasing_power_index"]) / 200.0)
            * (0.65 + 0.35 * float(row["commercial_index"])),
            3,
        )

    return gpd.GeoDataFrame(rows, geometry=geometries, crs=STORAGE_CRS)


def _point_frame(
    rows: Sequence[tuple],
    columns: list[str],
) -> gpd.GeoDataFrame:
    frame = pd.DataFrame(rows, columns=columns)
    return gpd.GeoDataFrame(
        frame,
        geometry=gpd.points_from_xy(frame["longitude"], frame["latitude"]),
        crs=STORAGE_CRS,
    )


def generate_candidates(seed: int) -> gpd.GeoDataFrame:
    """Create auditable candidate-site assumptions and investment inputs."""

    frame = _point_frame(
        CANDIDATE_LOCATIONS,
        ["candidate_id", "candidate_name", "latitude", "longitude"],
    )
    rng = np.random.default_rng(seed + 11)
    frame["store_area_sqm"] = rng.integers(520, 781, size=len(frame))
    frame["delivery_risk"] = np.round(rng.uniform(0.10, 0.42, size=len(frame)), 4)
    frame["permitting_months"] = rng.integers(4, 11, size=len(frame))
    frame["capacity_index"] = np.round(rng.uniform(0.75, 1.20, size=len(frame)), 4)
    return frame


def generate_existing_stores(seed: int) -> gpd.GeoDataFrame:
    """Create deterministic existing-store locations and operating facts."""

    frame = _point_frame(
        EXISTING_STORES,
        ["store_id", "store_name", "latitude", "longitude", "store_area_sqm"],
    )
    rng = np.random.default_rng(seed + 23)
    frame["opened_year"] = rng.integers(2012, 2023, size=len(frame))
    frame["annual_sales_try_m"] = np.round(rng.uniform(82, 142, size=len(frame)), 3)
    frame["ebit_margin"] = np.round(rng.uniform(0.075, 0.145, size=len(frame)), 4)
    return frame


def generate_competitors(seed: int, count: int = 96) -> gpd.GeoDataFrame:
    """Generate synthetic competitor sites clustered around commercial anchors."""

    rng = np.random.default_rng(seed + 37)
    anchor_weights = np.array([row[3] for row in DISTRICT_ANCHORS], dtype=float)
    anchor_weights /= anchor_weights.sum()
    rows: list[tuple[str, str, str, float, float, int]] = []
    for index in range(count):
        anchor_idx = int(rng.choice(len(DISTRICT_ANCHORS), p=anchor_weights))
        district, latitude, longitude, *_ = DISTRICT_ANCHORS[anchor_idx]
        lat = latitude + float(rng.normal(0, 0.018))
        lon = longitude + float(rng.normal(0, 0.024))
        rows.append(
            (
                f"R{index + 1:03d}",
                f"Competitor {index + 1:03d}",
                district,
                lat,
                lon,
                int(rng.integers(350, 1101)),
            )
        )
    return _point_frame(
        rows,
        [
            "competitor_id",
            "competitor_name",
            "anchor_district",
            "latitude",
            "longitude",
            "area_sqm",
        ],
    )


def generate_pois(seed: int, count: int = 720) -> gpd.GeoDataFrame:
    """Generate synthetic POIs with category and attraction-strength attributes."""

    rng = np.random.default_rng(seed + 53)
    categories = np.array(["transit", "office", "mall", "university", "hospital", "leisure"])
    category_probability = np.array([0.25, 0.22, 0.08, 0.10, 0.12, 0.23])
    rows: list[tuple[str, str, str, float, float, float]] = []
    for index in range(count):
        anchor = DISTRICT_ANCHORS[int(rng.integers(0, len(DISTRICT_ANCHORS)))]
        district, latitude, longitude, density, _, transit = anchor
        category = str(rng.choice(categories, p=category_probability))
        spread = 0.010 if category in {"transit", "mall"} else 0.018
        lat = latitude + float(rng.normal(0, spread))
        lon = longitude + float(rng.normal(0, spread * 1.3))
        attraction = np.clip(
            0.35 + 0.35 * density + 0.25 * transit + rng.normal(0, 0.08),
            0.15,
            1.0,
        )
        rows.append(
            (
                f"P{index + 1:04d}",
                f"{category.title()} POI {index + 1:04d}",
                category,
                lat,
                lon,
                round(float(attraction), 4),
            )
        )
    return _point_frame(
        rows,
        ["poi_id", "poi_name", "category", "latitude", "longitude", "attraction_index"],
    )


def generate_all(seed: int, resolution: int) -> dict[str, gpd.GeoDataFrame]:
    """Build all base spatial entities."""

    return {
        "footprint": metropolitan_footprint(),
        "grid": generate_h3_grid(resolution),
        "candidates": generate_candidates(seed),
        "existing_stores": generate_existing_stores(seed),
        "competitors": generate_competitors(seed),
        "pois": generate_pois(seed),
    }
