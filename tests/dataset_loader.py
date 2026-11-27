
"""Utilities for loading POC dataset files in tests."""

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = PROJECT_ROOT / "datasets" / "leakguard_poc"

TRAIN_DIR = DATASET_ROOT / "data"
EVAL_DIR = DATASET_ROOT / "tests" / "fixtures"


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from a dataset file."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path.name}")

    return data
