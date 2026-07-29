// Rebuilds the formula-driven review workbook from pipeline outputs.
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const runtimeModules = process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES;
if (!runtimeModules) {
  throw new Error("CODEX_PRIMARY_RUNTIME_NODE_MODULES is required.");
}
const artifactToolUrl = pathToFileURL(
  path.join(runtimeModules, "@oai", "artifact-tool", "dist", "artifact_tool.mjs"),
).href;
const { SpreadsheetFile, Workbook } = await import(artifactToolUrl);

const projectRoot = process.argv[2];
const outputPath = process.argv[3];
const qaDir = process.argv[4];

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (quoted) {
      if (char === '"' && text[index + 1] === '"') {
        field += '"';
        index += 1;
      } else if (char === '"') {
        quoted = false;
      } else {
        field += char;
      }
    } else if (char === '"') {
      quoted = true;
    } else if (char === ",") {
      row.push(field);
      field = "";
    } else if (char === "\n") {
      row.push(field.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      field = "";
    } else {
      field += char;
    }
  }
  if (field.length || row.length) {
    row.push(field.replace(/\r$/, ""));
    rows.push(row);
  }
  const headers = rows[0];
  return rows.slice(1).filter((r) => r.length > 1).map((values) => {
    const result = {};
    headers.forEach((header, idx) => {
      const raw = values[idx] ?? "";
      const numeric = raw !== "" && Number.isFinite(Number(raw)) ? Number(raw) : raw;
      result[header] = numeric;
    });
    return result;
  });
}

async function loadCsv(relativePath) {
  return parseCsv(await fs.readFile(path.join(projectRoot, relativePath), "utf8"));
}

function excelColumn(number) {
  let value = number;
  let result = "";
  while (value > 0) {
    const remainder = (value - 1) % 26;
    result = String.fromCharCode(65 + remainder) + result;
    value = Math.floor((value - 1) / 26);
  }
  return result;
}

const candidates = await loadCsv("artifacts/data/candidate_scores.csv");
const scenarios = await loadCsv("artifacts/data/scenario_summaries.csv");
const selections = await loadCsv("artifacts/data/scenario_selections.csv");
const factors = await loadCsv("artifacts/data/factor_specification.csv");
const accessibility = await loadCsv("artifacts/data/candidate_accessibility.csv");
const shap = await loadCsv("artifacts/data/shap_contributions.csv");

const selectedBase = new Set(
  selections.filter((row) => row.scenario === "base").map((row) => row.candidate_id),
);
const scenarioAssumptions = {
  optimistic: { demand: 1.15, cost: 0.95 },
  base: { demand: 1.0, cost: 1.0 },
  pessimistic: { demand: 0.85, cost: 1.1 },
};

const workbook = Workbook.create();
await workbook.comments.setSelf({ displayName: "Murat Miraç Gedik" });
const dashboard = workbook.worksheets.add("Dashboard");
const evaluation = workbook.worksheets.add("Location Evaluation");
const planner = workbook.worksheets.add("Scenario Planner");
const weights = workbook.worksheets.add("Weights");
const candidateSheet = workbook.worksheets.add("Candidates");
const scenarioSheet = workbook.worksheets.add("Scenarios");
const accessibilitySheet = workbook.worksheets.add("Accessibility");
const shapSheet = workbook.worksheets.add("SHAP Explanations");
const sources = workbook.worksheets.add("Sources & License");

const palette = {
  navy: "#0B3954",
  teal: "#2A9D8F",
  orange: "#F4A261",
  red: "#E76F51",
  cream: "#F7F3E9",
  mist: "#EAF2F3",
  white: "#FFFFFF",
  ink: "#17324D",
  gray: "#607D8B",
  light: "#DCE8EA",
  input: "#DDEBFF",
};

