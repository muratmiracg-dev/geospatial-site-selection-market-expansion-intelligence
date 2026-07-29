# Geospatial Dashboard Blueprint

## Visual language

- 1280 x 720 canvas, warm off-white background (`#F7F3E9`).
- Navy (`#0B3954`) establishes hierarchy; teal (`#2A9D8F`) signals opportunity;
  orange (`#F4A261`) flags review; red (`#E76F51`) marks risk.
- Map-first compositions, restrained KPI ribbons and flat analytical tables.
- Every page carries `Synthetic decision support - human review required`.

## Page 1 - Executive Overview

- KPI ribbon: top candidate, score, base selected stores, budget used, incremental
  population and market coverage.
- Main map: existing stores, candidates and base recommendations.
- Right-side ranking: candidate, score, predicted sales, ROI and risk.
- Bottom scenario strip: optimistic/base/pessimistic comparison.

## Page 2 - Candidate Ranking

- Ranked matrix with conditional formatting for score, ROI and cannibalization.
- AHP contribution stacked bar for the selected candidate.
- SHAP positive/negative contribution waterfall.
- Slicers: recommendation tier, score band, risk band and side of Istanbul.

## Page 3 - Accessibility & White Space

- H3 opportunity map colored by white-space index.
- Toggle for 5/10/15-minute drive or walk access.
- Cards for accessible population, POI density, competitor density and the
  straight-line-versus-network population gap.
- Detail table lists the highest-opportunity uncovered H3 microzones.

## Page 4 - Scenario Portfolio

- Scenario slicer and selected-candidate map.
- Budget utilization bullet chart.
- Incremental coverage and portfolio sales waterfall.
- Priority list with constraint notes and minimum-distance conflicts.

## Page 5 - Model & Governance

- Spatial block CV metrics and actual-versus-predicted scatter.
- Weight sensitivity and top-five rank stability.
- Data-quality checks, source/license crosswalk and known limitations.
- Human decision gates and monitoring ownership.

