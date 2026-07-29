// Rebuilds the executive deck from verified pipeline metrics and figures.
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
const { Presentation, PresentationFile } = await import(artifactToolUrl);

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
  return rows.slice(1).filter((values) => values.length > 1).map((values) => {
    const result = {};
    headers.forEach((header, index) => {
      const raw = values[index] ?? "";
      result[header] = raw !== "" && Number.isFinite(Number(raw)) ? Number(raw) : raw;
    });
    return result;
  });
}

async function loadCsv(relativePath) {
  return parseCsv(await fs.readFile(path.join(projectRoot, relativePath), "utf8"));
}

async function readImage(relativePath) {
  const bytes = await fs.readFile(path.join(projectRoot, relativePath));
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

const candidates = (await loadCsv("artifacts/data/candidate_scores.csv")).sort(
  (left, right) => left.location_rank - right.location_rank,
);
const scenarios = await loadCsv("artifacts/data/scenario_summaries.csv");
const selections = await loadCsv("artifacts/data/scenario_selections.csv");
const factors = await loadCsv("artifacts/data/factor_specification.csv");
const shap = await loadCsv("artifacts/data/shap_contributions.csv");
const sensitivity = await loadCsv("artifacts/data/weight_sensitivity.csv");

const top = candidates[0];
const baseSummary = scenarios.find((row) => row.scenario === "base");
const baseSelection = selections
  .filter((row) => row.scenario === "base")
  .sort((left, right) => left.priority - right.priority);
const baseIds = new Set(baseSelection.map((row) => row.candidate_id));
const baseCandidates = candidates.filter((row) => baseIds.has(row.candidate_id));
const topShap = shap
  .filter((row) => row.candidate_id === top.candidate_id)
  .sort((left, right) => Math.abs(right.shap_contribution_try_m) - Math.abs(left.shap_contribution_try_m));

const imagePaths = {
  candidateMap: "artifacts/figures/candidate_rank_map.png",
  isochrones: "artifacts/figures/network_isochrones.png",
  whiteSpace: "artifacts/figures/white_space_opportunity_map.png",
  validation: "artifacts/figures/model_validation.png",
  portfolio: "artifacts/figures/base_portfolio_map.png",
  contributions: "artifacts/figures/factor_contributions_top5.png",
};
const images = {};
for (const [key, relativePath] of Object.entries(imagePaths)) {
  images[key] = await readImage(relativePath);
}

const C = {
  navy: "#0B3954",
  teal: "#2A9D8F",
  orange: "#F4A261",
  red: "#E76F51",
  cream: "#F7F3E9",
  mist: "#EAF2F3",
  white: "#FFFFFF",
  ink: "#17324D",
  gray: "#607D8B",
  line: "#C8D8DC",
  blue: "#3A86FF",
  yellow: "#FFD166",
};

const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });
let pageNumber = 0;

function addText(slide, text, position, style = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = String(text);
  shape.text.style = {
    fontSize: style.fontSize ?? 18,
    bold: style.bold ?? false,
    color: style.color ?? C.ink,
    alignment: style.alignment ?? "left",
    italic: style.italic ?? false,
  };
  return shape;
}

function addRule(slide, left, top, width, color = C.teal, height = 5) {
  slide.shapes.add({
    geometry: "rect",
    position: { left, top, width, height },
    fill: color,
    line: { style: "solid", fill: color, width: 0 },
  });
}

function addStandardSlide(title, takeaway = "") {
  const slide = presentation.slides.add();
  pageNumber += 1;
  slide.background.fill = C.cream;
  addText(slide, title, { left: 72, top: 46, width: 1136, height: 52 }, {
    fontSize: 36,
    bold: true,
    color: C.navy,
  });
  addRule(slide, 72, 108, 118);
  if (takeaway) {
    addText(slide, takeaway, { left: 72, top: 124, width: 1110, height: 48 }, {
      fontSize: 20,
      color: C.gray,
    });
  }
  addText(
    slide,
    "Synthetic decision support • Human review required",
    { left: 72, top: 684, width: 700, height: 20 },
    { fontSize: 11, color: C.gray },
  );
  addText(
    slide,
    String(pageNumber).padStart(2, "0"),
    { left: 1160, top: 682, width: 48, height: 22 },
    { fontSize: 12, bold: true, color: C.navy, alignment: "right" },
  );
  return slide;
}

function addNotes(slide, narrative, sources) {
  slide.speakerNotes.textFrame.setText([
    ...narrative,
    "",
    "[Sources]",
    ...sources.map((source) => `- ${source}`),
  ]);
  slide.speakerNotes.setVisible(false);
}

function addImage(slide, blob, alt, position, fit = "contain") {
  return slide.images.add({
    blob,
    contentType: "image/png",
    alt,
    fit,
    position,
  });
}

