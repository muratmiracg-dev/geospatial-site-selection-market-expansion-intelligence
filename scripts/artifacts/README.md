# Artifact Builders

The Excel and PowerPoint builders use the ChatGPT Work primary runtime's
`@oai/artifact-tool`. They read verified CSV/JSON/PNG outputs and write user-facing
artifacts plus render/inspection evidence.

```bash
"$CODEX_PRIMARY_RUNTIME_NODE" scripts/artifacts/build_excel.mjs \
  "$PWD" \
  "$PWD/excel/Istanbul_Location_Evaluation_Scenario_Workbook.xlsx" \
  /tmp/geospatial-excel-qa

"$CODEX_PRIMARY_RUNTIME_NODE" scripts/artifacts/build_presentation.mjs \
  "$PWD" \
  "$PWD/presentation/Istanbul_Geospatial_Market_Expansion_Executive_Deck.pptx" \
  /tmp/geospatial-presentation-qa

python scripts/build_methodology_report.py
```

The PBIP starter is source-controlled directly under `powerbi/`.

