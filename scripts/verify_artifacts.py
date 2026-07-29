"""Verify that published analytical and user-facing artifacts are internally consistent."""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

import pandas as pd
import yaml
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
QA_PATH = ROOT / "artifacts" / "qa" / "artifact_verification.json"
IGNORED_PARTS = {".git", ".pytest_cache", ".ruff_cache", ".venv", "__pycache__"}


def check(condition: bool, name: str, details: str, results: list[dict[str, object]]) -> None:
    results.append({"check": name, "status": "PASS" if condition else "FAIL", "details": details})


def main() -> int:
    results: list[dict[str, object]] = []
    required = [
        "artifacts/metrics/pipeline_summary.json",
        "artifacts/data/candidate_scores.csv",
        "artifacts/data/scenario_summaries.csv",
        "artifacts/data/scenario_selections.csv",
        "artifacts/data/factor_specification.csv",
        "artifacts/qa/data_quality_summary.json",
        "artifacts/maps/candidate_portfolio_map.html",
        "artifacts/maps/white_space_h3_map.html",
        "artifacts/maps/network_isochrones_map.html",
        "artifacts/maps/scenario_portfolios_map.html",
        "excel/Istanbul_Location_Evaluation_Scenario_Workbook.xlsx",
        "presentation/Istanbul_Geospatial_Market_Expansion_Executive_Deck.pptx",
        "report/Istanbul_Geospatial_Site_Selection_Methodology_Governance_Report.pdf",
        "powerbi/MarketExpansion.pbip",
    ]
    for relative in required:
        target = ROOT / relative
        check(
            target.is_file() and target.stat().st_size > 0,
            f"exists:{relative}",
            str(target),
            results,
        )

    summary = json.loads((ROOT / "artifacts/metrics/pipeline_summary.json").read_text())
    candidates = pd.read_csv(ROOT / "artifacts/data/candidate_scores.csv")
    scenarios = pd.read_csv(ROOT / "artifacts/data/scenario_summaries.csv")
    selections = pd.read_csv(ROOT / "artifacts/data/scenario_selections.csv")
    factors = pd.read_csv(ROOT / "artifacts/data/factor_specification.csv")
    quality = json.loads((ROOT / "artifacts/qa/data_quality_summary.json").read_text())

    check(summary["run_status"] == "SUCCESS", "pipeline_status", summary["run_status"], results)
    check(len(candidates) == 24, "candidate_count", str(len(candidates)), results)
    check(candidates["candidate_id"].is_unique, "candidate_ids_unique", "candidate_id", results)
    check(candidates["location_rank"].is_unique, "ranks_unique", "location_rank", results)
    check(
        candidates["location_score"].between(0, 100).all(),
        "score_bounds",
        "0 <= location_score <= 100",
        results,
    )
    check(
        abs(float(factors["weight"].sum()) - 1.0) < 1e-9,
        "ahp_weights_sum",
        f"{factors['weight'].sum():.12f}",
        results,
    )
    check(
        (scenarios["solver_status"] == "Optimal").all(),
        "scenario_solver_status",
        ",".join(scenarios["solver_status"]),
        results,
    )
    check(
        (scenarios["budget_used_try_m"] <= scenarios["budget_try_m"] + 1e-9).all(),
        "scenario_budget_feasibility",
        "budget_used <= budget",
        results,
    )
    selected_counts = selections.groupby("scenario").size()
    expected_counts = scenarios.set_index("scenario")["selected_store_count"]
    check(
        selected_counts.reindex(expected_counts.index).equals(expected_counts.astype("int64")),
        "scenario_selection_counts",
        selected_counts.to_dict().__repr__(),
        results,
    )
    check(quality["failed"] == 0, "data_quality_failures", str(quality["failed"]), results)

    for relative in [
        "excel/Istanbul_Location_Evaluation_Scenario_Workbook.xlsx",
        "presentation/Istanbul_Geospatial_Market_Expansion_Executive_Deck.pptx",
    ]:
        path = ROOT / relative
        valid_zip = False
        if path.exists():
            try:
                with zipfile.ZipFile(path) as archive:
                    valid_zip = archive.testzip() is None
            except zipfile.BadZipFile:
                valid_zip = False
        check(valid_zip, f"office_container:{relative}", "valid Open XML ZIP", results)

    pdf_path = ROOT / "report/Istanbul_Geospatial_Site_Selection_Methodology_Governance_Report.pdf"
    pdf = PdfReader(pdf_path)
    check(
        len(pdf.pages) == 27 and not pdf.is_encrypted,
        "pdf_structure",
        f"{len(pdf.pages)} pages; encrypted={pdf.is_encrypted}",
        results,
    )

    for relative in [
        "artifacts/maps/candidate_portfolio_map.html",
        "artifacts/maps/white_space_h3_map.html",
        "artifacts/maps/network_isochrones_map.html",
        "artifacts/maps/scenario_portfolios_map.html",
    ]:
        text = (ROOT / relative).read_text(encoding="utf-8")
        check(
            "<html" in text.lower() and "openstreetmap" in text.lower(),
            f"interactive_map:{relative}",
            "HTML and OSM attribution present",
            results,
        )

    json_files = list((ROOT / "powerbi").rglob("*.json"))
    valid_json = True
    for path in json_files:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            valid_json = False
    check(valid_json and bool(json_files), "powerbi_json", f"{len(json_files)} JSON files", results)

    all_json_valid = True
    json_count = 0
    for path in ROOT.rglob("*.json"):
        if any(part in IGNORED_PARTS for part in path.parts):
            continue
        json_count += 1
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            all_json_valid = False
    check(all_json_valid, "repository_json", f"{json_count} JSON/GeoJSON files", results)

    markdown_links_valid = True
    markdown_link_count = 0
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in ROOT.rglob("*.md"):
        if any(part in IGNORED_PARTS for part in path.parts):
            continue
        for target in link_pattern.findall(path.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            markdown_link_count += 1
            local_target = target.split("#", maxsplit=1)[0]
            if not (path.parent / local_target).exists():
                markdown_links_valid = False
    check(
        markdown_links_valid,
        "markdown_local_links",
        f"{markdown_link_count} local links",
        results,
    )

    for relative in [
        "docker-compose.yml",
        ".github/workflows/ci.yml",
        ".github/workflows/codeql.yml",
        ".github/workflows/security.yml",
        ".github/dependabot.yml",
    ]:
        try:
            yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))
            valid_yaml = True
        except yaml.YAMLError:
            valid_yaml = False
        check(valid_yaml, f"yaml:{relative}", "valid YAML", results)

    failures = [row for row in results if row["status"] == "FAIL"]
    payload = {
        "status": "PASS" if not failures else "FAIL",
        "checks": len(results),
        "passes": len(results) - len(failures),
        "failures": len(failures),
        "results": results,
    }
    QA_PATH.parent.mkdir(parents=True, exist_ok=True)
    QA_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: payload[key] for key in ("status", "checks", "passes", "failures")}))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
