"""Aggregation utilities for reconstructed task/cell and approach summaries."""

from __future__ import annotations

import pandas as pd

from typing import Any

from src.config import DERIVED_METRICS, METRIC_ALIASES, RAW_NUMERIC_METRICS, RUBRIC_METRICS


SUMMARY_METRICS = list(RAW_NUMERIC_METRICS) + list(RUBRIC_METRICS) + list(DERIVED_METRICS)


def summarize_by(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """Compute mean/std/count for numeric metrics by grouping columns."""

    available = [metric for metric in SUMMARY_METRICS if metric in df.columns]
    numeric = df.copy()
    for metric in available:
        numeric[metric] = pd.to_numeric(numeric[metric], errors="coerce")
    grouped = numeric.groupby(group_cols, dropna=False)[available].agg(["mean", "std", "count"])
    grouped.columns = [f"{metric}_{stat}" for metric, stat in grouped.columns]
    return grouped.reset_index()


def per_cell_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return task/approach values directly supported by reconstructed rows."""

    return summarize_by(df, ["task_id", "approach"])


def per_approach_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize reconstructed task/cell values across tasks by approach."""

    return summarize_by(df, ["approach"])


def cell_mean_correlations(cell_df: pd.DataFrame) -> pd.DataFrame:
    """Return correlations across task-approach cell means."""

    mean_cols = [column for column in cell_df.columns if column.endswith("_mean")]
    return cell_df[mean_cols].corr(numeric_only=True)


def provided_approach_summary(source: dict[str, Any]) -> pd.DataFrame:
    """Flatten author-provided approach means without altering values."""

    rows = []
    for approach, metrics in source.get("aggregated_means_per_approach", {}).items():
        row: dict[str, Any] = {"approach": approach, "source_level": "provided_approach_mean"}
        for metric, value in metrics.items():
            row[METRIC_ALIASES.get(metric, metric)] = value
        rows.append(row)
    return pd.DataFrame(rows)
