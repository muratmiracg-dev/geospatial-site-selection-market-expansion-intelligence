"""Configuration loading and deterministic project paths."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ProjectPaths:
    """Resolved repository paths."""

    root: Path
    artifacts: Path
    processed: Path
    raw: Path

    @classmethod
    def from_root(cls, root: str | Path) -> ProjectPaths:
        resolved = Path(root).resolve()
        return cls(
            root=resolved,
            artifacts=resolved / "artifacts",
            processed=resolved / "data" / "processed",
            raw=resolved / "data" / "raw",
        )

    def ensure(self) -> None:
        for path in (
            self.artifacts,
            self.artifacts / "data",
            self.artifacts / "models",
            self.artifacts / "maps",
            self.artifacts / "figures",
            self.artifacts / "metrics",
            self.artifacts / "qa",
            self.processed,
            self.raw,
        ):
            path.mkdir(parents=True, exist_ok=True)


def load_config(path: str | Path) -> dict[str, Any]:
    """Load the checked-in YAML configuration."""

    with Path(path).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError("Configuration root must be a mapping.")
    return config
