# Power BI Project Starter

This folder contains a source-control-friendly PBIP scaffold using an enhanced
PBIR report definition and a TMDL semantic model. It is intentionally a starter
project: the five pages are defined and annotated with their design intent, while
visual placement is completed in Power BI Desktop using the supplied blueprint.

## Open

1. Install a current Power BI Desktop release that supports PBIP, PBIR and TMDL.
2. Replace `REPLACE_WITH_ABSOLUTE_PROJECT_PATH` in
   `MarketExpansion.SemanticModel/definition/expressions.tmdl`.
3. Open `MarketExpansion.pbip`.
4. Refresh the four CSV-backed tables.
5. Build visuals according to `dashboard_blueprint.md`.

The checked-in interactive HTML maps remain the detailed geospatial reference.
The Power BI pages should use Azure Maps, Shape Map, Icon Map or another
organization-approved visual after license and tenant-policy review.

## Validation boundary

The JSON files are syntax-validated in the local QA pipeline. Power BI Desktop is
not available in this Linux build environment, so the PBIP is not claimed as
Desktop-render-verified. This limitation is explicit rather than hidden.

Official format references:

- https://learn.microsoft.com/power-bi/developer/projects/projects-overview
- https://learn.microsoft.com/power-bi/developer/projects/projects-report
- https://learn.microsoft.com/power-bi/developer/projects/projects-dataset

