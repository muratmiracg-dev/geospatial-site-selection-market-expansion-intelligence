"""CRS-safe geometry, distance, H3, and spatial-neighbor helpers."""

from __future__ import annotations

import math
from collections.abc import Iterable

import geopandas as gpd
import h3
import numpy as np
from pyproj import Geod, Transformer
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

from site_intelligence.constants import METRIC_CRS, STORAGE_CRS

WGS84_GEOD = Geod(ellps="WGS84")
WGS84_TO_METRIC = Transformer.from_crs(STORAGE_CRS, METRIC_CRS, always_xy=True)


def h3_polygon_cells(polygon: Polygon, resolution: int) -> set[str]:
    """Return H3 cells whose centers fall inside a WGS84 polygon."""

    outer = [(lat, lon) for lon, lat in polygon.exterior.coords]
    shape = h3.LatLngPoly(outer)
    return set(h3.polygon_to_cells(shape, resolution))


def h3_cell_polygon(cell: str) -> Polygon:
    """Convert an H3 cell boundary to a WGS84 Shapely polygon."""

    boundary = h3.cell_to_boundary(cell)
    return Polygon([(lon, lat) for lat, lon in boundary])


def nearest_index(
    frame: gpd.GeoDataFrame,
    latitude: float,
    longitude: float,
    *,
    metric_crs: str = METRIC_CRS,
) -> int:
    """Find the index of the closest geometry using a projected CRS."""

    projected = frame.to_crs(metric_crs)
    if metric_crs == METRIC_CRS:
        x, y = WGS84_TO_METRIC.transform(longitude, latitude)
    else:
        x, y = Transformer.from_crs(STORAGE_CRS, metric_crs, always_xy=True).transform(
            longitude, latitude
        )
    target = Point(x, y)
    return int(projected.distance(target).idxmin())


def projected_distance_km(
    left: gpd.GeoDataFrame,
    right: gpd.GeoDataFrame,
    *,
    metric_crs: str = METRIC_CRS,
) -> np.ndarray:
    """Return an all-pairs projected distance matrix in kilometres."""

    left_projected = left.to_crs(metric_crs)
    right_projected = right.to_crs(metric_crs)
    result = np.empty((len(left_projected), len(right_projected)), dtype=float)
    for row, geometry in enumerate(left_projected.geometry):
        result[row, :] = right_projected.geometry.distance(geometry).to_numpy() / 1000.0
    return result


def haversine_km(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    """Calculate geodesic point distance in kilometres."""

    _, _, distance_m = WGS84_GEOD.inv(longitude_a, latitude_a, longitude_b, latitude_b)
    return float(distance_m / 1000.0)


def service_geometry(
    grid: gpd.GeoDataFrame,
    cells: Iterable[str],
) -> Polygon:
    """Union reachable H3 cell polygons into a validated service geometry."""

    selected = grid.loc[grid["h3_cell"].isin(set(cells)), "geometry"]
    if selected.empty:
        return Polygon()
    geometry = unary_union(selected.to_list())
    return geometry if geometry.is_valid else geometry.buffer(0)


def bearing_degrees(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    """Return forward bearing in degrees."""

    azimuth, _, _ = WGS84_GEOD.inv(longitude_a, latitude_a, longitude_b, latitude_b)
    return float((azimuth + 360.0) % 360.0)


def sigmoid(value: float) -> float:
    """Numerically stable scalar logistic transform."""

    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)
