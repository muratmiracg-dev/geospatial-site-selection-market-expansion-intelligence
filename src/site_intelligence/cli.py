"""Command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from site_intelligence.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Istanbul site-intelligence pipeline.")
    parser.add_argument("command", nargs="?", choices=["run"], default="run")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--config", type=Path, default=Path("configs/base.yaml"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary = run_pipeline(args.root, args.root / args.config)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