function addMetric(slide, value, label, left, top, width, accent = C.teal) {
  addText(slide, value, { left, top, width, height: 58 }, {
    fontSize: 40,
    bold: true,
    color: C.navy,
  });
  addRule(slide, left, top + 62, Math.min(width * 0.55, 110), accent, 4);
  addText(slide, label, { left, top: top + 76, width, height: 52 }, {
    fontSize: 16,
    color: C.gray,
  });
}

function addTable(slide, values, position, columnWidths) {
  const table = slide.tables.add({
    rows: values.length,
    columns: values[0].length,
    left: position.left,
    top: position.top,
    width: position.width,
    height: position.height,
    values,
    columnWidths,
  });
  table.borders.assign({ style: "solid", fill: C.line, width: 1 });
  for (let column = 0; column < values[0].length; column += 1) {
    const cell = table.getCell(0, column);
    cell.fill = C.navy;
    cell.text.style = { fontSize: 16, bold: true, color: C.white };
  }
  for (let row = 1; row < values.length; row += 1) {
    for (let column = 0; column < values[0].length; column += 1) {
      const cell = table.getCell(row, column);
      cell.fill = row % 2 === 0 ? C.mist : C.white;
      cell.text.style = { fontSize: 16, color: C.ink };
    }
  }
  return table;
}

function formatPercent(value, digits = 1) {
  return `${(Number(value) * 100).toFixed(digits)}%`;
}

function formatM(value) {
  return `TRY ${Number(value).toFixed(1)}m`;
}

// 1 - Cover
{
  const slide = presentation.slides.add();
  pageNumber += 1;
  slide.background.fill = C.navy;
  addText(
    slide,
    "GEOSPATIAL DECISION INTELLIGENCE",
    { left: 80, top: 84, width: 560, height: 32 },
    { fontSize: 16, bold: true, color: C.teal },
  );
  addText(
    slide,
    "Istanbul Site Selection\n& Market Expansion",
    { left: 80, top: 154, width: 850, height: 180 },
    { fontSize: 56, bold: true, color: C.white },
  );
  addText(
    slide,
    "Network accessibility, demand prediction, explainable scoring and constrained portfolio optimization",
    { left: 82, top: 376, width: 840, height: 82 },
    { fontSize: 24, color: "#DDEBEE" },
  );
  addRule(slide, 82, 500, 168, C.orange, 7);
  addText(
    slide,
    "MarmaraMart • Executive decision-support deck • 29 July 2026",
    { left: 82, top: 534, width: 760, height: 32 },
    { fontSize: 16, color: C.white },
  );
  addText(
    slide,
    "Deterministic synthetic commercial data",
    { left: 82, top: 646, width: 480, height: 24 },
    { fontSize: 14, color: C.teal },
  );
  addNotes(
    slide,
    ["Frame the deck as a reproducible decision-support system, not a site-acquisition recommendation."],
    ["Local pipeline: artifacts/metrics/pipeline_summary.json"],
  );
}

// 2 - Executive answer
{
  const slide = addStandardSlide(
    "The base scenario funds four complementary sites",
    "The optimized portfolio stays within budget and expands network coverage, but site-level economics still require validation.",
  );
  addMetric(slide, "4", "new stores in the base portfolio", 84, 222, 230);
  addMetric(slide, formatM(baseSummary.budget_used_try_m), "of TRY 110.0m budget", 350, 222, 250, C.orange);
  addMetric(
    slide,
    Number(baseSummary.incremental_covered_population).toLocaleString("en-US"),
    "incremental people in 10-minute drive catchments",
    650,
    222,
    300,
    C.blue,
  );
  addMetric(
    slide,
    formatPercent(baseSummary.market_coverage_rate),
    "total metro population covered by existing + selected stores",
    1000,
    222,
    210,
    C.teal,
  );
  addText(
    slide,
    `${top.candidate_name} leads at ${Number(top.location_score).toFixed(1)}/100; `
      + `Sultanbeyli is the only base-selected site with positive three-year ROI in the controlled assumptions.`,
    { left: 84, top: 456, width: 1060, height: 90 },
    { fontSize: 26, bold: true, color: C.navy },
  );
  addRule(slide, 84, 576, 1060, C.orange, 2);
  addText(
    slide,
    "Decision implication: approve field validation and commercial diligence—not capital commitment.",
    { left: 84, top: 594, width: 1080, height: 44 },
    { fontSize: 20, color: C.red, bold: true },
  );
  addNotes(
    slide,
    ["Lead with the portfolio answer, then emphasize that ROI uncertainty is a deliberate decision gate."],
    [
      "Local pipeline: artifacts/data/scenario_summaries.csv",
      "Local pipeline: artifacts/data/candidate_scores.csv",
    ],
  );
}

