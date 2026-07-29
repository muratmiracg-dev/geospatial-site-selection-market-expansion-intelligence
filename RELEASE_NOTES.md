# Stage 1 Review Release — v1.0.0

Date: 2026-07-29

## Analytical result

- Top candidate: C24 Ikitelli Industry — 81.236/100.
- Base portfolio: C24, C18, C17 and C07.
- Base budget used: TRY 93.382m of TRY 110.000m.
- Incremental modeled 10-minute population: 1,329,291.
- Total modeled market coverage: 23.125%.
- Base expected portfolio EBIT: TRY 28.826m.
- Spatial OOF MAE / RMSE / R2: TRY 3.819m / TRY 5.732m / 0.964.

## Quality result

- 13 tests passed; 96.44% branch coverage.
- Ruff formatting and lint passed.
- 46 data checks: 44 pass, two documented warnings, zero failures.
- 39 artifact/document checks passed.
- Excel formula error scan: zero matches.
- PowerPoint: 18 rendered slides and no overflow.
- PDF: 27 rendered pages and valid structure.
- Locked dependency audit: 87 packages and zero known vulnerabilities.

## External gates

GitHub Actions, CodeQL, Trivy, Docker/PostGIS/Kubernetes runtime and Power BI Desktop
rendering are configured but cannot be claimed as executed in this unpublished local
stage. They remain explicit publication or environment acceptance gates.

All business outcomes are deterministic synthetic data. Results require human review
and are not investment advice.

`PROJECT_STATUS: READY_FOR_REVIEW — NOT_PUBLISHED`

