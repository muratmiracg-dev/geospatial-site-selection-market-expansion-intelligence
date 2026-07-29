"""Build the professional methodology and governance PDF from pipeline outputs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    LongTable,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "report" / "Istanbul_Geospatial_Site_Selection_Methodology_Governance_Report.pdf"

NAVY = colors.HexColor("#0B3954")
TEAL = colors.HexColor("#2A9D8F")
ORANGE = colors.HexColor("#F4A261")
CREAM = colors.HexColor("#F8F5ED")
MIST = colors.HexColor("#EAF2F3")
INK = colors.HexColor("#183B56")
GRAY = colors.HexColor("#607D8B")
RED = colors.HexColor("#E76F51")
LINE = colors.HexColor("#CBD9DD")
WHITE = colors.white


def register_fonts() -> tuple[str, str]:
    regular = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    bold = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("ProjectSans", str(regular)))
        pdfmetrics.registerFont(TTFont("ProjectSans-Bold", str(bold)))
        return "ProjectSans", "ProjectSans-Bold"
    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = register_fonts()


class ProjectDocTemplate(BaseDocTemplate):
    def __init__(self, filename: Path) -> None:
        super().__init__(
            str(filename),
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=20 * mm,
            bottomMargin=18 * mm,
            title="Istanbul Geospatial Site Selection - Methodology and Governance",
            author="Murat Mirac Gedik",
            subject="Synthetic decision-support methodology and governance",
        )
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        self.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=draw_page)])


def draw_page(canvas, doc) -> None:  # type: ignore[no-untyped-def]
    canvas.saveState()
    width, height = A4
    if doc.page == 1:
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, width, height, stroke=0, fill=1)
        canvas.setFillColor(TEAL)
        canvas.rect(0, 0, width, 14 * mm, stroke=0, fill=1)
    else:
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.6)
        canvas.line(18 * mm, height - 14 * mm, width - 18 * mm, height - 14 * mm)
        canvas.setFont(FONT, 7.5)
        canvas.setFillColor(GRAY)
        canvas.drawString(
            18 * mm, height - 10.5 * mm, "MarmaraMart Geospatial Decision Intelligence"
        )
        canvas.drawRightString(width - 18 * mm, height - 10.5 * mm, "Methodology & Governance")
        canvas.drawString(
            18 * mm, 9 * mm, "Deterministic synthetic commercial data - Human review required"
        )
        canvas.setFont(FONT_BOLD, 8)
        canvas.setFillColor(NAVY)
        canvas.drawRightString(width - 18 * mm, 9 * mm, f"{doc.page:02d}")
    canvas.restoreState()


styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        "CoverKicker",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=10,
        leading=13,
        textColor=TEAL,
        spaceAfter=12,
        uppercase=True,
    )
)
styles.add(
    ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        fontName=FONT_BOLD,
        fontSize=30,
        leading=36,
        textColor=WHITE,
        alignment=TA_LEFT,
        spaceAfter=18,
    )
)
styles.add(
    ParagraphStyle(
        "CoverSub",
        parent=styles["Normal"],
        fontName=FONT,
        fontSize=13,
        leading=19,
        textColor=colors.HexColor("#DCEAF0"),
        spaceAfter=15,
    )
)
styles.add(
    ParagraphStyle(
        "H1Project",
        parent=styles["Heading1"],
        fontName=FONT_BOLD,
        fontSize=21,
        leading=26,
        textColor=NAVY,
        spaceAfter=9,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        "H2Project",
        parent=styles["Heading2"],
        fontName=FONT_BOLD,
        fontSize=13,
        leading=17,
        textColor=TEAL,
        spaceBefore=7,
        spaceAfter=5,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        "BodyProject",
        parent=styles["BodyText"],
        fontName=FONT,
        fontSize=9.2,
        leading=13.5,
        textColor=INK,
        spaceAfter=6,
    )
)
styles.add(
    ParagraphStyle(
        "SmallProject",
        parent=styles["BodyText"],
        fontName=FONT,
        fontSize=7.8,
        leading=10.5,
        textColor=GRAY,
        spaceAfter=4,
    )
)
styles.add(
    ParagraphStyle(
        "Callout",
        parent=styles["BodyText"],
        fontName=FONT_BOLD,
        fontSize=10,
        leading=14,
        textColor=NAVY,
        leftIndent=4,
        rightIndent=4,
    )
)
styles.add(
    ParagraphStyle(
        "Metric",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=17,
        leading=20,
        textColor=NAVY,
        alignment=TA_CENTER,
    )
)
styles.add(
    ParagraphStyle(
        "MetricLabel",
        parent=styles["Normal"],
        fontName=FONT,
        fontSize=7.4,
        leading=9.5,
        textColor=GRAY,
        alignment=TA_CENTER,
    )
)


def p(text: str, style: str = "BodyProject") -> Paragraph:
    return Paragraph(text, styles[style])


def bullets(items: list[str]) -> list[Paragraph]:
    return [
        Paragraph(
            f"- {item}",
            ParagraphStyle("BulletProject", parent=styles["BodyProject"], leftIndent=10),
        )
        for item in items
    ]


def section(title: str, number: str) -> list[object]:
    return [
        Paragraph(f"{number} / {title}", styles["H1Project"]),
        Table(
            [[None]],
            colWidths=[25 * mm],
            rowHeights=[1.5 * mm],
            style=[("BACKGROUND", (0, 0), (-1, -1), TEAL)],
        ),
        Spacer(1, 5 * mm),
    ]


def styled_table(data: list[list[object]], widths: list[float] | None = None) -> LongTable:
    converted = [
        [cell if isinstance(cell, Paragraph) else p(str(cell), "SmallProject") for cell in row]
        for row in data
    ]
    table = LongTable(converted, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, MIST]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def metric_strip(metrics: list[tuple[str, str]]) -> Table:
    cells = [
        [p(value, "Metric") for value, _ in metrics],
        [p(label, "MetricLabel") for _, label in metrics],
    ]
    table = Table(
        cells, colWidths=[175 * mm / len(metrics)] * len(metrics), rowHeights=[9 * mm, 10 * mm]
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), MIST),
                ("BOX", (0, 0), (-1, -1), 0.7, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, WHITE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def callout(text: str, color: colors.Color = TEAL) -> Table:
    table = Table([[p(text, "Callout")]], colWidths=[175 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), MIST),
                ("LINEBEFORE", (0, 0), (0, -1), 4, color),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def figure(relative: str, max_height_mm: float = 92, caption: str = "") -> list[object]:
    path = ROOT / relative
    with PILImage.open(path) as source:
        width_px, height_px = source.size
    max_width = 175 * mm
    max_height = max_height_mm * mm
    scale = min(max_width / width_px, max_height / height_px)
    image = Image(str(path), width=width_px * scale, height=height_px * scale)
    image.hAlign = "CENTER"
    items: list[object] = [image]
    if caption:
        items.extend([Spacer(1, 2 * mm), p(caption, "SmallProject")])
    return items


def page(story: list[object], title: str, number: str) -> None:
    if story:
        story.append(PageBreak())
    story.extend(section(title, number))


def build() -> None:
    summary = json.loads((ROOT / "artifacts/metrics/pipeline_summary.json").read_text())
    candidates = pd.read_csv(ROOT / "artifacts/data/candidate_scores.csv").sort_values(
        "location_rank"
    )
    factors = pd.read_csv(ROOT / "artifacts/data/factor_specification.csv")
    scenarios = pd.read_csv(ROOT / "artifacts/data/scenario_summaries.csv")
    selections = pd.read_csv(ROOT / "artifacts/data/scenario_selections.csv")
    quality = pd.read_csv(ROOT / "artifacts/qa/data_quality_checks.csv")
    sensitivity = pd.read_csv(ROOT / "artifacts/data/weight_sensitivity.csv")
    top = candidates.iloc[0]
    base_ids = selections.loc[selections["scenario"] == "base", "candidate_id"].tolist()
    base_candidates = candidates[candidates["candidate_id"].isin(base_ids)].copy()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    story: list[object] = []

    story.extend(
        [
            Spacer(1, 35 * mm),
            p("GEOSPATIAL DECISION INTELLIGENCE", "CoverKicker"),
            p("Istanbul Site Selection<br/>& Market Expansion", "CoverTitle"),
            p(
                "Detailed methodology, validation, governance and operating controls for an "
                "auditable synthetic retail decision-support platform.",
                "CoverSub",
            ),
            Spacer(1, 10 * mm),
            Table(
                [[None]],
                colWidths=[38 * mm],
                rowHeights=[2 * mm],
                style=[("BACKGROUND", (0, 0), (-1, -1), ORANGE)],
            ),
            Spacer(1, 11 * mm),
            p(
                "<b>MarmaraMart</b> - fictional retail chain<br/>Version 1.0.0 - 29 July 2026",
                "CoverSub",
            ),
            Spacer(1, 30 * mm),
            callout(
                "All commercial outcomes are deterministic synthetic data. No personal or sensitive "
                "data is used. This report is decision support, not investment advice.",
                ORANGE,
            ),
            Spacer(1, 14 * mm),
            p("PROJECT STATUS  /  READY FOR REVIEW - NOT PUBLISHED", "CoverKicker"),
        ]
    )

    page(story, "Executive summary", "01")
    story.extend(
        [
            p(
                "The platform converts Istanbul retail expansion from a radius-based map exercise "
                "into an auditable site-and-portfolio decision. It links network accessibility, "
                "microzone demand, competitive pressure, customer diversion, economics and execution "
                "risk, then separates transparent site ranking from constrained portfolio allocation."
            ),
            metric_strip(
                [
                    ("5,965", "H3 resolution-8 microzones"),
                    ("24", "candidate locations"),
                    ("81.236", "top C24 score / 100"),
                    ("4", "base selected sites"),
                ]
            ),
            Spacer(1, 5 * mm),
            metric_strip(
                [
                    ("TRY 93.382m", "base budget used"),
                    ("1,329,291", "incremental 10-minute population"),
                    ("23.125%", "total modeled market coverage"),
                    ("TRY 28.826m", "base expected portfolio EBIT"),
                ]
            ),
            Spacer(1, 7 * mm),
            callout(
                "Analytical recommendation: approve field validation and commercial diligence for "
                "C24 Ikitelli, C18 Sultanbeyli, C17 Sancaktepe and C07 Eyupsultan. Do not approve "
                "capital from these outputs alone.",
                ORANGE,
            ),
            Spacer(1, 5 * mm),
            p(
                "C24 leads the location score at 81.236/100 and has low modeled cannibalization, but "
                "its controlled three-year ROI is -16.0%. C18 is the only base-selected site with "
                "positive controlled three-year ROI (+14.7%). The gap between demand strength and "
                "site economics is an explicit decision gate."
            ),
        ]
    )

    page(story, "Contents and review path", "02")
    contents = [
        ["Section", "Decision question"],
        ["03-05", "How is the system designed, sourced and spatially controlled?"],
        ["06-09", "How are access, competition, white space and cannibalization modeled?"],
        ["10-13", "How are demand, SHAP, AHP and sensitivity validated?"],
        ["14-16", "How does optimization choose a portfolio and stress economics?"],
        ["17-20", "How are API, PostGIS, BI, governance and security operationalized?"],
        ["21-23", "What are the risks, limitations, licenses and review gates?"],
        ["Appendices", "Which artifacts, fields and exact metrics support the decision?"],
    ]
    story.extend(
        [
            styled_table(contents, [30 * mm, 145 * mm]),
            Spacer(1, 8 * mm),
            p("Recommended review sequence", "H2Project"),
            *bullets(
                [
                    "Challenge the decision framing and synthetic-data boundary.",
                    "Inspect network reach before accepting any population number.",
                    "Review SHAP demand explanations separately from AHP score contributions.",
                    "Test score weight sensitivity and scenario constraints.",
                    "Validate individual site economics before considering portfolio synergy.",
                    "Complete field, routing, legal and commercial diligence before capital approval.",
                ]
            ),
            Spacer(1, 8 * mm),
            callout(
                "Traceability spine: configuration -> processed data -> quality ledger -> model/OOF "
                "predictions -> SHAP -> AHP contributions -> optimizer selection -> dashboard/report."
            ),
        ]
    )

    page(story, "Decision architecture", "03")
    architecture = [
        ["Layer", "Primary method", "Audit evidence"],
        [
            "Spatial foundation",
            "WGS84, EPSG:32635, H3 resolution 8",
            "GeoJSON, CRS and geometry checks",
        ],
        [
            "Demand and access",
            "H3 network, Huff/gravity, spatial CV",
            "catchments, OOF predictions, SHAP",
        ],
        [
            "Explainable score",
            "AHP plus direction-adjusted min-max",
            "weights and factor contributions",
        ],
        [
            "Portfolio allocation",
            "binary maximum coverage",
            "solver status, budget, distance, coverage",
        ],
        ["Delivery", "API, PostGIS, maps, Excel, PBIP", "contracts, views, runbook and manifest"],
    ]
    story.extend(
        [
            styled_table(architecture, [33 * mm, 64 * mm, 78 * mm]),
            Spacer(1, 6 * mm),
            p(
                "Site rank and portfolio choice are intentionally distinct. A high-ranked candidate "
                "can be excluded because of overlap, distance conflict, capacity or budget. Conversely, "
                "a lower-ranked site can improve incremental coverage at portfolio level."
            ),
            p("Component responsibilities", "H2Project"),
            *bullets(
                [
                    "Geo quality gates stop invalid geometry or CRS before analytical joins.",
                    "Network catchments count unique cells reached within time thresholds.",
                    "Demand predictions and score contributions are persisted separately.",
                    "Optimization consumes approved scenario assumptions and exposes terminal status.",
                    "Every user-facing artifact is generated from pipeline output rather than typed KPIs.",
                ]
            ),
        ]
    )

    page(story, "Data provenance and synthetic design", "04")
    story.extend(
        [
            p(
                "The project uses approximate public-place coordinates only to frame a metropolitan "
                "analysis. Population, income, purchasing power, rent, traffic, store performance, "
                "sales, EBIT and investment costs are generated deterministically with seed 20260729."
            ),
            styled_table(
                [
                    ["Layer", "Provenance", "Privacy / governance"],
                    [
                        "Geographic anchors",
                        "Approximate public places",
                        "No customer or household address",
                    ],
                    ["Commercial outcomes", "Deterministic generator", "Synthetic; reproducible"],
                    [
                        "Network indicators",
                        "H3 geometry plus synthetic indices",
                        "No device traces",
                    ],
                    ["Basemap", "OpenStreetMap tiles", "Attribution included"],
                    ["Decision outputs", "Local pipeline", "Human review required"],
                ],
                [40 * mm, 62 * mm, 73 * mm],
            ),
            Spacer(1, 6 * mm),
            callout(
                "The absence of personal data removes person-level privacy exposure, but geographic "
                "allocation bias remains possible through income, centrality and current-estate proxies.",
                ORANGE,
            ),
            Spacer(1, 5 * mm),
            p(
                "The analytical footprint is a project-specific approximation and must not be "
                "represented as an official administrative boundary. Exact parcel coordinates are a "
                "field-validation input, not a model output."
            ),
        ]
    )

    page(story, "CRS, geometry and H3 microzones", "05")
    story.extend(
        [
            p(
                "All exchange geometry is stored in WGS84 (EPSG:4326). Distance and area calculations "
                "use UTM zone 35N (EPSG:32635). This prevents the common error of calculating meters "
                "directly from longitude/latitude degrees."
            ),
            metric_strip(
                [
                    ("EPSG:4326", "storage / web exchange"),
                    ("EPSG:32635", "distance and area"),
                    ("H3 r8", "microzone index"),
                    ("5,965", "cells in footprint"),
                ]
            ),
            Spacer(1, 5 * mm),
            *figure(
                "artifacts/figures/candidate_rank_map.png",
                105,
                "Analytical footprint, current estate and ranked candidate sites. The footprint is "
                "analytical, not an official district boundary.",
            ),
        ]
    )

    page(story, "Data quality controls", "06")
    warning_rows = quality.loc[
        quality["status"] != "PASS", ["dataset", "check", "status", "observed", "severity"]
    ]
    story.extend(
        [
            metric_strip(
                [
                    ("46", "checks executed"),
                    ("44", "passes"),
                    ("2", "non-critical warnings"),
                    ("0", "failures / critical failures"),
                ]
            ),
            Spacer(1, 6 * mm),
            p(
                "Checks cover missing values, invalid and empty geometry, CRS, coordinate bounds, "
                "duplicate identifiers/points and spatial-join coverage. Critical failures block the "
                "run. Warnings require documented disposition."
            ),
            p("Open warnings", "H2Project"),
            styled_table(
                [
                    ["Dataset", "Check", "Status", "Observed", "Severity"],
                    *warning_rows.astype(str).values.tolist(),
                ],
                [35 * mm, 43 * mm, 23 * mm, 49 * mm, 25 * mm],
            ),
            Spacer(1, 6 * mm),
            callout(
                "Seven synthetic competitors and sixteen synthetic POIs fall outside the analytical "
                "footprint. They are retained to exercise spatial-coverage warnings and do not enter "
                "in-footprint counts.",
                ORANGE,
            ),
        ]
    )

    page(story, "Network accessibility and isochrones", "07")
    story.extend(
        [
            p(
                "A connected H3-adjacency graph has 5,965 nodes and 17,431 edges. Projected edge length "
                "is converted to time using mode-specific speeds and synthetic mobility indices. "
                "Dijkstra shortest paths produce 5/10/15-minute drive and walk catchments."
            ),
            *figure(
                "artifacts/figures/network_isochrones.png",
                105,
                "Network catchments for the leading candidate. Cells are reached by travel-time cost, "
                "not by a circular radius.",
            ),
            metric_strip(
                [
                    ("118,859", "C24 five-minute drive population"),
                    ("396,396", "C24 ten-minute drive population"),
                    ("823,788", "C24 fifteen-minute drive population"),
                ]
            ),
        ]
    )

    page(story, "Straight-line versus network reach", "08")
    story.extend(
        [
            p(
                "A Euclidean buffer assumes uniform movement in every direction and can cross water, "
                "barriers and disconnected streets. Network time accumulates impedance along reachable "
                "links. The project stores both the network result and a naive comparison gap."
            ),
            callout(
                "For C24 Ikitelli, the recorded naive-buffer versus 10-minute network population gap is "
                "66.111%. This is why every dashboard labels network accessibility explicitly.",
                ORANGE,
            ),
            Spacer(1, 7 * mm),
            styled_table(
                [
                    ["Method", "Strength", "Failure mode", "Decision use"],
                    [
                        "Circular buffer",
                        "Fast, simple benchmark",
                        "Ignores barriers and impedance",
                        "QA comparison only",
                    ],
                    [
                        "H3 network time",
                        "Unique travel-time reach",
                        "Approximate speeds/links",
                        "Analytical screening",
                    ],
                    [
                        "Live road routing",
                        "Turn/traffic aware",
                        "Source availability and variability",
                        "Pre-investment gate",
                    ],
                ],
                [35 * mm, 42 * mm, 51 * mm, 47 * mm],
            ),
            Spacer(1, 8 * mm),
            p("Required independent validation", "H2Project"),
            *bullets(
                [
                    "rebuild drive and walk catchments with a current road network;",
                    "test peak/off-peak traffic and directionality;",
                    "verify bridge, ferry, toll and pedestrian restrictions;",
                    "confirm the exact parcel access point rather than the candidate centroid.",
                ]
            ),
        ]
    )

    page(story, "Competition, POIs and white space", "09")
    story.extend(
        [
            *figure(
                "artifacts/figures/white_space_opportunity_map.png",
                112,
                "Microzone opportunity combines demand, competition headroom and current-estate "
                "coverage penalties.",
            ),
            p(
                "Competitors are counted within a projected 3 km radius and POIs within 2 km. White "
                "space is not simply low competition: it rewards demand and uncovered reach while "
                "penalizing existing coverage and diversion."
            ),
            callout(
                "A high white-space score is a screening signal. It does not prove parcel availability, "
                "commercial viability or absence of planned competition."
            ),
        ]
    )

    page(story, "Huff gravity and cannibalization", "10")
    cannibal_rows = candidates.head(8)[
        [
            "candidate_id",
            "candidate_name",
            "huff_diversion_ratio",
            "cannibalization_risk",
            "nearest_existing_store_km",
        ]
    ].copy()
    cannibal_rows["huff_diversion_ratio"] = cannibal_rows["huff_diversion_ratio"].map(
        lambda value: f"{value:.1%}"
    )
    cannibal_rows["cannibalization_risk"] = cannibal_rows["cannibalization_risk"].map(
        lambda value: f"{value:.1%}"
    )
    cannibal_rows["nearest_existing_store_km"] = cannibal_rows["nearest_existing_store_km"].map(
        lambda value: f"{value:.1f}"
    )
    story.extend(
        [
            p(
                "Huff share is proportional to candidate attractiveness and inverse distance with "
                "decay 1.65. Captured demand and diversion from the current estate are reported "
                "separately. Cannibalization combines 10-minute overlap and nearest-store distance."
            ),
            styled_table(
                [
                    ["ID", "Candidate", "Huff diversion", "Cannibalization", "Nearest store km"],
                    *cannibal_rows.astype(str).values.tolist(),
                ],
                [14 * mm, 57 * mm, 34 * mm, 35 * mm, 35 * mm],
            ),
            Spacer(1, 6 * mm),
            callout(
                "C24 has 1.0% cannibalization and is 12.5 km from the nearest current store. C07 has "
                "34.9% cannibalization at 4.8 km and therefore requires an estate-overlap review.",
                ORANGE,
            ),
        ]
    )

    page(story, "Demand model and spatial validation", "11")
    model = summary["model_metrics"]
    story.extend(
        [
            p(
                "The 320-row benchmark is grouped into 33 projected 12 km blocks. Five GroupKFold "
                "splits ensure that neighboring sites in the same block cannot leak across training "
                "and validation. Final training occurs only after out-of-fold evaluation."
            ),
            *figure(
                "artifacts/figures/model_validation.png",
                102,
                "Out-of-fold actual-versus-predicted performance and residual stability.",
            ),
            metric_strip(
                [
                    (f"{model['mae_try_m']:.3f}m", "OOF MAE, TRY"),
                    (f"{model['rmse_try_m']:.3f}m", "OOF RMSE, TRY"),
                    (f"{model['r2']:.3f}", "OOF R2"),
                    (f"{model['mape']:.2%}", "OOF MAPE"),
                ]
            ),
            Spacer(1, 4 * mm),
            callout(
                "High fit is expected for a deterministic synthetic target and must not be generalized "
                "to real store performance.",
                ORANGE,
            ),
        ]
    )

    page(story, "SHAP demand explanations", "12")
    shap_rows = pd.read_csv(ROOT / "artifacts/data/shap_contributions.csv")
    shap_top = (
        shap_rows.loc[shap_rows["candidate_id"] == top["candidate_id"]]
        .assign(abs_value=lambda frame: frame["shap_contribution_try_m"].abs())
        .sort_values("abs_value", ascending=False)
        .head(8)
    )
    story.extend(
        [
            p(
                f"C24 model baseline is TRY {top['shap_base_value_try_m']:.3f}m and prediction is "
                f"TRY {top['predicted_sales_try_m']:.3f}m. Tree SHAP decomposes the difference into "
                "local feature contributions."
            ),
            styled_table(
                [["Feature", "SHAP contribution, TRY m"]]
                + [
                    [row.feature.replace("_", " "), f"{row.shap_contribution_try_m:+.3f}"]
                    for row in shap_top.itertuples()
                ],
                [115 * mm, 60 * mm],
            ),
            Spacer(1, 6 * mm),
            callout(
                "SHAP explains the demand model, not the final location score. AHP factor "
                "contributions provide the independent score-level audit.",
                ORANGE,
            ),
            Spacer(1, 5 * mm),
            p(
                "SHAP values are associative and local to the fitted model. They do not establish "
                "causality and can reflect correlated synthetic features."
            ),
        ]
    )

    page(story, "AHP location scoring", "13")
    factor_table = factors.copy()
    factor_table["weight"] = factor_table["weight"].map(lambda value: f"{value:.0%}")
    story.extend(
        [
            p(
                "AHP supplies transparent weights. Every factor has an explicit definition, direction, "
                "normalization and contribution. The reciprocal matrix has a consistency ratio of "
                f"{summary['ahp_consistency_ratio']:.3e}, below the 0.10 threshold."
            ),
            styled_table(
                [
                    ["Factor", "Direction", "Normalization", "Weight"],
                    *factor_table[["factor", "direction", "normalization", "weight"]]
                    .astype(str)
                    .values.tolist(),
                ],
                [65 * mm, 38 * mm, 42 * mm, 30 * mm],
            ),
            Spacer(1, 6 * mm),
            callout(
                "Score = 100 x sum(weight x normalized factor). Raw values, normalization and "
                "candidate-level contributions are persisted in separate audit tables."
            ),
        ]
    )

    page(story, "Factor contributions and sensitivity", "14")
    stable = sensitivity.sort_values("mean_rank").head(6).copy()
    stable["mean_rank"] = stable["mean_rank"].map(lambda value: f"{value:.2f}")
    stable["rank_p05"] = stable["rank_p05"].map(lambda value: f"{value:.0f}")
    stable["rank_p95"] = stable["rank_p95"].map(lambda value: f"{value:.0f}")
    stable["top_5_probability"] = stable["top_5_probability"].map(lambda value: f"{value:.1%}")
    stable["rank_1_probability"] = stable["rank_1_probability"].map(lambda value: f"{value:.1%}")
    story.extend(
        [
            *figure(
                "artifacts/figures/factor_contributions_top5.png",
                93,
                "The top five scores are sums of visible factor contributions.",
            ),
            styled_table(
                [
                    [
                        "Candidate",
                        "Mean rank",
                        "P05",
                        "P95",
                        "Top-five probability",
                        "#1 probability",
                    ],
                    *stable[
                        [
                            "candidate_id",
                            "mean_rank",
                            "rank_p05",
                            "rank_p95",
                            "top_5_probability",
                            "rank_1_probability",
                        ]
                    ]
                    .astype(str)
                    .values.tolist(),
                ],
                [24 * mm, 27 * mm, 20 * mm, 20 * mm, 50 * mm, 34 * mm],
            ),
            Spacer(1, 4 * mm),
            callout(
                "C24 remains top-five in 100% of 750 sampled weight sets. Stability means the ranking "
                "is not fragile to modest weight changes; it does not mean investment-ready.",
                ORANGE,
            ),
        ]
    )

    page(story, "Location-allocation optimization", "15")
    story.extend(
        [
            p(
                "Binary candidate variables are combined with microzone coverage variables. The "
                "objective balances expected EBIT, location score and newly covered population, with a "
                "cannibalization penalty."
            ),
            styled_table(
                [
                    ["Element", "Implementation"],
                    ["Budget", "scenario-specific cap on opening cost"],
                    ["Minimum distance", "pairwise conflict constraints"],
                    ["Capacity", "maximum portfolio count by scenario"],
                    ["Coverage", "10-minute drive microzone counted once"],
                    ["Feasibility", "publish only terminal Optimal status"],
                    ["Objective", "economics + score + incremental coverage - cannibalization"],
                ],
                [45 * mm, 130 * mm],
            ),
            Spacer(1, 7 * mm),
            p("Why optimization follows ranking", "H2Project"),
            *bullets(
                [
                    "Overlapping high-score catchments can waste portfolio budget.",
                    "A candidate may violate minimum distance from another candidate.",
                    "A lower-ranked site can add more unique population coverage.",
                    "Scenario economics can change the feasible site count.",
                    "The optimizer does not waive field or investment constraints.",
                ]
            ),
        ]
    )

    page(story, "Scenario results", "16")
    scenario_rows = scenarios.copy()
    scenario_rows["budget_used_try_m"] = scenario_rows["budget_used_try_m"].map(
        lambda value: f"{value:.3f}"
    )
    scenario_rows["market_coverage_rate"] = scenario_rows["market_coverage_rate"].map(
        lambda value: f"{value:.3%}"
    )
    scenario_rows["portfolio_sales_try_m"] = scenario_rows["portfolio_sales_try_m"].map(
        lambda value: f"{value:.3f}"
    )
    scenario_rows["portfolio_expected_ebit_try_m"] = scenario_rows[
        "portfolio_expected_ebit_try_m"
    ].map(lambda value: f"{value:.3f}")
    story.extend(
        [
            *figure(
                "artifacts/figures/scenario_comparison.png",
                95,
                "Scenario portfolios are comparative stress tests, not probability-weighted forecasts.",
            ),
            styled_table(
                [
                    ["Scenario", "Sites", "Budget TRY m", "Coverage", "Sales TRY m", "EBIT TRY m"],
                    *scenario_rows[
                        [
                            "scenario",
                            "selected_store_count",
                            "budget_used_try_m",
                            "market_coverage_rate",
                            "portfolio_sales_try_m",
                            "portfolio_expected_ebit_try_m",
                        ]
                    ]
                    .astype(str)
                    .values.tolist(),
                ],
                [30 * mm, 20 * mm, 32 * mm, 28 * mm, 35 * mm, 30 * mm],
            ),
            Spacer(1, 4 * mm),
            callout(
                "The pessimistic portfolio remains feasible but its controlled expected EBIT turns "
                "negative (-TRY 2.071m), making downside diligence a required approval gate.",
                ORANGE,
            ),
        ]
    )

    page(story, "Base portfolio and site economics", "17")
    base_rows = base_candidates.sort_values("location_rank").copy()
    base_rows["location_score"] = base_rows["location_score"].map(lambda value: f"{value:.1f}")
    base_rows["opening_cost_try_m"] = base_rows["opening_cost_try_m"].map(
        lambda value: f"{value:.3f}"
    )
    base_rows["predicted_sales_try_m"] = base_rows["predicted_sales_try_m"].map(
        lambda value: f"{value:.3f}"
    )
    base_rows["roi_3y"] = base_rows["roi_3y"].map(lambda value: f"{value:.1%}")
    story.extend(
        [
            *figure(
                "artifacts/figures/base_portfolio_map.png",
                90,
                "Existing stores and the four base-selected candidate corridors.",
            ),
            styled_table(
                [
                    ["ID", "Site", "Score", "Cost TRY m", "Sales TRY m", "3y ROI"],
                    *base_rows[
                        [
                            "candidate_id",
                            "candidate_name",
                            "location_score",
                            "opening_cost_try_m",
                            "predicted_sales_try_m",
                            "roi_3y",
                        ]
                    ]
                    .astype(str)
                    .values.tolist(),
                ],
                [15 * mm, 55 * mm, 20 * mm, 29 * mm, 31 * mm, 25 * mm],
            ),
            Spacer(1, 4 * mm),
            callout(
                "Only C18 has positive controlled three-year ROI. Binding rent, fit-out, staffing, "
                "margin and opening-ramp evidence must replace synthetic assumptions before approval.",
                ORANGE,
            ),
        ]
    )

    page(story, "PostGIS, API and observability", "18")
    story.extend(
        [
            styled_table(
                [
                    ["Capability", "Implementation", "Control"],
                    [
                        "Spatial storage",
                        "PostGIS geometry and geography",
                        "WGS84 checks and GIST indexes",
                    ],
                    [
                        "Analytics",
                        "SQL views for ranking, coverage and scenarios",
                        "source-to-view reconciliation",
                    ],
                    [
                        "Service",
                        "FastAPI candidate/score/scenario endpoints",
                        "Pydantic bounds; read-only artifacts",
                    ],
                    [
                        "Monitoring",
                        "Prometheus metrics and Grafana dashboard",
                        "health, latency, errors and drift",
                    ],
                    [
                        "Deployment",
                        "Docker Compose and Kubernetes starter",
                        "read-only, cap drop, network policy",
                    ],
                ],
                [35 * mm, 72 * mm, 68 * mm],
            ),
            Spacer(1, 7 * mm),
            p("Service contract", "H2Project"),
            *bullets(
                [
                    "GET /health reports artifact readiness.",
                    "GET /v1/candidates and /v1/candidates/{id} expose ranked evidence.",
                    "POST /v1/score recomputes bounded, normalized weight scenarios.",
                    "POST /v1/scenarios/evaluate returns controlled precomputed portfolios.",
                    "GET /metrics exposes service indicators without sensitive payloads.",
                ]
            ),
            Spacer(1, 7 * mm),
            callout(
                "The included infrastructure is a production-oriented starter. No cloud deployment or "
                "live availability claim is made in Stage 1."
            ),
        ]
    )

    page(story, "Decision products and BI design", "19")
    story.extend(
        [
            p(
                "The same pipeline outputs feed interactive HTML maps, a formula-driven Excel scenario "
                "workbook, a PBIP/PBIR/TMDL starter, an executive deck and this report."
            ),
            *figure(
                "powerbi/assets/dashboard_mockup.png",
                105,
                "Dashboard design reference with ranking, scenario and factor-contribution views.",
            ),
            styled_table(
                [
                    ["Deliverable", "Validation completed", "Remaining gate"],
                    [
                        "Excel",
                        "formula scan and visual sheet inspection",
                        "business user acceptance",
                    ],
                    ["PowerPoint", "all-slide render and overflow test", "presenter review"],
                    ["PDF", "all-page render and structural checks", "reviewer sign-off"],
                    [
                        "HTML maps",
                        "content, layers and attribution checks",
                        "browser/accessibility review",
                    ],
                    [
                        "PBIP starter",
                        "JSON structure and source paths",
                        "Power BI Desktop render/refresh",
                    ],
                ],
                [38 * mm, 68 * mm, 69 * mm],
            ),
        ]
    )

    page(story, "Governance, monitoring and incidents", "20")
    story.extend(
        [
            styled_table(
                [
                    ["Gate", "Owner", "Required evidence"],
                    ["Data", "Data owner", "source/license, contract, CRS and quality ledger"],
                    ["Model", "Analytical owner", "spatial CV, baseline, residuals and model card"],
                    [
                        "Decision",
                        "Business + analytical",
                        "contributions, sensitivity and constraints",
                    ],
                    [
                        "Field",
                        "Business/real estate",
                        "parcel, routing, legal and commercial diligence",
                    ],
                    [
                        "Capital",
                        "Investment committee",
                        "approved business case and risk acceptance",
                    ],
                ],
                [33 * mm, 45 * mm, 97 * mm],
            ),
            Spacer(1, 7 * mm),
            p("Monitoring and incident priorities", "H2Project"),
            *bullets(
                [
                    "stop publication on any critical data-quality failure;",
                    "track MAE/RMSE, feature distributions, SHAP and rank stability;",
                    "surface non-Optimal optimizer status and block stale results;",
                    "verify artifacts by SHA-256 before release and rollback;",
                    "withdraw any report that may change candidate ranking or portfolio selection.",
                ]
            ),
            callout(
                "The final capital decision remains a human accountability and cannot be delegated to "
                "the scoring API, dashboard or optimizer.",
                ORANGE,
            ),
        ]
    )

    page(story, "Bias, threat model and open risks", "21")
    story.extend(
        [
            styled_table(
                [
                    ["Risk", "Mechanism", "Primary control"],
                    [
                        "Affluence bias",
                        "income/purchasing-power proxy",
                        "sensitivity and service-equity overlay",
                    ],
                    [
                        "Centrality bias",
                        "transit and POI advantage",
                        "white-space/cost balance and corridor review",
                    ],
                    [
                        "Estate bias",
                        "current stores define coverage",
                        "report uncovered demand separately",
                    ],
                    [
                        "Analytical tampering",
                        "weights/output edited after review",
                        "CODEOWNERS, manifest and protected main",
                    ],
                    [
                        "Supply chain",
                        "dependency/image compromise",
                        "Dependabot, pip-audit, CodeQL and Trivy",
                    ],
                    [
                        "Decision misuse",
                        "synthetic output presented as fact",
                        "persistent labels and human stage gates",
                    ],
                ],
                [37 * mm, 64 * mm, 74 * mm],
            ),
            Spacer(1, 6 * mm),
            p(
                "The most important residual risk is not a software exploit but decision misuse. The "
                "system can be technically correct under its assumptions while commercially wrong. "
                "Governance labels and field evidence are therefore core controls."
            ),
        ]
    )

    page(story, "Limitations and required next evidence", "22")
    story.extend(
        [
            *bullets(
                [
                    "Replace synthetic sales, demand, rent, capex and opex with governed aggregates and binding quotes.",
                    "Replace H3 routing with a current turn-aware road and pedestrian network.",
                    "Validate peak/off-peak traffic, parcel entrance and delivery access.",
                    "Add zoning, permit, frontage, parking, visibility and planned infrastructure.",
                    "Add competitor quality, openings, closures and future pipeline.",
                    "Backtest on temporally and spatially held-out real store openings.",
                    "Calibrate uncertainty intervals and monitor residuals by geography/store format.",
                    "Review geographic equity and proxy effects with business/legal stakeholders.",
                    "Open and refresh the PBIP starter in Power BI Desktop.",
                    "Observe CI, CodeQL and security workflows to terminal results after publication.",
                ]
            ),
            Spacer(1, 8 * mm),
            callout(
                "No candidate should advance to capital approval until its exact site, live routing and "
                "binding unit economics replace the synthetic assumptions.",
                ORANGE,
            ),
        ]
    )

    page(story, "Source and license register", "23")
    story.extend(
        [
            styled_table(
                [
                    ["Source/component", "Use", "License / status"],
                    [
                        "Project generator",
                        "commercial and performance data",
                        "original MIT; deterministic synthetic",
                    ],
                    ["Approximate anchors", "geographic framing", "manual approximate coordinates"],
                    ["OpenStreetMap tiles", "interactive basemap", "ODbL attribution included"],
                    ["H3", "microzone indexing", "Apache-2.0"],
                    ["GeoPandas / Shapely", "spatial operations", "BSD-3-Clause"],
                    ["scikit-learn / SHAP", "model and explanations", "BSD-3-Clause / MIT"],
                    ["PuLP / CBC", "location allocation", "MIT / EPL-2.0"],
                    [
                        "Power BI Project format",
                        "PBIP/PBIR/TMDL starter",
                        "Microsoft product/docs terms",
                    ],
                ],
                [52 * mm, 66 * mm, 57 * mm],
            ),
            Spacer(1, 6 * mm),
            p(
                "<b>Primary references:</b><br/>"
                '<link href="https://www.openstreetmap.org/copyright">OpenStreetMap copyright and attribution</link><br/>'
                '<link href="https://h3geo.org/docs/">H3 documentation</link><br/>'
                '<link href="https://geopandas.org/en/stable/about.html">GeoPandas project and license</link><br/>'
                '<link href="https://shapely.readthedocs.io/">Shapely documentation</link><br/>'
                '<link href="https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview">'
                "Microsoft Power BI Projects overview</link>"
            ),
            callout(
                "No external real demographic, transaction, mobility, rent or proprietary POI dataset "
                "is bundled in this package."
            ),
        ]
    )

    page(story, "Appendix A - Candidate priority list", "A")
    candidate_rows = candidates.head(12).copy()
    candidate_rows["location_score"] = candidate_rows["location_score"].map(
        lambda value: f"{value:.3f}"
    )
    candidate_rows["predicted_sales_try_m"] = candidate_rows["predicted_sales_try_m"].map(
        lambda value: f"{value:.3f}"
    )
    candidate_rows["opening_cost_try_m"] = candidate_rows["opening_cost_try_m"].map(
        lambda value: f"{value:.3f}"
    )
    candidate_rows["cannibalization_risk"] = candidate_rows["cannibalization_risk"].map(
        lambda value: f"{value:.1%}"
    )
    story.extend(
        [
            styled_table(
                [
                    ["Rank", "ID", "Candidate", "Score", "Sales TRY m", "Cost TRY m", "Cannib."],
                    *candidate_rows[
                        [
                            "location_rank",
                            "candidate_id",
                            "candidate_name",
                            "location_score",
                            "predicted_sales_try_m",
                            "opening_cost_try_m",
                            "cannibalization_risk",
                        ]
                    ]
                    .astype(str)
                    .values.tolist(),
                ],
                [15 * mm, 14 * mm, 54 * mm, 20 * mm, 28 * mm, 25 * mm, 19 * mm],
            ),
            Spacer(1, 6 * mm),
            p(
                "The full 24-row ranking, all raw/normalized factors and economic fields are available "
                "in artifacts/data/candidate_scores.csv and the Excel workbook."
            ),
        ]
    )

    page(story, "Appendix B - Reproducibility and QA evidence", "B")
    story.extend(
        [
            styled_table(
                [
                    ["Evidence", "Location"],
                    ["Pipeline run summary", "artifacts/metrics/pipeline_summary.json"],
                    [
                        "Model metrics and folds",
                        "artifacts/metrics/model_metrics.json; artifacts/data/model_fold_metrics.csv",
                    ],
                    ["Out-of-fold predictions", "artifacts/data/model_out_of_fold_predictions.csv"],
                    ["Data quality", "artifacts/qa/data_quality_checks.csv"],
                    ["AHP specification", "artifacts/data/factor_specification.csv"],
                    [
                        "SHAP and score contributions",
                        "artifacts/data/shap_contributions.csv; score_contributions.csv",
                    ],
                    [
                        "Scenario outputs",
                        "artifacts/data/scenario_summaries.csv; scenario_selections.csv",
                    ],
                    ["Tests and coverage", "artifacts/qa/test_results.txt; coverage.json/xml"],
                    ["Artifact verification", "artifacts/qa/artifact_verification.json"],
                    ["File hashes", "MANIFEST.sha256; project_manifest.json"],
                ],
                [58 * mm, 117 * mm],
            ),
            Spacer(1, 7 * mm),
            callout(
                f"Pipeline run status: {summary['run_status']} - seed {summary['seed']} - "
                f"runtime {summary['runtime_seconds']:.3f} seconds. Generated metrics are evidence, "
                "not manually authored presentation values."
            ),
            Spacer(1, 6 * mm),
            p(
                "The release package intentionally excludes Git metadata, caches and local inspection "
                "sidecars. GitHub publication is a separate, approval-gated stage."
            ),
        ]
    )

    page(story, "Appendix C - Review decision record", "C")
    story.extend(
        [
            p(
                "Use this page to record the Stage 1 review outcome. Approval here means approval to "
                "publish the reviewed repository tree, not approval to invest in any location."
            ),
            styled_table(
                [
                    ["Review item", "Reviewer / date / disposition"],
                    ["Analytical methodology", ""],
                    ["Model validation and SHAP", ""],
                    ["AHP weights and sensitivity", ""],
                    ["Optimization constraints and scenarios", ""],
                    ["Data quality and source/license", ""],
                    ["Security, risk and operations", ""],
                    ["Excel / maps / deck / PDF / PBIP", ""],
                    ["GitHub publication authorization", ""],
                ],
                [67 * mm, 108 * mm],
            ),
            Spacer(1, 12 * mm),
            callout(
                "PROJECT_STATUS: READY_FOR_REVIEW - NOT_PUBLISHED",
                ORANGE,
            ),
            Spacer(1, 6 * mm),
            p(
                "Publication requires the explicit repository link and authorization to publish on "
                "main. Until then, no remote, push, pull request or GitHub write is permitted."
            ),
        ]
    )

    doc = ProjectDocTemplate(OUTPUT)
    doc.build(story)
    print(f"created {OUTPUT}")


if __name__ == "__main__":
    build()