function titleBand(sheet, title, subtitle, lastColumn) {
  sheet.showGridLines = false;
  const titleRange = sheet.getRange(`A1:${lastColumn}1`);
  titleRange.merge();
  titleRange.values = [[title]];
  titleRange.format = {
    fill: palette.navy,
    font: { bold: true, color: palette.white, size: 20 },
    verticalAlignment: "center",
  };
  titleRange.format.rowHeight = 34;
  const subtitleRange = sheet.getRange(`A2:${lastColumn}2`);
  subtitleRange.merge();
  subtitleRange.values = [[subtitle]];
  subtitleRange.format = {
    fill: palette.mist,
    font: { color: palette.ink, italic: true, size: 10 },
    verticalAlignment: "center",
  };
  subtitleRange.format.rowHeight = 28;
}

function headerStyle(range) {
  range.format = {
    fill: palette.teal,
    font: { bold: true, color: palette.white },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "outside", style: "thin", color: palette.navy },
  };
  range.format.rowHeight = 30;
}

function sectionLabel(range) {
  range.format = {
    fill: palette.navy,
    font: { bold: true, color: palette.white },
    verticalAlignment: "center",
  };
}

// Weights
titleBand(
  weights,
  "Auditable AHP Weighting",
  "Blue cells are editable. Weights are normalized automatically for scenario scoring.",
  "F",
);
weights.getRange("A4:F4").values = [[
  "Factor",
  "Definition",
  "Direction",
  "Input Weight",
  "Normalized Weight",
  "Weight Check",
]];
headerStyle(weights.getRange("A4:F4"));
factors.forEach((factor, index) => {
  const row = index + 5;
  weights.getRange(`A${row}:D${row}`).values = [[
    factor.factor,
    factor.definition,
    factor.direction,
    factor.weight,
  ]];
  weights.getRange(`E${row}`).formulas = [[`=D${row}/SUM($D$5:$D$12)`]];
  weights.getRange(`F${row}`).formulas = [[`=SUM($E$5:$E$12)`]];
});
weights.getRange("D5:D12").format.fill = palette.input;
weights.getRange("D5:F12").format.numberFormat = "0.0%";
weights.getRange("F5:F12").conditionalFormats.add("cellIs", {
  operator: "notEqual",
  formula: 1,
  format: { fill: "#FDE2E2", font: { color: "#A61B1B", bold: true } },
});
weights.getRange("A14:F16").values = [
  ["Method", "Reciprocal AHP matrix derived from the approved base weights", null, null, null, null],
  ["Consistency ratio", 0.00000000000000054, "Pass threshold", 0.1, "Status", "PASS"],
  ["Audit note", "Final score = SUMPRODUCT(normalized factor values, normalized weights) x 100", null, null, null, null],
];
weights.getRange("A14:F16").format.wrapText = true;
weights.getRange("A14:A16").format.font = { bold: true, color: palette.navy };
weights.getRange("A1:F16").format.verticalAlignment = "center";
weights.freezePanes.freezeRows(4);
weights.getRange("A:A").format.columnWidth = 26;
weights.getRange("B:B").format.columnWidth = 52;
weights.getRange("C:F").format.columnWidth = 18;