// 3 - Spatial footprint
{
  const slide = addStandardSlide(
    "A city-scale microzone model replaces district averages",
    "5,965 H3 cells preserve local differences in demand, access, cost and competitive pressure.",
  );
  addImage(
    slide,
    images.candidateMap,
    "Istanbul analytical footprint with existing stores and candidate location scores",
    { left: 60, top: 178, width: 770, height: 450 },
    "contain",
  );
  addMetric(slide, "5,965", "H3 resolution-8 microzones", 875, 210, 250);
  addMetric(slide, "24", "candidate sites ranked", 875, 348, 250, C.orange);
  addMetric(slide, "10 / 96 / 720", "existing stores / competitors / POIs", 875, 486, 300, C.blue);
  addNotes(
    slide,
    ["Explain that the footprint is analytical—not an administrative boundary—and all coordinates are WGS84."],
    [
      "Local map: artifacts/figures/candidate_rank_map.png",
      "Local pipeline: artifacts/metrics/pipeline_summary.json",
    ],
  );
}

// 4 - Architecture
{
  const slide = addStandardSlide(
    "Four layers turn geography into an auditable decision",
    "Every output is traceable from source assumptions through network, model, score and optimization artifacts.",
  );
  const blocks = [
    ["01", "Spatial foundation", "WGS84 storage\nEPSG:32635 metrics\nH3 microzones"],
    ["02", "Demand & access", "Network isochrones\nHuff customer share\nSpatial block CV"],
    ["03", "Explainable scoring", "SHAP demand drivers\nAHP weights\nSensitivity testing"],
    ["04", "Portfolio allocation", "Budget and distance\nMaximum coverage\nScenario portfolios"],
  ];
  blocks.forEach((block, index) => {
    const left = 70 + index * 300;
    slide.shapes.add({
      geometry: "roundRect",
      position: { left, top: 222, width: 250, height: 276 },
      fill: index % 2 === 0 ? C.white : C.mist,
      line: { style: "solid", fill: C.line, width: 1.5 },
      borderRadius: "rounded-xl",
    });
    addText(slide, block[0], { left: left + 22, top: 244, width: 60, height: 34 }, {
      fontSize: 18,
      bold: true,
      color: C.teal,
    });
    addText(slide, block[1], { left: left + 22, top: 294, width: 205, height: 58 }, {
      fontSize: 24,
      bold: true,
      color: C.navy,
    });
    addText(slide, block[2], { left: left + 22, top: 378, width: 205, height: 104 }, {
      fontSize: 17,
      color: C.ink,
    });
    if (index < blocks.length - 1) {
      addText(slide, "→", { left: left + 260, top: 324, width: 34, height: 40 }, {
        fontSize: 30,
        bold: true,
        color: C.orange,
        alignment: "center",
      });
    }
  });
  addText(
    slide,
    "Audit spine  •  data contracts  •  quality gates  •  model card  •  runbook  •  monitored API",
    { left: 110, top: 548, width: 1060, height: 54 },
    { fontSize: 20, bold: true, color: C.navy, alignment: "center" },
  );
  addNotes(
    slide,
    ["Walk left to right. The audit spine is continuous across every analytical stage."],
    ["Local architecture: docs/architecture.md", "Local pipeline: src/site_intelligence/"],
  );
}

// 5 - Data and governance
{
  const slide = addStandardSlide(
    "Commercial outcomes remain synthetic by design",
    "The separation prevents personal-data exposure and keeps every business result reproducible.",
  );
  addTable(
    slide,
    [
      ["Layer", "What is used", "Governance control"],
      ["Geographic frame", "Approximate public-place coordinates; WGS84", "No address-level customer or device data"],
      ["Business attributes", "Population, income, rent, demand and sales", "Deterministic generator; seed 20260729"],
      ["Network", "H3 adjacency plus explicit bridge links", "Projected centroid distance in EPSG:32635"],
      ["Map context", "OpenStreetMap tiles in interactive HTML", "Attribution and ODbL link included"],
      ["Decision outputs", "Scores, forecasts and selected portfolios", "Human review; not investment advice"],
    ],
    { left: 76, top: 200, width: 1128, height: 352 },
    [220, 410, 498],
  );
  addText(
    slide,
    "Source/license crosswalk records access date, use, origin and license for each external component.",
    { left: 88, top: 584, width: 1050, height: 38 },
    { fontSize: 18, color: C.navy, bold: true },
  );
  addNotes(
    slide,
    ["Call out the analytical-boundary limitation and the absence of real customer data."],
    [
      "OpenStreetMap attribution: https://www.openstreetmap.org/copyright",
      "H3 license: https://h3geo.org/docs/",
      "GeoPandas license: https://geopandas.org/en/stable/about.html",
      "Shapely license: https://shapely.readthedocs.io/",
      "Local crosswalk: docs/data_source_license_crosswalk.md",
    ],
  );
}

