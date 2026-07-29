# ADR 0004 — Separate AHP Ranking from Portfolio Optimization

- **Status:** Accepted
- **Date:** 2026-07-29

## Decision

Use AHP-weighted normalized scoring for transparent site ranking and a separate binary
maximum-coverage formulation for portfolio selection.

## Consequences

Every factor contribution is inspectable, while budget, distance, capacity and overlap
are handled at portfolio level. The selected portfolio need not equal the first
`p` candidates by rank, so both outputs and their trade-offs must be reported.

