"""The CI reproducibility check must flag committed outputs a fresh run no longer produces."""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def compare_outputs():
    spec = importlib.util.spec_from_file_location(
        "compare_outputs", ROOT / "scripts" / "compare_outputs.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _copy_committed(target: Path) -> Path:
    for relative in ("data/processed", "artifacts/data", "artifacts/metrics"):
        shutil.copytree(ROOT / relative, target / relative)
    return target


def test_identical_outputs_and_float_noise_match(tmp_path, compare_outputs):
    committed = _copy_committed(tmp_path / "committed")
    fresh = _copy_committed(tmp_path / "fresh")
    metrics_path = fresh / "artifacts/metrics/model_metrics.json"
    metrics = json.loads(metrics_path.read_text())
    metrics["mae_try_m"] *= 1 + 1e-14
    metrics_path.write_text(json.dumps(metrics))
    summary_path = fresh / "artifacts/metrics/pipeline_summary.json"
    summary = json.loads(summary_path.read_text())
    summary["runtime_seconds"] += 30
    summary_path.write_text(json.dumps(summary))

    assert compare_outputs.compare(committed, fresh) == []


def test_stale_committed_outputs_are_reported(tmp_path, compare_outputs):
    committed = _copy_committed(tmp_path / "committed")
    fresh = _copy_committed(tmp_path / "fresh")
    scores_path = committed / "artifacts/data/candidate_scores.csv"
    lines = scores_path.read_text().splitlines()
    header = lines[0].split(",")
    first = lines[1].split(",")
    column = header.index("location_score")
    first[column] = str(float(first[column]) + 0.5)
    lines[1] = ",".join(first)
    scores_path.write_text("\n".join(lines) + "\n")
    summary_path = committed / "artifacts/metrics/model_metrics.json"
    summary = json.loads(summary_path.read_text())
    summary["r2"] = 0.5
    summary_path.write_text(json.dumps(summary))
    (fresh / "artifacts/data/new_output.csv").write_text("a\n1\n")

    errors = compare_outputs.compare(committed, fresh)

    assert any(
        e.startswith("artifacts/data/candidate_scores.csv row 1 column location_score")
        for e in errors
    )
    assert any(e.startswith("artifacts/metrics/model_metrics.json.r2") for e in errors)
    assert "artifacts/data/new_output.csv: missing in committed outputs" in errors
    assert compare_outputs.main(["compare_outputs.py", str(committed), str(fresh)]) == 1
