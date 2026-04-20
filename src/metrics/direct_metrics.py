"""Build raw measurement CSVs from author-provided paper data.

This module does not parse damaged artifacts or invent missing sessions. It
only converts values present in `data/source/provided_paper_data.json` into
the raw schema. Because the provided data does not include 45 repetition-level
rows, reconstructed raw rows are cell-level placeholders with blank
`session_id` and `repetition=MISSING`.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.config import APPROACHES, SOURCE_TASK_METRICS, TASKS
from src.schemas import MANIFEST_COLUMNS, RAW_MEASUREMENT_COLUMNS


def normalize_metric_name(name: str) -> str:
    """Normalize source metric names into repository column names."""

    return SOURCE_TASK_METRICS.get(name, name)


def rows_from_provided_source(source: dict[str, Any]) -> pd.DataFrame:
    """Create directly supported raw rows from source task-level values."""

    rows: dict[tuple[str, str], dict[str, Any]] = {}
    extra_columns: set[str] = set()
    task_values = source.get("task_level_values", {})
    for source_metric, by_approach in task_values.items():
        metric = normalize_metric_name(source_metric)
        for approach, by_task in by_approach.items():
            for task_id, value in by_task.items():
                key = (task_id, approach)
                if key not in rows:
                    row = {column: pd.NA for column in RAW_MEASUREMENT_COLUMNS}
                    row.update(
                        {
                            "session_id": pd.NA,
                            "task_id": task_id,
                            "approach": approach,
                            "repetition": "MISSING",
                            "notes": "TASK_LEVEL_VALUE_FROM_PROVIDED_PAPER_DATA; NOT_A_SESSION_ROW",
                        }
                    )
                    rows[key] = row
                rows[key][metric] = value
                if metric not in RAW_MEASUREMENT_COLUMNS:
                    extra_columns.add(metric)

    ordered = [rows[(task, approach)] for approach in APPROACHES for task in TASKS if (task, approach) in rows]
    columns = RAW_MEASUREMENT_COLUMNS + sorted(extra_columns)
    return pd.DataFrame(ordered, columns=columns)


def manifest_from_provided_source(source: dict[str, Any]) -> pd.DataFrame:
    """Create placeholders for available task/approach cells, not fake sessions."""

    raw = rows_from_provided_source(source)
    rows = []
    for _, row in raw.iterrows():
        rows.append(
            {
                "session_id": pd.NA,
                "task_id": row["task_id"],
                "approach": row["approach"],
                "repetition": "MISSING",
                "source_type": "author_provided_task_level_value",
                "source_note": "No repetition-level artifact path was provided.",
                "status": "MISSING_SESSION_ROWS",
            }
        )
    return pd.DataFrame(rows, columns=MANIFEST_COLUMNS)


def write_raw_reconstruction(source: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return reconstructed raw measurements and manifest placeholders."""

    return rows_from_provided_source(source), manifest_from_provided_source(source)
