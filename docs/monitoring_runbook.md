# Monitoring Runbook

## Service indicators

| Signal | Normal | Warning | Critical action |
|---|---|---|---|
| API availability | ≥99.5% monthly | <99.5% | rollback/restart; inspect dependency |
| p95 request latency | <500 ms | 500–1,000 ms | inspect CPU, payload and disk |
| 5xx rate | <1% | 1–3% | inspect logs and recent release |
| data critical failures | 0 | n/a | stop publication |
| spatial coverage warnings | documented baseline | increase | inspect CRS, extent and source |
| model MAE drift | <15% vs approved baseline | 15–25% | analytical review |
| rank stability | top-five probability stable | material decline | re-run sensitivity |
| solver status | `Optimal` | n/a | block scenario output |

Prometheus scrapes `/metrics`; Grafana provisions the included dashboard. Logs must
include request path, status, latency and run version but not secrets or payload data.

## Daily checks

1. Confirm API health and scrape success.
2. Check 5xx rate, p95 latency and restart count.
3. Confirm the loaded artifact manifest matches the approved run.
4. Review new data-quality warnings and failed pipeline schedules.

## Analytical release checks

1. Run the full data-quality ledger.
2. Compare feature distribution and missingness with the approved baseline.
3. Run spatial cross-validation and compare fold/residual metrics.
4. Reconcile SHAP values and AHP factor contributions.
5. Run sensitivity and all scenario optimizations.
6. Confirm solver feasibility, budget, distance and coverage constraints.
7. Review changed metrics and obtain analytical/business sign-off.

## Alert response

- **P1:** unsafe/incorrect portfolio published, data exposure or widespread outage.
  Disable affected endpoint/output, preserve evidence and start incident response.
- **P2:** material metric drift, repeated 5xx or optimizer failure. Stop the affected
  release and investigate within four hours.
- **P3:** non-critical coverage warning or dashboard degradation. Triage next business
  day and document disposition.

## Rollback

Deploy the previous approved image and artifact set, verify `/health`, candidate count,
top candidate and scenario summary, then compare manifest hashes. Do not mix a model
from one run with features or score specifications from another.

