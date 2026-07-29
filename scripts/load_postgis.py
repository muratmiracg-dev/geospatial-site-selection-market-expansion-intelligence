"""Load processed spatial layers into the prepared PostGIS schema."""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine

SPATIAL_LAYERS = {
    "h3_microzones.geojson": (
        "h3_microzone",
        [
            "h3_cell",
            "population",
            "households",
            "income_index",
            "purchasing_power_index",
            "commercial_index",
            "transit_index",
            "walkability_index",
            "road_index",
            "congestion_index",
            "rent_try_sqm_month",
            "white_space_index",
            "existing_covered",
            "geometry",
        ],
    ),
    "existing_stores.geojson": (
        "existing_store",
        [
            "store_id",
            "store_name",
            "store_area_sqm",
            "opened_year",
            "annual_sales_try_m",
            "ebit_margin",
            "geometry",
        ],
    ),
    "candidate_locations.geojson": (
        "candidate_site",
        [
            "candidate_id",
            "candidate_name",
            "store_area_sqm",
            "delivery_risk",
            "permitting_months",
            "geometry",
        ],
    ),
    "competitors.geojson": (
        "competitor",
        [
            "competitor_id",
            "competitor_name",
            "anchor_district",
            "area_sqm",
            "geometry",
        ],
    ),
    "pois.geojson": (
        "poi",
        ["poi_id", "poi_name", "category", "attraction_index", "geometry"],
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--schema", default="site_intelligence")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    engine = create_engine(args.database_url)
    for filename, (table, columns) in SPATIAL_LAYERS.items():
        frame = gpd.read_file(root / "data" / "processed" / filename).to_crs(4326)[columns]
        frame = frame.rename_geometry("geom")
        frame.to_postgis(table, engine, schema=args.schema, if_exists="append", index=False)
        print(f"loaded {len(frame):,} rows into {args.schema}.{table}")

    scores = pd.read_csv(root / "artifacts" / "data" / "candidate_scores.csv")[
        [
            "candidate_id",
            "location_rank",
            "location_score",
            "predicted_sales_try_m",
            "accessible_pop_drive_10",
            "accessible_pop_walk_15",
            "cannibalization_risk",
            "opening_cost_try_m",
            "roi_3y",
            "recommendation_tier",
        ]
    ]
    scores.to_sql(
        "candidate_score",
        engine,
        schema=args.schema,
        if_exists="append",
        index=False,
        method="multi",
    )
    print(f"loaded {len(scores):,} rows into {args.schema}.candidate_score")

    selections = pd.read_csv(root / "artifacts" / "data" / "scenario_selections.csv")[
        [
            "scenario",
            "priority",
            "candidate_id",
            "scenario_sales_try_m",
            "scenario_opening_cost_try_m",
        ]
    ]
    selections.to_sql(
        "scenario_selection",
        engine,
        schema=args.schema,
        if_exists="append",
        index=False,
        method="multi",
    )
    print(f"loaded {len(selections):,} rows into {args.schema}.scenario_selection")


if __name__ == "__main__":
    main()
