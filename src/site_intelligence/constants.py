"""Shared geographic and feature constants."""

from __future__ import annotations

MODEL_FEATURES = [
    "accessible_pop_drive_10",
    "income_index",
    "commercial_index",
    "transit_index",
    "poi_density_2km",
    "competitor_density_3km",
    "rent_try_sqm_month",
    "cannibalization_risk",
    "walkability_index",
]

SCORE_FACTORS = [
    "market_potential",
    "accessibility",
    "commercial_attraction",
    "white_space",
    "cost_efficiency",
    "cannibalization_resilience",
    "profitability",
    "delivery_confidence",
]

STORAGE_CRS = "EPSG:4326"
METRIC_CRS = "EPSG:32635"
