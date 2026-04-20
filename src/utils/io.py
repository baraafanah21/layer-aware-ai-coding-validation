"""I/O helpers that preserve missing values and avoid silent fabrication."""

from __future__ import annotations

import json
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pandas as pd

LOGGER = logging.getLogger(__name__)


def read_csv(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    """Read a CSV file, returning an empty frame if it is absent."""

    if not path.exists():
        LOGGER.warning("CSV missing: %s", path)
        return pd.DataFrame(columns=columns)
    return pd.read_csv(path, keep_default_na=True)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    """Write a DataFrame to CSV, creating parent directories."""

    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def load_json(path: Path) -> Any | None:
    """Load JSON from a path; return None on missing or parse failure."""

    if not path.exists():
        LOGGER.warning("JSON artifact missing: %s", path)
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception as exc:
        LOGGER.exception("Failed to parse JSON %s: %s", path, exc)
        return None


def write_json(data: Any, path: Path) -> None:
    """Write JSON with stable formatting."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def load_xml(path: Path) -> ET.Element | None:
    """Load XML from a path; return None on missing or parse failure."""

    if not path.exists():
        LOGGER.warning("XML artifact missing: %s", path)
        return None
    try:
        return ET.parse(path).getroot()
    except Exception as exc:
        LOGGER.exception("Failed to parse XML %s: %s", path, exc)
        return None


def coerce_numeric_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Convert selected columns to numeric values, leaving failures as NA."""

    result = df.copy()
    for column in columns:
        if column in result.columns:
            result[column] = pd.to_numeric(result[column], errors="coerce")
    return result
