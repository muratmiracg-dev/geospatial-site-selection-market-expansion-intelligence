"""Interactive Folium decision maps with explicit source attribution."""

from __future__ import annotations

from pathlib import Path

import folium
import geopandas as gpd
import pandas as pd
from branca.colormap import linear

ISTANBUL_CENTER = [41.02, 28.98]
TILE_ATTRIBUTION = (
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'
)


def _base_map(zoom_start: int = 9) -> folium.Map:
    return folium.Map(
        location=ISTANBUL_CENTER,
        zoom_start=zoom_start,
        tiles="OpenStreetMap",
        attr=TILE_ATTRIBUTION,
        control_scale=True,
        prefer_canvas=True,
    )


def _candidate_popup(row: pd.Series) -> str:
    return (
        f"<b>{row['candidate_name']}</b><br>"
        f"ID: {row['candidate_id']}<br>"
        f"Rank: {int(row['location_rank'])}<br>"
        f"Score: {row['location_score']:.1f}/100<br>"
        f"Predicted sales: TRY {row['predicted_sales_try_m']:.1f}m<br>"
        f"10-min drive population: {int(row['accessible_pop_drive_10']):,}<br>"
        f"Cannibalization risk: {row['cannibalization_risk']:.1%}<br>"
        f"Opening cost: TRY {row['opening_cost_try_m']:.1f}m<br>"
        "<i>Decision support only - human review required.</i>"
    )


def create_candidate_map(
    candidates: gpd.GeoDataFrame,
    existing: gpd.GeoDataFrame,
    competitors: gpd.GeoDataFrame,
    selections: pd.DataFrame,
    output_path: str | Path,
) -> None:
    """Create a layer-controlled map of sites and scenario recommendations."""

    map_object = _base_map()
    existing_layer = folium.FeatureGroup(name="Existing stores", show=True)
    competitor_layer = folium.FeatureGroup(name="Synthetic competitors", show=False)
    candidate_layer = folium.FeatureGroup(name="Candidate sites", show=True)
    selected_layer = folium.FeatureGroup(name="Base scenario portfolio", show=True)

    for _, row in existing.iterrows():
        folium.CircleMarker(
            [row["latitude"], row["longitude"]],
            radius=6,
            color="#0B3954",
            fill=True,
            fill_color="#0B3954",
            fill_opacity=0.95,
            tooltip=f"Existing: {row['store_name']}",
        ).add_to(existing_layer)
    for _, row in competitors.iterrows():
        folium.CircleMarker(
            [row["latitude"], row["longitude"]],
            radius=2.5,
            color="#E94F37",
            fill=True,
            fill_color="#E94F37",
            fill_opacity=0.55,
            tooltip=row["competitor_name"],
        ).add_to(competitor_layer)
    for _, row in candidates.iterrows():
        color = "#2A9D8F" if int(row["location_rank"]) <= 5 else "#F4A261"
        folium.CircleMarker(
            [row["latitude"], row["longitude"]],
            radius=7 if int(row["location_rank"]) <= 5 else 5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            popup=folium.Popup(_candidate_popup(row), max_width=330),
            tooltip=f"#{int(row['location_rank'])} {row['candidate_name']}",
        ).add_to(candidate_layer)

    base_selected = set(
        selections.loc[selections["scenario"] == "base", "candidate_id"].astype(str)
    )
    for _, row in candidates[candidates["candidate_id"].isin(base_selected)].iterrows():
        folium.CircleMarker(
            [row["latitude"], row["longitude"]],
            radius=13,
            color="#FFD166",
            weight=4,
            fill=False,
            tooltip=f"Base portfolio: {row['candidate_name']}",
        ).add_to(selected_layer)

    existing_layer.add_to(map_object)
    competitor_layer.add_to(map_object)
    candidate_layer.add_to(map_object)
    selected_layer.add_to(map_object)
    folium.LayerControl(collapsed=False).add_to(map_object)
    map_object.get_root().html.add_child(
        folium.Element(
            '<div style="position:fixed;bottom:18px;left:50px;z-index:9999;'
            'background:white;padding:8px 12px;border:1px solid #888;font-size:11px;">'
            "Commercial attributes are deterministic synthetic data. Map tiles: "
            f"{TILE_ATTRIBUTION}.</div>"
        )
    )
    map_object.save(str(output_path))


