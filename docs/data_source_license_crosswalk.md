# Data Source and License Crosswalk

Access date: **2026-07-29**

| Source/component | Use in project | Data origin | License / terms | Attribution / notes |
|---|---|---|---|---|
| Project synthetic generator | commercial, demand, costs and performance | original deterministic code | MIT | Seed 20260729; no real personal data |
| Approximate public-place anchors | geographic framing only | manually encoded approximate coordinates | project documentation | Not an authoritative address dataset |
| OpenStreetMap tiles | interactive HTML basemap context | OpenStreetMap contributors | ODbL; tile usage policy applies | `© OpenStreetMap contributors` and link included |
| H3 | grid indexing | Uber H3 open source | Apache-2.0 | Library/software component |
| GeoPandas | geospatial dataframe operations | open source | BSD-3-Clause | Library/software component |
| Shapely | geometry operations | open source | BSD-3-Clause | Library/software component |
| pyproj / PROJ | CRS transformation | open source | MIT / PROJ terms | EPSG:4326 and EPSG:32635 |
| Folium / Leaflet | interactive maps | open source | MIT / BSD-2-Clause | OSM attribution preserved |
| scikit-learn | random forest and CV | open source | BSD-3-Clause | Model implementation |
| SHAP | local model explanations | open source | MIT | Explanations are non-causal |
| PuLP / CBC | optimization model | open source | MIT / EPL-2.0 | Solver status is recorded |
| Microsoft Power BI Project format | PBIP/PBIR/TMDL starter structure | Microsoft documentation | documentation/product terms | Starter requires Power BI Desktop validation |

Primary references:

- OpenStreetMap copyright and attribution: <https://www.openstreetmap.org/copyright>
- H3 documentation: <https://h3geo.org/docs/>
- GeoPandas project/about: <https://geopandas.org/en/stable/about.html>
- Shapely documentation: <https://shapely.readthedocs.io/>
- Power BI Projects overview:
  <https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview>

No external real demographic, transaction, mobility, rent or proprietary POI dataset is
bundled. If such a source is added, this register must record the exact version,
license, access date, permitted uses, retention rules, attribution and geographic
coverage before ingestion.