// Candidate source
titleBand(
  candidateSheet,
  "Candidate Source Table",
  "Pipeline outputs. Commercial and performance fields are deterministic synthetic data.",
  "Y",
);
const candidateHeaders = [
  "candidate_id", "candidate_name", "location_rank", "location_score",
  "predicted_sales_try_m", "sales_p10_try_m", "sales_p90_try_m",
  "accessible_pop_drive_5", "accessible_pop_drive_10", "accessible_pop_drive_15",
  "accessible_pop_walk_5", "accessible_pop_walk_10", "accessible_pop_walk_15",
  "competitor_density_3km", "poi_density_2km", "cannibalization_risk",
  "opening_cost_try_m", "annual_opex_try_m", "roi_3y", "payback_months",
  "recommendation_tier",
  ...factors.map((factor) => `${factor.factor}_normalized`),
];
candidateSheet.getRangeByIndexes(3, 0, 1, candidateHeaders.length).values = [candidateHeaders];
headerStyle(candidateSheet.getRangeByIndexes(3, 0, 1, candidateHeaders.length));
candidateSheet.getRangeByIndexes(
  4,
  0,
  candidates.length,
  candidateHeaders.length,
).values = candidates.map((row) => candidateHeaders.map((header) => row[header] ?? null));
candidateSheet.tables.add(
  `A4:${excelColumn(candidateHeaders.length)}${candidates.length + 4}`,
  true,
  "CandidateSourceTable",
);
candidateSheet.freezePanes.freezeRows(4);
candidateSheet.getRange("A:B").format.columnWidth = 24;
candidateSheet.getRange("C:AC").format.columnWidth = 14;
candidateSheet.getRange(`D5:D${candidates.length + 4}`).format.numberFormat = "0.0";
candidateSheet.getRange(`E5:G${candidates.length + 4}`).format.numberFormat = '0.0';
candidateSheet.getRange(`H5:M${candidates.length + 4}`).format.numberFormat = "#,##0";
candidateSheet.getRange(`P5:P${candidates.length + 4}`).format.numberFormat = "0.0%";
candidateSheet.getRange(`Q5:R${candidates.length + 4}`).format.numberFormat = '"TRY "0.0"m"';
candidateSheet.getRange(`S5:S${candidates.length + 4}`).format.numberFormat = "0.0%";

// Location Evaluation
titleBand(
  evaluation,
  "Formula-Based Location Evaluation",
  "Adjusted score reacts to the editable AHP weights; pipeline score remains the controlled reference.",
  "R",
);
const evalHeaders = [
  "Rank", "Candidate ID", "Candidate", "Pipeline Score", "Adjusted Score",
  "Predicted Sales", "Opening Cost", "3Y ROI", "10-min Population", "Cannibalization",
  ...factors.map((factor) => factor.factor),
];
evaluation.getRangeByIndexes(3, 0, 1, evalHeaders.length).values = [evalHeaders];
headerStyle(evaluation.getRangeByIndexes(3, 0, 1, evalHeaders.length));
candidates.forEach((_, index) => {
  const row = index + 5;
  const sourceRow = index + 5;
  evaluation.getRange(`A${row}:J${row}`).formulas = [[
    `='Candidates'!C${sourceRow}`,
    `='Candidates'!A${sourceRow}`,
    `='Candidates'!B${sourceRow}`,
    `='Candidates'!D${sourceRow}`,
    `=(${factors
      .map(
        (_, factorIndex) =>
          `${String.fromCharCode(75 + factorIndex)}${row}*'Weights'!$E$${factorIndex + 5}`,
      )
      .join("+")})*100`,
    `='Candidates'!E${sourceRow}`,
    `='Candidates'!Q${sourceRow}`,
    `='Candidates'!S${sourceRow}`,
    `='Candidates'!I${sourceRow}`,
    `='Candidates'!P${sourceRow}`,
  ]];
  factors.forEach((_, factorIndex) => {
    const candidateColumnIndex = 21 + factorIndex;
    const candidateExcelColumn = excelColumn(candidateColumnIndex + 1);
    const evalColumn = String.fromCharCode(75 + factorIndex);
    evaluation.getRange(`${evalColumn}${row}`).formulas = [[`='Candidates'!${candidateExcelColumn}${sourceRow}`]];
  });
});
evaluation.getRange(`D5:E${candidates.length + 4}`).format.numberFormat = "0.0";
evaluation.getRange(`F5:G${candidates.length + 4}`).format.numberFormat = '"TRY "0.0"m"';
evaluation.getRange(`H5:H${candidates.length + 4}`).format.numberFormat = "0.0%";
evaluation.getRange(`I5:I${candidates.length + 4}`).format.numberFormat = "#,##0";
evaluation.getRange(`J5:J${candidates.length + 4}`).format.numberFormat = "0.0%";
evaluation.getRange(`K5:R${candidates.length + 4}`).format.numberFormat = "0.000";
evaluation.getRange(`E5:E${candidates.length + 4}`).conditionalFormats.add("colorScale", {
  colors: [palette.red, "#F6D365", palette.teal],
  thresholds: ["min", "50%", "max"],
});
evaluation.getRange(`J5:J${candidates.length + 4}`).conditionalFormats.add("cellIs", {
  operator: "greaterThan",
  formula: 0.4,
  format: { fill: "#FDE2E2", font: { color: "#A61B1B", bold: true } },
});
evaluation.freezePanes.freezeRows(4);
evaluation.freezePanes.freezeColumns(3);
evaluation.getRange("A:B").format.columnWidth = 13;
evaluation.getRange("C:C").format.columnWidth = 26;
evaluation.getRange("D:R").format.columnWidth = 15;