// 6 - Network accessibility
{
  const slide = addStandardSlide(
    "Network time exposes reach that circular buffers cannot",
    `${top.candidate_name} reaches 396,396 people in 10 minutes by the modeled drive network.`,
  );
  addImage(
    slide,
    images.isochrones,
    "Five, ten and fifteen minute drive-time isochrones for the top three candidates",
    { left: 56, top: 176, width: 720, height: 454 },
    "contain",
  );
  addMetric(slide, Number(top.accessible_pop_drive_5).toLocaleString("en-US"), "5-minute drive", 815, 208, 300);
  addMetric(slide, Number(top.accessible_pop_drive_10).toLocaleString("en-US"), "10-minute drive", 815, 342, 300, C.orange);
  addMetric(slide, Number(top.accessible_pop_drive_15).toLocaleString("en-US"), "15-minute drive", 815, 476, 300, C.blue);
  addText(
    slide,
    `${formatPercent(top.euclidean_vs_network_population_gap)} fewer people than the naïve straight-line radius estimate`,
    { left: 815, top: 610, width: 360, height: 52 },
    { fontSize: 17, color: C.red, bold: true },
  );
  addNotes(
    slide,
    ["Stress that travel times come from a deterministic H3 network proxy, not live routing or current traffic."],
    [
      "Local map: artifacts/figures/network_isochrones.png",
      "Local accessibility: artifacts/data/candidate_accessibility.csv",
    ],
  );
}

// 7 - White space
{
  const whiteSpaceTop = [...candidates]
    .sort((left, right) => right.white_space_normalized - left.white_space_normalized)
    .slice(0, 4);
  const slide = addStandardSlide(
    "White-space scoring rewards uncovered demand",
    "Opportunity combines demand weight, competition headroom and an explicit penalty for existing-store coverage.",
  );
  addImage(
    slide,
    images.whiteSpace,
    "H3 white-space opportunity map with highest-ranked candidate sites",
    { left: 520, top: 174, width: 700, height: 470 },
    "contain",
  );
  addTable(
    slide,
    [
      ["Candidate", "White-space norm.", "Rank"],
      ...whiteSpaceTop.map((row) => [
        row.candidate_name,
        Number(row.white_space_normalized).toFixed(3),
        `#${row.location_rank}`,
      ]),
    ],
    { left: 66, top: 230, width: 420, height: 280 },
    [240, 120, 60],
  );
  addText(
    slide,
    "A high white-space score is necessary but not sufficient: cost, delivery and profitability remain independent gates.",
    { left: 70, top: 548, width: 410, height: 88 },
    { fontSize: 18, color: C.navy, bold: true },
  );
  addNotes(
    slide,
    ["Use the map to distinguish microzone opportunity from the final candidate rank."],
    [
      "Local map: artifacts/figures/white_space_opportunity_map.png",
      "Local H3 data: data/processed/h3_microzones.geojson",
    ],
  );
}

// 8 - Cannibalization
{
  const slide = addStandardSlide(
    "Cannibalization distinguishes growth from estate overlap",
    "The risk combines 10-minute population overlap and distance decay to the nearest existing store.",
  );
  slide.charts.add("scatter", {
    position: { left: 70, top: 190, width: 760, height: 430 },
    series: [
      {
        name: "Candidate sites",
        xValues: candidates.map((row) => Number(row.cannibalization_risk)),
        values: candidates.map((row) => Number(row.location_score)),
        marker: { symbol: "circle", size: 8 },
        fill: C.teal,
      },
    ],
    hasLegend: false,
    scatterOptions: { style: "marker" },
    xAxis: {
      title: "Cannibalization risk",
      min: 0,
      max: 1,
      numberFormatCode: "0%",
      majorGridlines: { style: "solid", fill: C.line, width: 1 },
    },
    yAxis: {
      title: "Location score",
      min: 0,
      max: 100,
      majorGridlines: { style: "solid", fill: C.line, width: 1 },
    },
    chartFill: C.white,
    plotAreaFill: C.white,
  });
  addTable(
    slide,
    [
      ["Candidate", "Risk", "Nearest store"],
      ...["C24", "C18", "C07", "C05"].map((candidateId) => {
        const row = candidates.find((candidate) => candidate.candidate_id === candidateId);
        return [row.candidate_name, formatPercent(row.cannibalization_risk), `${Number(row.nearest_existing_store_km).toFixed(1)} km`];
      }),
    ],
    { left: 870, top: 232, width: 340, height: 260 },
    [170, 75, 95],
  );
  addText(
    slide,
    "Huff diversion is reported separately, so customer-share transfer is not hidden inside one overlap metric.",
    { left: 874, top: 532, width: 330, height: 88 },
    { fontSize: 17, color: C.navy, bold: true },
  );
  addNotes(
    slide,
    ["Contrast C24 and C18 with Kagithane: similar demand, very different estate overlap."],
    [
      "Local candidates: artifacts/data/candidate_scores.csv",
      "Local method: docs/methodology.md",
    ],
  );
}

