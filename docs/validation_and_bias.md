# Validation, Bias Assessment and Limitations

## Validation design

Random row splits leak information when nearby locations share spatial context. The
benchmark therefore assigns projected 12 km blocks and uses GroupKFold so a block
appears in only one validation fold. Out-of-fold residuals feed both reported metrics
and empirical prediction intervals.

Additional validation gates:

- target/prediction reconciliation and non-negativity;
- fold membership uniqueness;
- monotonic 5/10/15-minute accessibility;
- AHP weights sum to one;
- AHP consistency ratio below 0.10;
- optimizer terminal status and budget feasibility;
- pairwise minimum-distance conflicts;
- exact scenario selection-to-summary reconciliation.

## Bias and fairness

There are no individuals in the data, so the system does not make person-level
decisions. Geographic allocative effects remain possible:

| Risk | Mechanism | Control |
|---|---|---|
| Affluence bias | purchasing-power variables increase demand | sensitivity; business review; service-equity overlay |
| Centrality bias | transit/POI features favor dense centers | white-space and cost factors; corridor review |
| Historical estate bias | current stores define coverage/cannibalization | report uncovered demand separately |
| Cost exclusion | expensive areas may be suppressed | expose raw cost, factor contribution and scenario trade-off |
| Map precision bias | approximate anchors imply false accuracy | field-coordinate gate and limitation labels |
| Synthetic optimism | controlled target inflates fit | explicit model-card warning; no production claim |

## Sensitivity

The pipeline perturbs weights with 750 Dirichlet draws and runs one-at-a-time factor
changes. C24 remains top-five in 100% of sampled weights; this indicates rank stability
within the sampled assumptions, not investment readiness. Scenario changes separately
stress budget, sales, costs and capacity.

## Required production validation

Before any real deployment:

1. replace synthetic outcomes with governed real aggregates;
2. use rolling time and spatial holdouts;
3. test residuals by district, density, income band and store format;
4. independently validate routing with live/open road graphs;
5. compare predictions with a transparent baseline;
6. calibrate prediction intervals;
7. conduct backtesting on openings not used for training;
8. obtain legal, privacy and business-owner approval.

## Known limitations

The current model has no causal identification, time-series opening ramp, stockout,
brand awareness, competitor quality, parcel-level visibility, legal feasibility,
planned infrastructure, construction pipeline or macroeconomic forecast. These are
explicit diligence inputs, not silently assumed to be zero.