// Scenario source
titleBand(
  scenarioSheet,
  "Scenario Source",
  "Controlled pipeline outputs and scenario assumptions.",
  "M",
);
const scenarioHeaders = [
  "scenario", "budget_try_m", "demand_multiplier", "cost_multiplier",
  "selected_store_count", "budget_used_try_m", "budget_utilization",
  "incremental_covered_population", "market_coverage_rate",
  "portfolio_sales_try_m", "portfolio_expected_ebit_try_m", "solver_status",
  "selected_candidate_ids",
];
scenarioSheet.getRange("A4:M4").values = [scenarioHeaders];
headerStyle(scenarioSheet.getRange("A4:M4"));
scenarios.forEach((row, index) => {
  const assumption = scenarioAssumptions[row.scenario];
  scenarioSheet.getRangeByIndexes(index + 4, 0, 1, scenarioHeaders.length).values = [[
    row.scenario,
    row.budget_try_m,
    assumption.demand,
    assumption.cost,
    row.selected_store_count,
    row.budget_used_try_m,
    row.budget_utilization,
    row.incremental_covered_population,
    row.market_coverage_rate,
    row.portfolio_sales_try_m,
    row.portfolio_expected_ebit_try_m,
    row.solver_status,
    row.selected_candidate_ids,
  ]];
});
scenarioSheet.getRange("B5:B7").format.numberFormat = '"TRY "0.0"m"';
scenarioSheet.getRange("C5:D7").format.numberFormat = "0%";
scenarioSheet.getRange("F5:F7").format.numberFormat = '"TRY "0.0"m"';
scenarioSheet.getRange("G5:G7").format.numberFormat = "0.0%";
scenarioSheet.getRange("H5:H7").format.numberFormat = "#,##0";
scenarioSheet.getRange("I5:I7").format.numberFormat = "0.0%";
scenarioSheet.getRange("J5:K7").format.numberFormat = '"TRY "0.0"m"';
scenarioSheet.getRange("A:M").format.columnWidth = 18;
scenarioSheet.getRange("M:M").format.columnWidth = 36;

