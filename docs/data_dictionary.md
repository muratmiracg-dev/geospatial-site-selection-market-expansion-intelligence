# Data Dictionary

## Candidate and output fields

| Field | Type / unit | Meaning |
|---|---|---|
| `candidate_id` | string | Stable synthetic candidate identifier |
| `latitude`, `longitude` | degrees | WGS84 point coordinates |
| `h3_cell` | string | H3 resolution-8 cell |
| `store_area_sqm` | m² | Assumed gross store area |
| `income_index` | index | Synthetic local income proxy |
| `purchasing_power_index` | index | Synthetic spending-power proxy |
| `commercial_index` | 0–1 | Commercial attraction proxy |
| `transit_index`, `walkability_index`, `road_index` | 0–1 | Mobility proxies |
| `congestion_index` | 0–1 | Higher means more congestion |
| `rent_try_sqm_month` | TRY/m²/month | Synthetic asking-rent proxy |
| `competitor_density_3km` | count | Competitors within projected 3 km |
| `poi_density_2km` | count | POIs within projected 2 km |
| `accessible_pop_drive_5/10/15` | people | Network-reachable population |
| `accessible_pop_walk_5/10/15` | people | Network-reachable population |
| `cannibalization_risk` | 0–1 | Catchment overlap and distance-decay risk |
| `nearest_existing_store_km` | km | Projected nearest-store distance |
| `euclidean_vs_network_population_gap` | ratio | Buffer-versus-network difference |
| `opening_cost_try_m` | TRY m | Synthetic opening investment |
| `annual_opex_try_m` | TRY m/year | Synthetic operating expense |
| `huff_capture_demand` | demand units | Gravity-model captured demand |
| `huff_diverted_demand` | demand units | Demand diverted from current estate |
| `huff_diversion_ratio` | 0–1 | Diverted / captured demand |
| `predicted_sales_try_m` | TRY m/year | Model demand potential |
| `sales_p10_try_m`, `sales_p90_try_m` | TRY m/year | Empirical residual interval |
| `expected_ebit_try_m` | TRY m/year | Controlled EBIT proxy |
| `roi_3y` | ratio | Three-year controlled ROI proxy |
| `payback_months` | months | Simple payback proxy |
| `*_normalized` | 0–1 | Direction-adjusted min-max factor |
| `location_score` | 0–100 | Sum of weighted normalized factors |
| `location_rank` | integer | Descending score rank |

## AHP factors

| Factor | Direction | Normalization | Weight |
|---|---|---|---:|
| Market potential | higher is better | min-max | 0.23 |
| Accessibility | higher is better | min-max | 0.15 |
| Commercial attraction | higher is better | min-max | 0.11 |
| White space | higher is better | min-max | 0.12 |
| Cost efficiency | higher is better after inversion | min-max | 0.10 |
| Cannibalization resilience | higher is better | min-max | 0.11 |
| Profitability | higher is better | min-max | 0.13 |
| Delivery confidence | higher is better | min-max | 0.05 |

## Scenario fields

| Field | Unit | Meaning |
|---|---|---|
| `solver_status` | string | PuLP/CBC terminal status |
| `selected_store_count` | count | Number selected |
| `budget_try_m` | TRY m | Scenario cap |
| `budget_used_try_m` | TRY m | Selected investment |
| `incremental_covered_population` | people | Newly covered 10-minute population |
| `market_coverage_rate` | ratio | Existing plus selected metro coverage |
| `portfolio_sales_try_m` | TRY m | Scenario-adjusted synthetic sales |
| `portfolio_expected_ebit_try_m` | TRY m | Scenario-adjusted synthetic EBIT |
| `objective_value` | points | Composite optimizer objective |

