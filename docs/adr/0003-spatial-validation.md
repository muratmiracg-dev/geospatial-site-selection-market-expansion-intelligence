# ADR 0003 — Spatial Block Cross-Validation

- **Status:** Accepted
- **Date:** 2026-07-29

## Decision

Use projected 12 km blocks as groups in five-fold GroupKFold and report only
out-of-fold validation metrics.

## Consequences

Neighboring observations cannot be randomly split across train and validation folds.
The effective sample diversity is lower than a random split, and synthetic target
construction still limits external validity.