// 9 - Demand model
{
  const slide = addStandardSlide(
    "Spatial folds prevent neighboring-site leakage",
    "Five GroupKFold splits use 12 km projected blocks to reduce spatial leakage.",
  );
  addImage(
    slide,
    images.validation,
    "Out-of-fold actual versus predicted sales and residual diagnostics",
    { left: 48, top: 190, width: 820, height: 410 },
    "contain",
  );
  addMetric(slide, "3.82m", "MAE (TRY)", 910, 204, 240);
  addMetric(slide, "5.73m", "RMSE (TRY)", 910, 338, 240, C.orange);
  addMetric(slide, "0.964", "out-of-fold R²", 910, 472, 240, C.blue);
  addText(
    slide,
    "High fit is expected in a deterministic synthetic benchmark and must not be extrapolated to real stores.",
    { left: 884, top: 608, width: 300, height: 50 },
    { fontSize: 16, color: C.red, bold: true },
  );
  addNotes(
    slide,
    ["Explain that spatial validation is correctly implemented but synthetic targets make the metric optimistic."],
    [
      "Local figure: artifacts/figures/model_validation.png",
      "Local metrics: artifacts/metrics/model_metrics.json",
      "Local out-of-fold data: artifacts/data/model_out_of_fold_predictions.csv",
    ],
  );
}

// 10 - SHAP
{
  const slide = addStandardSlide(
    "Accessible population drives Ikitelli demand",
    `SHAP reconciles the ${formatM(top.shap_base_value_try_m)} model baseline to a ${formatM(top.predicted_sales_try_m)} prediction.`,
  );
  const chartRows = topShap.slice(0, 7).reverse();
  slide.charts.add("bar", {
    position: { left: 72, top: 190, width: 830, height: 430 },
    categories: chartRows.map((row) => row.feature.replaceAll("_", " ")),
    series: [
      {
        name: "Positive",
        values: chartRows.map((row) => Math.max(0, Number(row.shap_contribution_try_m))),
        fill: C.teal,
      },
      {
        name: "Negative",
        values: chartRows.map((row) => Math.min(0, Number(row.shap_contribution_try_m))),
        fill: C.red,
      },
    ],
    barOptions: { direction: "bar", grouping: "stacked", gapWidth: 45 },
    hasLegend: true,
    legend: { position: "bottom", textStyle: { fontSize: 14, fill: C.gray } },
    xAxis: {
      numberFormatCode: "0.0",
      majorGridlines: { style: "solid", fill: C.line, width: 1 },
      title: "SHAP contribution (TRY m)",
    },
    yAxis: { textStyle: { fontSize: 14, fill: C.ink } },
    chartFill: C.white,
    plotAreaFill: C.white,
  });
  addMetric(slide, "+17.4m", "10-minute population", 952, 238, 230);
  addMetric(slide, "+3.1m", "walkability", 952, 376, 230, C.blue);
  addMetric(slide, "-1.2m", "cannibalization term", 952, 514, 230, C.red);
  addNotes(
    slide,
    ["SHAP explains the demand model, while AHP contributions explain the final location score."],
    ["Local SHAP: artifacts/data/shap_contributions.csv"],
  );
}

// 11 - MCDA
{
  const slide = addStandardSlide(
    "AHP makes the score inspectable",
    "Market potential receives 23% weight; accessibility, profitability and white space jointly shape the decision.",
  );
  slide.charts.add("bar", {
    position: { left: 64, top: 190, width: 430, height: 430 },
    categories: factors.map((row) => row.factor.replaceAll("_", " ")),
    series: [{ name: "Weight", values: factors.map((row) => Number(row.weight) * 100), fill: C.teal }],
    barOptions: { direction: "bar", grouping: "clustered", gapWidth: 48 },
    hasLegend: false,
    xAxis: { min: 0, max: 25, numberFormatCode: "0", majorGridlines: null, title: "Weight (%)" },
    yAxis: { textStyle: { fontSize: 13, fill: C.ink } },
    dataLabels: {
      showValue: true,
      position: "outEnd",
      valuesFormatCode: "0",
      textStyle: { fontSize: 13, fill: C.navy },
    },
    chartFill: C.white,
    plotAreaFill: C.white,
  });
  addImage(
    slide,
    images.contributions,
    "Stacked factor contributions for the five highest-ranked candidates",
    { left: 510, top: 190, width: 710, height: 430 },
    "contain",
  );
  addText(
    slide,
    "AHP consistency ratio: effectively 0.000 • threshold < 0.10 • PASS",
    { left: 76, top: 630, width: 1040, height: 32 },
    { fontSize: 17, color: C.navy, bold: true },
  );
  addNotes(
    slide,
    ["Clarify that exact reciprocal ratios make the pairwise matrix fully consistent by construction."],
    [
      "Local factor specification: artifacts/data/factor_specification.csv",
      "Local contributions: artifacts/data/score_contributions.csv",
      "Local AHP check: artifacts/metrics/ahp_consistency.json",
    ],
  );
}