// Scenario planner
titleBand(
  planner,
  "Expansion Scenario Planner",
  "Choose a scenario and edit the blue Yes/No selection cells. Budget and impact recalculate.",
  "L",
);
planner.getRange("A4:B8").values = [
  ["Scenario", "base"],
  ["Budget", null],
  ["Demand multiplier", null],
  ["Cost multiplier", null],
  ["Decision rule", "Budget check plus manual portfolio selection"],
];
planner.getRange("A4:A8").format = {
  fill: palette.navy,
  font: { bold: true, color: palette.white },
};
planner.getRange("B4").format.fill = palette.input;
planner.getRange("B4").dataValidation = {
  rule: { type: "list", values: ["optimistic", "base", "pessimistic"] },
};
planner.getRange("B5").formulas = [[`=INDEX('Scenarios'!$B$5:$B$7,MATCH($B$4,'Scenarios'!$A$5:$A$7,0))`]];
planner.getRange("B6").formulas = [[`=INDEX('Scenarios'!$C$5:$C$7,MATCH($B$4,'Scenarios'!$A$5:$A$7,0))`]];
planner.getRange("B7").formulas = [[`=INDEX('Scenarios'!$D$5:$D$7,MATCH($B$4,'Scenarios'!$A$5:$A$7,0))`]];
planner.getRange("B5").format.numberFormat = '"TRY "0.0"m"';
planner.getRange("B6:B7").format.numberFormat = "0%";
planner.getRange("D4:F8").values = [
  ["Portfolio KPI", "Formula Output", "Status"],
  ["Selected stores", null, null],
  ["Budget used", null, null],
  ["Adjusted sales", null, null],
  ["Incremental 10-min population*", null, "Overlap not de-duplicated in workbook"],
];
headerStyle(planner.getRange("D4:F4"));
planner.getRange("E5").formulas = [[`=COUNTIF(B12:B35,"Yes")`]];
planner.getRange("E6").formulas = [[`=SUM(F12:F35)`]];
planner.getRange("E7").formulas = [[`=SUM(E12:E35)`]];
planner.getRange("E8").formulas = [[`=SUM(G12:G35)`]];
planner.getRange("F5").formulas = [[`=IF(E5=0,"Select sites","Review")`]];
planner.getRange("F6").formulas = [[`=IF(E6<=$B$5,"PASS","OVER BUDGET")`]];
planner.getRange("E6:E7").format.numberFormat = '"TRY "0.0"m"';
planner.getRange("E8").format.numberFormat = "#,##0";
planner.getRange("F6").conditionalFormats.add("containsText", {
  text: "OVER",
  format: { fill: "#FDE2E2", font: { color: "#A61B1B", bold: true } },
});
const plannerHeaders = [
  "Rank", "Select", "Candidate", "Pipeline Score", "Adjusted Sales",
  "Adjusted Opening Cost", "10-min Population", "Cannibalization", "3Y ROI",
];
planner.getRange("A11:I11").values = [plannerHeaders];
headerStyle(planner.getRange("A11:I11"));
candidates.forEach((candidate, index) => {
  const row = index + 12;
  const sourceRow = index + 5;
  planner.getRange(`A${row}`).formulas = [[`='Candidates'!C${sourceRow}`]];
  planner.getRange(`B${row}`).values = [[selectedBase.has(candidate.candidate_id) ? "Yes" : "No"]];
  planner.getRange(`C${row}:I${row}`).formulas = [[
    `='Candidates'!B${sourceRow}`,
    `='Candidates'!D${sourceRow}`,
    `=IF(B${row}="Yes",'Candidates'!E${sourceRow}*$B$6,0)`,
    `=IF(B${row}="Yes",'Candidates'!Q${sourceRow}*$B$7,0)`,
    `=IF(B${row}="Yes",'Candidates'!I${sourceRow},0)`,
    `='Candidates'!P${sourceRow}`,
    `='Candidates'!S${sourceRow}`,
  ]];
});
planner.getRange("B12:B35").format.fill = palette.input;
planner.getRange("B12:B35").dataValidation = {
  rule: { type: "list", values: ["Yes", "No"] },
};
planner.getRange("D12:D35").format.numberFormat = "0.0";
planner.getRange("E12:F35").format.numberFormat = '"TRY "0.0"m"';
planner.getRange("G12:G35").format.numberFormat = "#,##0";
planner.getRange("H12:I35").format.numberFormat = "0.0%";
planner.getRange("A:I").format.columnWidth = 17;
planner.getRange("C:C").format.columnWidth = 26;
planner.getRange("D:D").format.columnWidth = 26;
planner.getRange("E:E").format.columnWidth = 20;
planner.getRange("F:F").format.columnWidth = 36;
planner.freezePanes.freezeRows(11);

