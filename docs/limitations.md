# Known Limitations and Open Risks

1. **Synthetic commercial reality:** sales, demand, rent, capex, opex, income and
   demographic values are controlled synthetic assumptions.
2. **Approximate footprint:** the boundary is analytical and not an official Istanbul
   administrative geometry.
3. **Approximate routing:** H3 adjacency is not a turn-aware, time-dependent road or
   pedestrian network.
4. **No live traffic:** congestion is a synthetic index and does not reflect hour,
   direction, incident or season.
5. **No parcel feasibility:** title, zoning, permits, frontage, entrance, parking,
   loading and accessibility are not verified.
6. **No competitor pipeline:** future openings, closures, quality and format are absent.
7. **No temporal demand:** the model has no trend, seasonality or opening ramp.
8. **Synthetic validation optimism:** model fit cannot be generalized to real stores.
9. **Relative score bounds:** min-max scoring changes when the candidate set changes.
10. **Portfolio economics:** ROI and payback are simple proxies without financing,
    tax, inflation, depreciation or option value.
11. **PBIP starter:** structure and JSON are validated, but Power BI Desktop rendering
    is not executed in the Linux build environment.
12. **CI/security workflows:** configured locally and must be observed to a terminal
    result after GitHub publication.

Open risks and ownership are maintained in `docs/risk_register.md`.