// 12 - Sensitivity
{
  const slide = addStandardSlide(
    "Ikitelli stays top-five across weight samples",
    "750 Dirichlet draws quantify rank stability around the approved AHP weights.",
  );
  const stable = sensitivity.slice(0, 6);
  slide.charts.add("bar", {
    position: { left: 70, top: 194, width: 660, height: 420 },
    categories: stable.map((row) => row.candidate_id),
    series: [{
      name: "Top-five probability",
      values: stable.map((row) => Math.round(Number(row.top_5_probability) * 1000) / 10),
      fill: C.teal,
    }],
    barOptions: { direction: "column", grouping: "clustered", gapWidth: 60 },
    hasLegend: false,
    yAxis: {
      min: 0,
      max: 100,
      numberFormatCode: "0",
      title: "Top-five probability (%)",
      majorGridlines: { style: "solid", fill: C.line, width: 1 },
    },
    xAxis: { textStyle: { fontSize: 16, fill: C.ink } },
    dataLabels: {
      showValue: true,
      position: "outEnd",
      valuesFormatCode: "0.0",
      textStyle: { fontSize: 14, fill: C.navy, bold: true },
    },
    chartFill: C.white,
    plotAreaFill: C.white,
  });
  addTable(
    slide,
    [
      ["Candidate", "Mean rank", "P05–P95", "#1 probability"],
      ...stable.slice(0, 5).map((row) => [
        row.candidate_id,
        Number(row.mean_rank).toFixed(2),
        `${Number(row.rank_p05).toFixed(0)}–${Number(row.rank_p95).toFixed(0)}`,
        formatPercent(row.rank_1_probability),
      ]),
    ],
    { left: 770, top: 222, width: 430, height: 330 },
    [115, 100, 100, 115],
  );
  addText(
    slide,
    "Stable does not mean investment-ready; it means the ranking is not fragile to modest weight changes.",
    { left: 784, top: 584, width: 400, height: 62 },
    { fontSize: 17, color: C.red, bold: true },
  );
  addNotes(
    slide,
    ["Separate ranking robustness from real-world validity."],
    ["Local sensitivity: artifacts/data/weight_sensitivity.csv"],
  );
}

// 13 - Optimization
{
  const slide = addStandardSlide(
    "Optimization balances economics and coverage",
    "Binary location-allocation chooses sites while preventing infeasible distance and budget combinations.",
  );
  addText(slide, "MAXIMIZE", { left: 84, top: 220, width: 180, height: 34 }, {
    fontSize: 18,
    bold: true,
    color: C.teal,
  });
  addText(
    slide,
    "expected EBIT  +  location score  +  uncovered population  −  cannibalization penalty",
    { left: 84, top: 270, width: 1080, height: 64 },
    { fontSize: 28, bold: true, color: C.navy, alignment: "center" },
  );
  addRule(slide, 160, 354, 960, C.line, 2);
  const constraints = [
    ["Budget", "TRY 75m / 110m / 150m by scenario"],
    ["Portfolio capacity", "Maximum 4 / 5 / 6 stores"],
    ["Minimum distance", "4.5 km pairwise conflict constraint"],
    ["Coverage", "10-minute network catchments counted once"],
  ];
  constraints.forEach((item, index) => {
    const left = 78 + (index % 2) * 580;
    const topPosition = 392 + Math.floor(index / 2) * 112;
    addText(slide, item[0], { left, top: topPosition, width: 210, height: 30 }, {
      fontSize: 20,
      bold: true,
      color: C.orange,
    });
    addText(slide, item[1], { left, top: topPosition + 40, width: 500, height: 52 }, {
      fontSize: 18,
      color: C.ink,
    });
  });
  addNotes(
    slide,
    ["Explain that CBC solves the checked-in deterministic binary program to optimality for all three scenarios."],
    [
      "Local optimizer: src/site_intelligence/optimization.py",
      "Local scenario results: artifacts/data/scenario_summaries.csv",
    ],
  );
}