// Accessibility raw
titleBand(
  accessibilitySheet,
  "Network Accessibility",
  "H3 adjacency network; projected centroid edge lengths; Dijkstra travel-time cutoffs.",
  "G",
);
const accessHeaders = Object.keys(accessibility[0]);
accessibilitySheet.getRangeByIndexes(3, 0, 1, accessHeaders.length).values = [accessHeaders];
headerStyle(accessibilitySheet.getRangeByIndexes(3, 0, 1, accessHeaders.length));
accessibilitySheet.getRangeByIndexes(4, 0, accessibility.length, accessHeaders.length).values =
  accessibility.map((row) => accessHeaders.map((header) => row[header]));
accessibilitySheet.tables.add(
  `A4:G${accessibility.length + 4}`,
  true,
  "AccessibilityTable",
);
accessibilitySheet.getRange("A:G").format.columnWidth = 22;
accessibilitySheet.getRange(`E5:F${accessibility.length + 4}`).format.numberFormat = "#,##0";
accessibilitySheet.freezePanes.freezeRows(4);

// SHAP explanations
titleBand(
  shapSheet,
  "SHAP Sales Explanations",
  "Feature contributions reconcile the model prediction to its expected baseline.",
  "E",
);
const shapHeaders = Object.keys(shap[0]);
shapSheet.getRange("A4:E4").values = [shapHeaders];
headerStyle(shapSheet.getRange("A4:E4"));
shapSheet.getRangeByIndexes(4, 0, shap.length, shapHeaders.length).values =
  shap.map((row) => shapHeaders.map((header) => row[header]));
shapSheet.tables.add(`A4:E${shap.length + 4}`, true, "ShapTable");
shapSheet.getRange("A:E").format.columnWidth = 26;
shapSheet.getRange(`C5:D${shap.length + 4}`).format.numberFormat = "0.000";
shapSheet.getRange(`D5:D${shap.length + 4}`).conditionalFormats.add("colorScale", {
  colors: [palette.red, palette.cream, palette.teal],
  thresholds: ["min", "50%", "max"],
});
shapSheet.freezePanes.freezeRows(4);

// Sources and licenses
titleBand(
  sources,
  "Sources, Licenses & Governance",
  "No personal data. Real coordinates frame the scenario; all commercial outcomes are synthetic.",
  "F",
);
sources.getRange("A4:F4").values = [[
  "Asset", "Use", "Origin", "License", "Access Date", "URL / Note",
]];
headerStyle(sources.getRange("A4:F4"));
const sourceRows = [
  ["Commercial features and performance", "All numeric business outcomes", "Deterministic generator", "Project MIT code; synthetic outputs", "2026-07-29", "Seed 20260729"],
  ["Candidate and store coordinates", "Scenario anchors", "Manually curated approximate public-place coordinates", "Project assumption", "2026-07-29", "Not an authoritative address register"],
  ["Base map tiles", "Interactive HTML context only", "OpenStreetMap contributors", "ODbL attribution", "2026-07-29", "https://www.openstreetmap.org/copyright"],
  ["H3", "Microzone indexing", "Uber H3", "Apache-2.0", "2026-07-29", "https://h3geo.org/docs/"],
  ["GeoPandas", "Spatial processing", "GeoPandas", "BSD-3-Clause", "2026-07-29", "https://geopandas.org/en/stable/about.html"],
  ["Shapely / GEOS", "Planar geometry", "Shapely", "BSD-3-Clause / LGPL-2.1", "2026-07-29", "https://shapely.readthedocs.io/"],
  ["Power BI PBIP guidance", "Project scaffold", "Microsoft Learn", "Documentation terms", "2026-07-29", "https://learn.microsoft.com/power-bi/developer/projects/projects-overview"],
];
sources.getRangeByIndexes(4, 0, sourceRows.length, 6).values = sourceRows;
sources.getRange("A:F").format.columnWidth = 27;
sources.getRange("B:B").format.columnWidth = 36;
sources.getRange("F:F").format.columnWidth = 58;
sources.getRange(`A5:F${sourceRows.length + 4}`).format.wrapText = true;
sources.freezePanes.freezeRows(4);
for (let index = 0; index < sourceRows.length; index += 1) {
  const cell = sources.getRange(`F${index + 5}`);
  workbook.comments.addThread(
    { cell },
    `Audit source recorded by Murat Miraç Gedik. Access date: ${sourceRows[index][4]}.`,
  );
}

