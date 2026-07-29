-- PostGIS physical model for auditable site-selection analytics.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE SCHEMA IF NOT EXISTS site_intelligence;

CREATE TABLE IF NOT EXISTS site_intelligence.h3_microzone (
    h3_cell text PRIMARY KEY,
    population integer NOT NULL CHECK (population >= 0),
    households integer NOT NULL CHECK (households >= 0),
    income_index numeric(9,3) NOT NULL,
    purchasing_power_index numeric(9,3) NOT NULL,
    commercial_index numeric(9,6) NOT NULL CHECK (commercial_index BETWEEN 0 AND 1),
    transit_index numeric(9,6) NOT NULL CHECK (transit_index BETWEEN 0 AND 1),
    walkability_index numeric(9,6) NOT NULL CHECK (walkability_index BETWEEN 0 AND 1),
    road_index numeric(9,6) NOT NULL CHECK (road_index BETWEEN 0 AND 1),
    congestion_index numeric(9,6) NOT NULL CHECK (congestion_index BETWEEN 0 AND 1),
    rent_try_sqm_month numeric(12,2) NOT NULL,
    white_space_index numeric(7,2),
    existing_covered boolean NOT NULL DEFAULT false,
    geom geometry(Polygon, 4326) NOT NULL
);

CREATE TABLE IF NOT EXISTS site_intelligence.existing_store (
    store_id text PRIMARY KEY,
    store_name text NOT NULL,
    store_area_sqm integer NOT NULL CHECK (store_area_sqm > 0),
    opened_year integer NOT NULL,
    annual_sales_try_m numeric(12,3) NOT NULL,
    ebit_margin numeric(8,4) NOT NULL,
    geom geometry(Point, 4326) NOT NULL
);

CREATE TABLE IF NOT EXISTS site_intelligence.candidate_site (
    candidate_id text PRIMARY KEY,
    candidate_name text NOT NULL,
    store_area_sqm integer NOT NULL CHECK (store_area_sqm > 0),
    delivery_risk numeric(8,6) NOT NULL CHECK (delivery_risk BETWEEN 0 AND 1),
    permitting_months integer NOT NULL CHECK (permitting_months > 0),
    geom geometry(Point, 4326) NOT NULL
);

CREATE TABLE IF NOT EXISTS site_intelligence.competitor (
    competitor_id text PRIMARY KEY,
    competitor_name text NOT NULL,
    anchor_district text NOT NULL,
    area_sqm integer NOT NULL CHECK (area_sqm > 0),
    geom geometry(Point, 4326) NOT NULL
);

CREATE TABLE IF NOT EXISTS site_intelligence.poi (
    poi_id text PRIMARY KEY,
    poi_name text NOT NULL,
    category text NOT NULL,
    attraction_index numeric(8,4) NOT NULL CHECK (attraction_index BETWEEN 0 AND 1),
    geom geometry(Point, 4326) NOT NULL
);

CREATE TABLE IF NOT EXISTS site_intelligence.candidate_score (
    candidate_id text PRIMARY KEY REFERENCES site_intelligence.candidate_site(candidate_id),
    location_rank integer NOT NULL,
    location_score numeric(8,3) NOT NULL CHECK (location_score BETWEEN 0 AND 100),
    predicted_sales_try_m numeric(12,3) NOT NULL,
    accessible_pop_drive_10 integer NOT NULL,
    accessible_pop_walk_15 integer NOT NULL,
    cannibalization_risk numeric(8,6) NOT NULL CHECK (cannibalization_risk BETWEEN 0 AND 1),
    opening_cost_try_m numeric(12,3) NOT NULL,
    roi_3y numeric(12,6),
    recommendation_tier text NOT NULL,
    model_version text NOT NULL DEFAULT '1.0.0',
    scored_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS site_intelligence.scenario_selection (
    scenario text NOT NULL CHECK (scenario IN ('optimistic', 'base', 'pessimistic')),
    priority integer NOT NULL,
    candidate_id text NOT NULL REFERENCES site_intelligence.candidate_site(candidate_id),
    scenario_sales_try_m numeric(12,3) NOT NULL,
    scenario_opening_cost_try_m numeric(12,3) NOT NULL,
    PRIMARY KEY (scenario, candidate_id)
);

CREATE INDEX IF NOT EXISTS h3_microzone_geom_gix
    ON site_intelligence.h3_microzone USING gist (geom);
CREATE INDEX IF NOT EXISTS existing_store_geom_gix
    ON site_intelligence.existing_store USING gist (geom);
CREATE INDEX IF NOT EXISTS candidate_site_geom_gix
    ON site_intelligence.candidate_site USING gist (geom);
CREATE INDEX IF NOT EXISTS competitor_geom_gix
    ON site_intelligence.competitor USING gist (geom);
CREATE INDEX IF NOT EXISTS poi_geom_gix
    ON site_intelligence.poi USING gist (geom);
CREATE INDEX IF NOT EXISTS candidate_score_rank_idx
    ON site_intelligence.candidate_score (location_rank);

