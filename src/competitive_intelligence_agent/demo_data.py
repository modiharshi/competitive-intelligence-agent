"""Demo data loading helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DEMO_PATH = PACKAGE_ROOT / "data" / "demo_signals.json"


def load_demo_dataset(path: Path | None = None) -> dict[str, Any]:
    dataset_path = path or DEFAULT_DEMO_PATH
    with dataset_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
