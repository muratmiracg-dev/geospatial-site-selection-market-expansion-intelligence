# ADR 0002 — WGS84 Storage, UTM Metrics and H3 Resolution 8

- **Status:** Accepted
- **Date:** 2026-07-29

## Decision

Store exchange geometry in EPSG:4326, perform metric calculations in EPSG:32635 and
index the analytical footprint at H3 resolution 8.

## Consequences

Web compatibility and distance correctness are explicit. H3 makes microzone joins and
coverage reproducible, while its cell geometry remains an analytical discretization
that can create edge effects.

