# Interview Narrative

## 90-second version

I wanted to demonstrate that site selection is not a map-ranking problem but a
portfolio decision under uncertainty and constraints. I created a fictional Istanbul
retailer and generated every commercial outcome deterministically so the project is
safe and reproducible.

I discretized the metro footprint into 5,965 H3 cells, stored coordinates in WGS84 and
used UTM 35N for metric calculations. I built an H3 transport graph for 5/10/15-minute
drive and walk catchments, then combined competition, POIs, white space, costs, Huff
customer diversion and cannibalization. The demand model uses spatial block
cross-validation to prevent neighboring-site leakage, with SHAP for local explanations.

For the decision layer, AHP makes every factor direction, normalization, weight and
contribution auditable. A separate maximum-coverage optimizer enforces budget,
distance, capacity and unique coverage. In the base synthetic scenario it selects four
sites within TRY 93.4m and adds 1.33 million people to modeled 10-minute coverage.

The most important design choice is governance: I clearly separate synthetic evidence
from investment claims, surface limitations, and require independent routing,
commercial diligence and human approval.

## Likely follow-ups

**Why not rank by predicted sales?**  
Sales ignores cost, cannibalization, delivery confidence and portfolio overlap.
AHP preserves site-level transparency; optimization handles portfolio constraints.

**How did you prevent spatial leakage?**  
I created 12 km projected blocks and used GroupKFold. Nearby observations in the same
block cannot appear in both training and validation.

**Why is R² so high?**  
The benchmark target is deterministic synthetic data. The metric verifies pipeline
behavior, not real-world forecast accuracy; the model card says this explicitly.

**Why H3 instead of districts?**  
District averages hide local variation. H3 gives stable microzones for joins,
catchments and coverage, while I document edge effects and keep official-boundary
claims out of scope.

**What would you change for production?**  
Use governed real aggregate performance, an OSM/traffic routing engine, parcel and
competitor pipeline data, temporal backtesting, calibrated intervals, authenticated
deployment, Desktop validation for PBIP and formal investment stage gates.