def create_white_space_map(
    grid: gpd.GeoDataFrame,
    candidates: gpd.GeoDataFrame,
    output_path: str | Path,
) -> None:
    """Create an H3 white-space opportunity choropleth."""

    map_object = _base_map()
    colormap = linear.YlGnBu_09.scale(0, 100)
    colormap.caption = "White-space opportunity index (synthetic)"
    folium.GeoJson(
        grid[["h3_cell", "population", "white_space_index", "existing_covered", "geometry"]],
        name="H3 white-space index",
        style_function=lambda feature: {
            "fillColor": colormap(feature["properties"]["white_space_index"]),
            "color": "#FFFFFF",
            "weight": 0.25,
            "fillOpacity": 0.68,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["h3_cell", "population", "white_space_index", "existing_covered"],
            aliases=["H3", "Population", "Opportunity", "Existing coverage"],
            localize=True,
        ),
    ).add_to(map_object)
    for _, row in candidates.nsmallest(10, "location_rank").iterrows():
        folium.CircleMarker(
            [row["latitude"], row["longitude"]],
            radius=6,
            color="#FF6B35",
            fill=True,
            fill_opacity=0.95,
            tooltip=f"#{int(row['location_rank'])} {row['candidate_name']}",
        ).add_to(map_object)
    colormap.add_to(map_object)
    folium.LayerControl().add_to(map_object)
    map_object.save(str(output_path))


def create_isochrone_map(
    candidates: gpd.GeoDataFrame,
    isochrones: gpd.GeoDataFrame,
    output_path: str | Path,
) -> None:
    """Create layered drive/walk isochrones for the three highest-ranked candidates."""

    map_object = _base_map(10)
    top_ids = candidates.nsmallest(3, "location_rank")["candidate_id"].astype(str).tolist()
    colors = {5: "#2A9D8F", 10: "#F4A261", 15: "#E76F51"}
    for mode in ("drive", "walk"):
        layer = folium.FeatureGroup(name=f"Top-3 {mode} isochrones", show=mode == "drive")
        subset = isochrones[
            (isochrones["candidate_id"].isin(top_ids)) & (isochrones["mode"] == mode)
        ].sort_values("minutes", ascending=False)
        for _, row in subset.iterrows():
            folium.GeoJson(
                row.geometry,
                style_function=lambda _, minute=int(row["minutes"]), selected_mode=mode: {
                    "fillColor": colors[minute],
                    "color": colors[minute],
                    "weight": 1.1,
                    "dashArray": "4,4" if selected_mode == "walk" else None,
                    "fillOpacity": 0.09 if selected_mode == "drive" else 0.04,
                },
                tooltip=(
                    f"{row['candidate_id']} | {mode} {int(row['minutes'])} min | "
                    f"{int(row['accessible_population']):,} people"
                ),
            ).add_to(layer)
        layer.add_to(map_object)
    for _, row in candidates[candidates["candidate_id"].isin(top_ids)].iterrows():
        folium.Marker(
            [row["latitude"], row["longitude"]],
            tooltip=f"#{int(row['location_rank'])} {row['candidate_name']}",
            icon=folium.Icon(color="darkblue", icon="shopping-cart", prefix="fa"),
        ).add_to(map_object)
    folium.LayerControl(collapsed=False).add_to(map_object)
    map_object.save(str(output_path))


def create_scenario_map(
    candidates: gpd.GeoDataFrame,
    selections: pd.DataFrame,
    output_path: str | Path,
) -> None:
    """Create toggleable optimistic/base/pessimistic portfolio layers."""

    map_object = _base_map()
    color_by_scenario = {"optimistic": "#2A9D8F", "base": "#3A86FF", "pessimistic": "#E76F51"}
    indexed = candidates.set_index("candidate_id")
    for scenario in ("optimistic", "base", "pessimistic"):
        layer = folium.FeatureGroup(name=f"{scenario.title()} portfolio", show=scenario == "base")
        subset = selections[selections["scenario"] == scenario]
        for _, selected in subset.iterrows():
            row = indexed.loc[selected["candidate_id"]].copy()
            row["candidate_id"] = selected["candidate_id"]
            folium.CircleMarker(
                [row["latitude"], row["longitude"]],
                radius=10,
                color=color_by_scenario[scenario],
                weight=3,
                fill=True,
                fill_color=color_by_scenario[scenario],
                fill_opacity=0.80,
                tooltip=f"{scenario.title()} P{int(selected['priority'])}: {row['candidate_name']}",
                popup=folium.Popup(_candidate_popup(row), max_width=330),
            ).add_to(layer)
        layer.add_to(map_object)
    folium.LayerControl(collapsed=False).add_to(map_object)
    map_object.save(str(output_path))