// Dashboard
titleBand(
  dashboard,
  "MarmaraMart Market Expansion Control Tower",
  "Istanbul metropolitan analytical footprint | deterministic synthetic decision support | as of 2026-07-29",
  "U",
);
dashboard.getRange("A4:B4").values = [["Selected scenario", null]];
dashboard.getRange("A4").format = {
  fill: palette.navy,
  font: { bold: true, color: palette.white },
};
dashboard.getRange("B4").formulas = [[`='Scenario Planner'!B4`]];
dashboard.getRange("B4").format = { fill: palette.input, font: { bold: true, color: palette.navy } };
const cardRanges = [
  ["A6:D9", "Top Candidate", `='Location Evaluation'!C5`, null],
  ["E6:H9", "Top Location Score", `='Location Evaluation'!D5`, "0.0"],
  ["I6:L9", "Selected Stores", `='Scenario Planner'!E5`, "0"],
  ["M6:P9", "Budget Used", `='Scenario Planner'!E6`, '"TRY "0.0"m"'],
  ["Q6:U9", "Adjusted Portfolio Sales", `='Scenario Planner'!E7`, '"TRY "0.0"m"'],
];
cardRanges.forEach(([rangeAddress, label, formula, numberFormat]) => {
  const range = dashboard.getRange(rangeAddress);
  range.merge();
  range.formulas = [[formula]];
  range.format = {
    fill: palette.white,
    font: { bold: true, color: palette.navy, size: 18 },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    borders: { preset: "outside", style: "medium", color: palette.teal },
  };
  if (numberFormat) range.format.numberFormat = numberFormat;
  const startCell = rangeAddress.split(":")[0];
  const column = startCell.match(/[A-Z]+/)[0];
  const labelRow = 5;
  const endColumn = rangeAddress.split(":")[1].match(/[A-Z]+/)[0];
  const labelRange = dashboard.getRange(`${column}${labelRow}:${endColumn}${labelRow}`);
  labelRange.merge();
  labelRange.values = [[label]];
  labelRange.format = {
    fill: palette.teal,
    font: { bold: true, color: palette.white },
    horizontalAlignment: "center",
  };
});
dashboard.getRange("A11:D11").values = [["Rank", "Candidate", "Score", "Predicted Sales"]];
headerStyle(dashboard.getRange("A11:D11"));
for (let index = 0; index < 10; index += 1) {
  const row = index + 12;
  const sourceRow = index + 5;
  dashboard.getRange(`A${row}:D${row}`).formulas = [[
    `='Location Evaluation'!A${sourceRow}`,
    `='Location Evaluation'!C${sourceRow}`,
    `='Location Evaluation'!D${sourceRow}`,
    `='Location Evaluation'!F${sourceRow}`,
  ]];
}
dashboard.getRange("C12:C21").format.numberFormat = "0.0";
dashboard.getRange("D12:D21").format.numberFormat = '"TRY "0.0"m"';
dashboard.getRange("A:A").format.columnWidth = 10;
dashboard.getRange("B:B").format.columnWidth = 28;
dashboard.getRange("C:D").format.columnWidth = 17;
dashboard.getRange("A:A").format.columnWidth = 16;
dashboard.getRange("F:F").format.columnWidth = 18;
dashboard.getRange("G:G").format.columnWidth = 17;
dashboard.getRange("H:H").format.columnWidth = 22;
dashboard.getRange("F11:H14").values = [
  ["Scenario", "Budget Used", "Incremental Population"],
  ["pessimistic", scenarios.find((row) => row.scenario === "pessimistic").budget_used_try_m, scenarios.find((row) => row.scenario === "pessimistic").incremental_covered_population],
  ["base", scenarios.find((row) => row.scenario === "base").budget_used_try_m, scenarios.find((row) => row.scenario === "base").incremental_covered_population],
  ["optimistic", scenarios.find((row) => row.scenario === "optimistic").budget_used_try_m, scenarios.find((row) => row.scenario === "optimistic").incremental_covered_population],
];
headerStyle(dashboard.getRange("F11:H11"));
dashboard.getRange("G12:G14").format.numberFormat = '"TRY "0.0"m"';
dashboard.getRange("H12:H14").format.numberFormat = "#,##0";
dashboard.getRange("F16:G19").values = [
  ["Scenario", "Incremental Population"],
  ["pessimistic", scenarios.find((row) => row.scenario === "pessimistic").incremental_covered_population],
  ["base", scenarios.find((row) => row.scenario === "base").incremental_covered_population],
  ["optimistic", scenarios.find((row) => row.scenario === "optimistic").incremental_covered_population],
];
headerStyle(dashboard.getRange("F16:G16"));
dashboard.getRange("G17:G19").format.numberFormat = "#,##0";
const rankChart = dashboard.charts.add("bar", dashboard.getRange("B11:C21"));
rankChart.title = "Top candidates by controlled pipeline score";
rankChart.hasLegend = false;
rankChart.xAxis = { axisType: "textAxis" };
rankChart.yAxis = { numberFormatCode: "0" };
rankChart.setPosition("J11", "U25");
const scenarioChart = dashboard.charts.add("bar", dashboard.getRange("F11:G14"));
scenarioChart.title = "Scenario budget used (TRY m)";
scenarioChart.hasLegend = false;
scenarioChart.yAxis = { numberFormatCode: '"TRY "0.0"m"' };
scenarioChart.setPosition("A24", "I38");
const coverageChart = dashboard.charts.add("bar", dashboard.getRange("F16:G19"));
coverageChart.title = "Incremental network coverage (people)";
coverageChart.hasLegend = false;
coverageChart.yAxis = { numberFormatCode: "#,##0" };
coverageChart.setPosition("J24", "U38");
dashboard.getRange("A46:U48").merge();
dashboard.getRange("A46:U48").values = [[
  "Governance: outputs are synthetic, not investment advice, and require human review. "
  + "Workbook scenario population sums are not de-duplicated; authoritative coverage is the optimization pipeline output.",
]];
dashboard.getRange("A46:U48").format = {
  fill: palette.mist,
  font: { color: palette.ink, italic: true, size: 10 },
  wrapText: true,
  verticalAlignment: "center",
  borders: { preset: "outside", style: "thin", color: palette.light },
};
dashboard.freezePanes.freezeRows(4);

await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.mkdir(qaDir, { recursive: true });

const keyInspect = await workbook.inspect({
  kind: "table",
  range: "Dashboard!A1:U48",
  include: "values,formulas",
  tableMaxRows: 48,
  tableMaxCols: 21,
  maxChars: 9000,
});
await fs.writeFile(path.join(qaDir, "excel-dashboard-inspect.ndjson"), keyInspect.ndjson);

const formulaErrors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
await fs.writeFile(path.join(qaDir, "excel-formula-errors.ndjson"), formulaErrors.ndjson);

for (const sheetName of [
  "Dashboard",
  "Location Evaluation",
  "Scenario Planner",
  "Weights",
  "Candidates",
  "Scenarios",
  "Accessibility",
  "SHAP Explanations",
  "Sources & License",
]) {
  const preview = await workbook.render({
    sheetName,
    autoCrop: "all",
    scale: sheetName === "Dashboard" ? 1.25 : 0.8,
    format: "png",
  });
  const safeName = sheetName.toLowerCase().replaceAll(" ", "-").replaceAll("&", "and");
  await fs.writeFile(
    path.join(qaDir, `excel-${safeName}.png`),
    new Uint8Array(await preview.arrayBuffer()),
  );
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
