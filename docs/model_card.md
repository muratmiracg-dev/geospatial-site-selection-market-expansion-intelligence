# Model Card — Synthetic Site Demand Potential

## Model details

- **Model:** scikit-learn random forest regressor
- **Version:** 1.0.0
- **Run date:** 2026-07-29
- **Target:** synthetic annual sales potential, TRY millions
- **Training data:** 320 deterministic synthetic benchmark locations
- **Spatial validation:** five-fold GroupKFold over 33 projected 12 km blocks
- **Artifact:** `artifacts/models/demand_model.joblib`

## Intended use

Rank candidate locations for analyst review and provide one input to an AHP score and
portfolio optimizer. The model is a demonstration of spatially responsible validation,
not a calibrated production forecast for real stores.

## Out-of-scope use

- investment authorization;
- valuation, lending or regulated decisions;
- person-level targeting or demographic exclusion;
- estimating performance outside the analytical Istanbul footprint;
- using predictions without field and commercial validation.

## Performance

Out-of-fold MAE is TRY 3.819m, RMSE TRY 5.732m, R² 0.964 and MAPE 2.648%. Metrics are
computed from actual pipeline predictions, not illustrative values. High fit is
expected because the response is produced by a controlled synthetic function.

## Explainability

SHAP TreeExplainer calculates local contributions. For C24 Ikitelli the model baseline
is TRY 162.787m and the final prediction is TRY 183.107m. SHAP explains the demand
prediction; it does not explain the AHP location score, whose contributions are stored
separately.

## Data and bias

No personal data, protected-class labels, customer transactions or device traces are
used. This eliminates person-level privacy risk but does not eliminate geographic
proxy risk. Synthetic income and purchasing-power indices can still encode assumptions
that favor affluent or well-connected areas.

Required real-data deployment tests include subgroup/geography residual analysis,
feature coverage, protected-area and accessibility review, rent and service-equity
sensitivity, and human review of locations that are disadvantaged by model proxies.

## Limitations

- Synthetic labels make absolute accuracy claims invalid.
- The H3 network approximates travel time and omits live traffic and turn restrictions.
- Candidate selection determines the scoring min/max range.
- Out-of-footprint extrapolation is unsupported.
- Economic inputs are controlled assumptions, not binding quotes.
- SHAP is associative, not causal.

## Monitoring

Monitor feature missingness, range violations, spatial coverage, prediction
distribution, residual MAE/RMSE by block, SHAP drift, candidate-rank stability and
score/portfolio change. Retraining requires a versioned dataset, spatial validation,
model-card update and analytical-owner approval.

## Accountability

The analytical owner validates model behavior; the data owner approves data
provenance; the business owner confirms assumptions; the investment committee makes
the final decision. The API and dashboards must retain the “human review required”
label.