// 14 - Scenarios
{
  const slide = addStandardSlide(
    "Downside economics turn negative",
    "The pessimistic portfolio stays feasible but produces -TRY 2.1m expected EBIT under controlled assumptions.",
  );
  slide.charts.add("bar", {
    position: { left: 66, top: 200, width: 520, height: 410 },
    categories: ["Pessimistic", "Base", "Optimistic"],
    series: [{
      name: "Incremental population",
      values: ["pessimistic", "base", "optimistic"].map(
        (name) => Number(scenarios.find((row) => row.scenario === name).incremental_covered_population),
      ),
      fill: C.blue,
    }],
    barOptions: { direction: "column", grouping: "clustered", gapWidth: 62 },
    hasLegend: false,
    yAxis: { numberFormatCode: "#,##0", majorGridlines: { style: "solid", fill: C.line, width: 1 } },
    dataLabels: { showValue: true, position: "outEnd", textStyle: { fontSize: 13, fill: C.navy } },
    chartFill: C.white,
    plotAreaFill: C.white,
  });
  addTable(
    slide,
    [
      ["Scenario", "Sites", "Budget used", "Sales", "Expected EBIT", "Coverage"],
      ...["pessimistic", "base", "optimistic"].map((name) => {
        const row = scenarios.find((item) => item.scenario === name);
        return [
          name[0].toUpperCase() + name.slice(1),
          String(row.selected_store_count),
          formatM(row.budget_used_try_m),
          formatM(row.portfolio_sales_try_m),
          formatM(row.portfolio_expected_ebit_try_m),
          formatPercent(row.market_coverage_rate),
        ];
      }),
    ],
    { left: 600, top: 226, width: 610, height: 270 },
    [100, 65, 105, 100, 130, 110],
  );
  addText(
    slide,
    "Scenario outputs are comparative stress tests—not probability-weighted forecasts.",
    { left: 640, top: 542, width: 540, height: 60 },
    { fontSize: 18, color: C.red, bold: true },
  );
  addNotes(
    slide,
    ["Use the negative pessimistic EBIT to reinforce the commercial validation gate."],
    ["Local scenarios: artifacts/data/scenario_summaries.csv"],
  );
}

// 15 - Base portfolio
{
  const slide = addStandardSlide(
    "Four sites anchor the base portfolio",
    "Ikitelli, Sultanbeyli, Sancaktepe and Eyupsultan form the optimized TRY 93.4m portfolio.",
  );
  addImage(
    slide,
    images.portfolio,
    "Existing stores and four base scenario recommended locations",
    { left: 48, top: 176, width: 730, height: 470 },
    "contain",
  );
  addTable(
    slide,
    [
      ["Priority", "Site", "Score", "Cost", "Risk"],
      ...baseSelection.map((selected) => {
        const candidate = candidates.find((row) => row.candidate_id === selected.candidate_id);
        return [
          `P${selected.priority}`,
          candidate.candidate_name,
          Number(candidate.location_score).toFixed(1),
          formatM(candidate.opening_cost_try_m),
          formatPercent(candidate.cannibalization_risk),
        ];
      }),
    ],
    { left: 792, top: 226, width: 420, height: 290 },
    [65, 155, 65, 75, 60],
  );
  addText(
    slide,
    "Eyupsultan contributes reach but carries 34.9% cannibalization risk; validate estate overlap before approval.",
    { left: 810, top: 558, width: 380, height: 76 },
    { fontSize: 18, color: C.red, bold: true },
  );
  addNotes(
    slide,
    ["Explain why optimization can include a site with higher cannibalization: portfolio-level coverage and score trade-offs."],
    [
      "Local map: artifacts/figures/base_portfolio_map.png",
      "Local selections: artifacts/data/scenario_selections.csv",
    ],
  );
}

// 16 - Economics
{
  const slide = addStandardSlide(
    "Demand strength does not ensure site economics",
    "Three of four base-selected sites have negative controlled three-year ROI before field validation.",
  );
  slide.charts.add("bar", {
    position: { left: 70, top: 196, width: 720, height: 420 },
    categories: baseCandidates.map((row) => row.candidate_id),
    series: [
      {
        name: "Three-year ROI",
        values: baseCandidates.map((row) => Number(row.roi_3y)),
        fill: C.orange,
        points: baseCandidates.map((row, index) => ({
          idx: index,
          fill: Number(row.roi_3y) >= 0 ? C.teal : C.red,
        })),
      },
    ],
    barOptions: { direction: "column", grouping: "clustered", gapWidth: 60, varyColors: true },
    hasLegend: false,
    yAxis: { min: -0.3, max: 0.25, numberFormatCode: "0%", majorGridlines: { style: "solid", fill: C.line, width: 1 } },
    chartFill: C.white,
    plotAreaFill: C.white,
  });
  addText(
    slide,
    baseCandidates
      .map((row) => `${row.candidate_id} ${formatPercent(row.roi_3y)}`)
      .join("  •  "),
    { left: 100, top: 608, width: 660, height: 28 },
    { fontSize: 15, color: C.navy, bold: true, alignment: "center" },
  );
  addMetric(slide, formatM(baseSummary.portfolio_expected_ebit_try_m), "base portfolio expected EBIT", 850, 224, 300);
  addMetric(slide, "42.9 mo", "Ikitelli payback proxy", 850, 376, 300, C.orange);
  addText(
    slide,
    "Required validation: binding rent quote, fit-out capex, staffing plan, unit margin and opening ramp.",
    { left: 850, top: 532, width: 340, height: 94 },
    { fontSize: 18, color: C.navy, bold: true },
  );
  addNotes(
    slide,
    ["The portfolio can be positive in aggregate while individual sites miss the three-year hurdle."],
    [
      "Local candidates: artifacts/data/candidate_scores.csv",
      "Local scenarios: artifacts/data/scenario_summaries.csv",
    ],
  );
}

