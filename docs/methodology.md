# Methodology

## 1. Decision framing

The unit of analysis is a candidate retail site; the decision unit is a multi-site
portfolio. Site ranking and portfolio selection are separated because the individually
highest-ranked sites can overlap, breach budget or fail minimum-distance constraints.

## 2. Synthetic and spatial foundation

The run uses seed `20260729`. Geographic anchors approximate public Istanbul places,
while population, income, purchasing power, store performance, costs and all business
outcomes are synthetic. The analytical footprint is intentionally not presented as an
official municipal boundary.

Geometry is stored in WGS84 (`EPSG:4326`). Data are reprojected to UTM zone 35N
(`EPSG:32635`) for distances and areas. H3 resolution 8 supplies 5,965 reproducible
microzones.

## 3. Data quality

The pipeline checks missing values, empty/invalid geometry, CRS, coordinate range,
duplicate geometry, duplicate identifiers and spatial coverage. Critical checks block
the run. The verified run has 44 passes, two warnings and no failures. The warnings
identify synthetic out-of-footprint competitor and POI test records.

## 4. Network accessibility

Centroid adjacency between neighboring H3 cells forms the base graph. Explicit bridge
links connect cross-water corridors so the model is a connected metropolitan network.
Projected edge length is divided by mode-specific speed and adjusted by road,
walkability and congestion indicators.

Dijkstra shortest paths calculate the microzones reachable within 5, 10 and 15
minutes by driving and walking. Accessible population is the sum of unique reachable
microzones. This is materially different from a circular buffer: for C24 Ikitelli,
the modeled 10-minute drive population is 396,396 and the recorded naive-buffer versus
network population gap is 66.111%.

This network is a deterministic analytical approximation, not live routing. A current
road network and traffic source must replace it before investment approval.

## 5. Competition, POIs and white space

Projected spatial joins count competitors within 3 km and POIs within 2 km. White-space
opportunity combines demand weight and competition headroom, then penalizes
current-estate coverage and Huff diversion. The factor is normalized across the
candidate set; it is not a claim that an area has no competition.

## 6. Huff/gravity and cannibalization

Candidate attractiveness is proportional to assumed capacity, commercial attraction
and demand, and inversely related to distance using a decay exponent of 1.65. Customer
share is normalized across the current and candidate estate. Diversion measures the
share pulled from existing stores.

Cannibalization risk combines 10-minute catchment overlap and nearest-store
distance decay. Huff diversion remains a separate field, preventing distinct overlap
mechanisms from being hidden in one number.

## 7. Demand potential model

A 320-row deterministic synthetic benchmark is grouped into 12 km projected spatial
blocks. Five-fold `GroupKFold` produces strictly out-of-block predictions. The final
random forest is trained only after the out-of-fold evaluation.

Verified out-of-fold metrics:

| Metric | Value |
|---|---:|
| MAE | TRY 3.818541m |
| RMSE | TRY 5.732220m |
| R² | 0.964329 |
| MAPE | 2.648% |

The high fit reflects a controlled synthetic response function and does not establish
real-world accuracy. Prediction intervals use out-of-fold residual quantiles. SHAP
TreeExplainer contributions reconcile the model baseline to each candidate
prediction.

## 8. AHP and location scoring

A reciprocal AHP comparison matrix is constructed from the approved factor-weight
ratios. Its consistency ratio is effectively zero and passes the `<0.10` rule. Each
factor declares its direction and uses direction-adjusted min-max normalization.
The scoring gate requires exactly one finite, strictly positive weight for every
approved factor and rejects missing or unknown factors before constructing the
comparison matrix. Accepted weights are normalized to sum to one.

For candidate \(i\), the score is:

\[
S_i = 100 \sum_{j=1}^{8} w_j z_{ij}
\]

where \(w_j\) is the AHP weight and \(z_{ij}\) is the normalized factor. The contribution
of each factor is stored explicitly. A 750-draw Dirichlet perturbation and
one-at-a-time tests quantify rank sensitivity.

## 9. Location-allocation optimization

Binary variables select candidates and count each 10-minute network microzone once.
The objective balances expected EBIT, location score and incremental population, with
a cannibalization penalty. Constraints include:

- scenario budget;
- maximum selected-store count;
- minimum pairwise candidate distance;
- candidate capacity/portfolio count;
- unique coverage attribution.

The verified solver status is `Optimal` in all three scenarios.

| Scenario | Sites | Budget used | Incremental population | Coverage | Sales | EBIT |
|---|---:|---:|---:|---:|---:|---:|
| Pessimistic | 3 | TRY 74.473m | 908,890 | 20.447% | TRY 466.551m | TRY -2.071m |
| Base | 4 | TRY 93.382m | 1,329,291 | 23.125% | TRY 732.554m | TRY 28.826m |
| Optimistic | 6 | TRY 135.783m | 2,068,792 | 27.835% | TRY 1,256.350m | TRY 81.520m |

## 10. Interpretation protocol

Use score and optimization outputs to prioritize diligence, not to authorize a store.
For each shortlisted site validate exact coordinates, legal access, parcel conditions,
live routing, traffic, visibility, competing pipeline, binding rent, fit-out capex,
staffing, margin, opening ramp and portfolio operational capacity.
