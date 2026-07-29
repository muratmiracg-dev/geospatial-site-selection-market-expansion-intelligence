# Data Contract

## Contract principles

- Every spatial layer declares EPSG:4326 at rest.
- Identifiers are unique, non-null strings and stable within a run.
- Latitude is in `[-90, 90]`; longitude is in `[-180, 180]`.
- Point geometries must be non-empty and valid.
- Microzone polygons must be valid and associated with a unique H3 index.
- Monetary figures use nominal synthetic TRY millions unless the column states
  otherwise.
- Rates are decimal values in `[0, 1]`.
- A data-quality warning may publish only if it is explicitly non-critical; failures
  block the pipeline.

Machine-readable schemas are in `data/contracts/`.

## Core datasets

| Dataset | Grain | Primary key | Geometry |
|---|---|---|---|
| `existing_stores` | one current store | `store_id` | Point |
| `candidate_locations` | one candidate | `candidate_id` | Point |
| `competitors` | one competitor point | `competitor_id` | Point |
| `pois` | one point of interest | `poi_id` | Point |
| `h3_microzones` | one microzone | `h3_cell` | Polygon |
| `candidate_scores` | one candidate/run | `candidate_id` | latitude/longitude columns |
| `candidate_accessibility` | candidate/mode/minutes | composite | none |
| `score_contributions` | candidate/factor | composite | none |
| `scenario_selections` | scenario/priority | composite | none |

## Candidate score contract

Required fields include candidate identity, WGS84 coordinates, cost, accessibility,
competition/POI features, Huff metrics, demand prediction, economics, raw factor
values, normalized factor values, score contributions, final score and rank.

Rules:

- `location_score` is in `[0, 100]`.
- `location_rank` is unique from 1 through the number of candidates.
- `predicted_sales_try_m >= 0`.
- `sales_p10_try_m <= predicted_sales_try_m <= sales_p90_try_m`.
- `opening_cost_try_m > 0`.
- `nearest_existing_store_km >= 0`.
- all eight AHP weights sum to one within `1e-9`.
- a candidate remains `Human review required` until external approval.

## Accessibility contract

`mode ∈ {drive, walk}` and `minutes ∈ {5, 10, 15}`. Accessible population and demand
are non-negative and must be monotonic by threshold within candidate and mode.

The catchment is defined by the H3 network graph, not a Euclidean buffer. The
`euclidean_vs_network_population_gap` field records the relative population difference
between the naive circular proxy and the 10-minute network result.

## Scenario contract

Scenario name is one of `optimistic`, `base`, `pessimistic`. A scenario result is
publishable only when `solver_status == "Optimal"`. Selected cost cannot exceed the
declared budget. Pairwise candidate distance must satisfy the scenario minimum.
Coverage counts each microzone once even when selected catchments overlap.

## Compatibility and change control

Removing or changing the meaning/type of a required field is a breaking change and
requires an ADR plus a major contract version. Additive nullable fields are minor
changes. Changes to the seed, CRS, H3 resolution, travel speeds, model target, score
weights or optimizer objective are assumption changes and must be recorded in the run
manifest.