// 17 - Governance and monitoring
{
  const slide = addStandardSlide(
    "Operational controls keep the decision system reviewable",
    "Data quality, model drift, API health and incident ownership are treated as production concerns.",
  );
  const bands = [
    ["DATA", "46 checks • 44 pass • 2 non-critical spatial-coverage warnings", "Geometry, CRS, duplicates, missing values and joins"],
    ["MODEL", "Spatial CV • SHAP • weight sensitivity • model card", "Monitor residual drift, rank stability and feature distributions"],
    ["SERVICE", "FastAPI • Prometheus • Grafana • runbook", "Health, latency, errors, artifact freshness and rollback"],
  ];
  bands.forEach((band, index) => {
    const topPosition = 202 + index * 130;
    addText(slide, band[0], { left: 84, top: topPosition, width: 130, height: 36 }, {
      fontSize: 18,
      bold: true,
      color: index === 0 ? C.teal : index === 1 ? C.orange : C.blue,
    });
    addText(slide, band[1], { left: 230, top: topPosition - 4, width: 900, height: 42 }, {
      fontSize: 24,
      bold: true,
      color: C.navy,
    });
    addText(slide, band[2], { left: 230, top: topPosition + 48, width: 900, height: 38 }, {
      fontSize: 17,
      color: C.gray,
    });
    addRule(slide, 84, topPosition + 106, 1050, C.line, 1);
  });
  addText(
    slide,
    "Open warnings: 7 synthetic competitors and 16 synthetic POIs fall outside the analytical footprint; no critical failures.",
    { left: 84, top: 604, width: 1060, height: 42 },
    { fontSize: 17, color: C.red, bold: true },
  );
  addNotes(
    slide,
    ["The warnings are retained because transparent scope mismatch is preferable to silently clipping generated points."],
    [
      "Local QA: artifacts/qa/data_quality_checks.csv",
      "Local runbook: docs/monitoring_runbook.md",
      "Local incident response: docs/incident_response.md",
    ],
  );
}

// 18 - Decision gates
{
  const slide = addStandardSlide(
    "Four gates precede capital approval",
    "The analytical portfolio is ready for review; publication and investment decisions remain explicitly separate.",
  );
  const gates = [
    ["01", "Site survey", "Validate visibility, footfall, access, parcel constraints and address accuracy."],
    ["02", "Independent routing", "Rebuild drive/walk isochrones with a current road network and live traffic assumptions."],
    ["03", "Commercial diligence", "Replace synthetic rent, capex, opex, margin and ramp inputs with binding evidence."],
    ["04", "Investment committee", "Review portfolio synergies, downside case, cannibalization and implementation capacity."],
  ];
  gates.forEach((gate, index) => {
    const topPosition = 190 + index * 104;
    addText(slide, gate[0], { left: 84, top: topPosition, width: 70, height: 36 }, {
      fontSize: 20,
      bold: true,
      color: C.teal,
    });
    addText(slide, gate[1], { left: 170, top: topPosition - 2, width: 270, height: 38 }, {
      fontSize: 24,
      bold: true,
      color: C.navy,
    });
    addText(slide, gate[2], { left: 460, top: topPosition, width: 700, height: 58 }, {
      fontSize: 17,
      color: C.ink,
    });
    addRule(slide, 84, topPosition + 78, 1080, C.line, 1);
  });
  addText(
    slide,
    "PROJECT STATUS  •  READY FOR REVIEW  •  NOT PUBLISHED",
    { left: 84, top: 620, width: 1080, height: 40 },
    { fontSize: 22, bold: true, color: C.orange, alignment: "center" },
  );
  addNotes(
    slide,
    ["Close by asking for review of the analytical assumptions and deliverables, not approval to publish or invest."],
    [
      "Local limitations: docs/limitations.md",
      "Local risk register: docs/risk_register.md",
      "Local project status: docs/review_handoff.md",
    ],
  );
}

await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.mkdir(qaDir, { recursive: true });
for (const [index, slide] of presentation.slides.items.entries()) {
  const stem = `slide-${String(index + 1).padStart(2, "0")}`;
  const png = await presentation.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(path.join(qaDir, `${stem}.png`), new Uint8Array(await png.arrayBuffer()));
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(qaDir, `${stem}.layout.json`), await layout.text());
}
const montage = await presentation.export({ format: "webp", montage: true, scale: 1 });
await fs.writeFile(path.join(qaDir, "deck-montage.webp"), new Uint8Array(await montage.arrayBuffer()));
const inspection = await presentation.inspect({
  kind: "slide,textbox,shape,image,table,chart,notes",
  maxChars: 20000,
});
await fs.writeFile(path.join(qaDir, "deck-inspection.ndjson"), inspection.ndjson);
const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(outputPath);
