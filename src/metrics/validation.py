"""Validation between preserved source values and recomputed outputs."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.config import (
    LAYER_QUALITY_METRICS,
    METRIC_ALIASES,
    RUBRIC_METRICS,
    SOURCE_PRESERVED_NOT_RECOMPUTED,
    SOURCE_TASK_METRICS,
    VALIDATION_CATEGORIES,
)


VALIDATION_COLUMNS = [
    "metric_name",
    "level",
    "expected_value",
    "computed_value",
    "abs_diff",
    "rel_diff_pct",
    "status",
]

FLOAT_EPSILON = 1e-12
ROUNDING_ABS_THRESHOLD = 0.001
ROUNDING_REL_THRESHOLD_PCT = 1.0

GROUPED_VALIDATION_COLUMNS = VALIDATION_COLUMNS + [
    "category",
    "reproducibility_status",
    "explanation",
    "recommended_action",
]

NEEDS_INPUT_COLUMNS = [
    "metric_name",
    "level",
    "category",
    "needed_input",
    "reason",
]

PAPER_READY_COLUMNS = [
    "level",
    "approach",
    "task_id",
    "metric_name",
    "value",
    "source_path",
    "reproducibility_status",
    "note",
]

OVERVIEW_COLUMNS = [
    "category",
    "count",
    "interpretation",
    "reviewer_risk_level",
    "action_needed",
]

CATEGORY_DETAILS = {
    "MATCH": (
        "fully supported",
        "low",
        "No action needed.",
    ),
    "INSUFFICIENT_SOURCE_DATA": (
        "limited by missing raw rows or supporting source fields",
        "medium",
        "Recover session-level rows, supplementary cell statistics, or source fields.",
    ),
    "MISSING_RUBRIC_MAPPING": (
        "limited by missing rubric definitions",
        "medium",
        "Recover rubric thresholds and source-signal definitions.",
    ),
    "ROUNDING_DIFFERENCE": (
        "harmless rounding difference",
        "low",
        "Keep both values visible and document rounding.",
    ),
    "FORMULA_NOT_RECONSTRUCTABLE": (
        "preserved value whose original formula or normalization was not recovered",
        "medium",
        "Recover the original formula, normalization constants, and supporting inputs.",
    ),
    "TRUE_MISMATCH": (
        "direct contradiction",
        "high",
        "Investigate before submission.",
    ),
}

CORRELATION_MAP = {
    "mi_vs_loc": ("maintainability_index_mean", "loc_mean"),
    "mi_vs_average_cc": ("maintainability_index_mean", "cc_avg_mean"),
    "mi_vs_code_smells": ("maintainability_index_mean", "code_smells_mean"),
    "average_cc_vs_bugs_pre": ("cc_avg_mean", "bugs_pre_release_mean"),
    "security_issues_vs_critical": ("security_issues_mean", "critical_security_mean"),
    "coverage_vs_bugs_post": ("coverage_pct_mean", "bugs_post_integration_mean"),
}


def _compare(metric: str, level: str, expected: Any, computed: Any) -> dict[str, Any]:
    """Compare two scalar values exactly, reporting transparent differences."""

    expected_num = pd.to_numeric(pd.Series([expected]), errors="coerce").iloc[0]
    computed_num = pd.to_numeric(pd.Series([computed]), errors="coerce").iloc[0]
    if pd.isna(expected_num) or pd.isna(computed_num):
        return {
            "metric_name": metric,
            "level": level,
            "expected_value": expected,
            "computed_value": computed,
            "abs_diff": pd.NA,
            "rel_diff_pct": pd.NA,
            "status": "MISSING_COMPUTED" if pd.isna(computed_num) else "MISSING_EXPECTED",
        }
    abs_diff = abs(float(expected_num) - float(computed_num))
    rel_diff = 0.0 if float(expected_num) == 0 else 100 * abs_diff / abs(float(expected_num))
    return {
        "metric_name": metric,
        "level": level,
        "expected_value": expected,
        "computed_value": computed,
        "abs_diff": abs_diff,
        "rel_diff_pct": rel_diff,
        "status": "MATCH" if abs_diff <= FLOAT_EPSILON else "MISMATCH",
    }


def validate_source_against_outputs(
    source: dict[str, Any],
    cell_summary: pd.DataFrame,
    approach_summary: pd.DataFrame,
) -> pd.DataFrame:
    """Validate task, approach, and correlation values against computed outputs."""

    rows: list[dict[str, Any]] = []

    for source_metric, by_approach in source.get("task_level_values", {}).items():
        metric = SOURCE_TASK_METRICS.get(source_metric, source_metric)
        computed_column = f"{metric}_mean"
        for approach, by_task in by_approach.items():
            for task_id, expected in by_task.items():
                subset = cell_summary[
                    (cell_summary["approach"] == approach) & (cell_summary["task_id"] == task_id)
                ]
                computed = subset[computed_column].iloc[0] if computed_column in subset and not subset.empty else pd.NA
                rows.append(_compare(f"{metric}:{approach}:{task_id}", "cell", expected, computed))

    for approach, metrics in source.get("aggregated_means_per_approach", {}).items():
        subset = approach_summary[approach_summary["approach"] == approach]
        for source_metric, expected in metrics.items():
            metric = METRIC_ALIASES.get(source_metric, source_metric)
            computed_column = f"{metric}_mean"
            computed = subset[computed_column].iloc[0] if computed_column in subset and not subset.empty else pd.NA
            rows.append(_compare(f"{metric}:{approach}", "approach", expected, computed))

    correlations = source.get("correlations", {})
    for source_metric, expected in correlations.items():
        pair = CORRELATION_MAP.get(source_metric)
        if pair is None or pair[0] not in cell_summary.columns or pair[1] not in cell_summary.columns:
            computed = pd.NA
        else:
            computed = cell_summary[pair[0]].corr(cell_summary[pair[1]])
        rows.append(_compare(source_metric, "correlation", expected, computed))

    return pd.DataFrame(rows, columns=VALIDATION_COLUMNS)


def _base_metric(metric_name: str) -> str:
    """Return the metric portion before approach/task suffixes."""

    return str(metric_name).split(":", maxsplit=1)[0]


def _is_rounding_difference(row: pd.Series) -> bool:
    abs_diff = pd.to_numeric(pd.Series([row.get("abs_diff")]), errors="coerce").iloc[0]
    rel_diff = pd.to_numeric(pd.Series([row.get("rel_diff_pct")]), errors="coerce").iloc[0]
    if pd.isna(abs_diff):
        return False
    return abs_diff <= ROUNDING_ABS_THRESHOLD or (
        pd.notna(rel_diff) and rel_diff <= ROUNDING_REL_THRESHOLD_PCT
    )


def classify_validation_row(row: pd.Series) -> tuple[str, str, str]:
    """Classify a non-MATCH validation row without altering source values."""

    metric = _base_metric(str(row.get("metric_name", "")))
    level = str(row.get("level", ""))
    status = str(row.get("status", ""))

    if status == "MATCH":
        return (
            "MATCH",
            "Computed value matches the provided source value.",
            "No action needed.",
        )

    if _is_rounding_difference(row):
        return (
            "ROUNDING_DIFFERENCE",
            "The difference is within the configured rounding threshold.",
            "Keep both values visible; cite rounded paper value where appropriate.",
        )

    if metric in RUBRIC_METRICS or metric in LAYER_QUALITY_METRICS:
        return (
            "MISSING_RUBRIC_MAPPING",
            "Rubric threshold mappings were not recovered, so this rubric metric cannot be recomputed.",
            "Recover or recreate the study rubric table with explicit thresholds.",
        )

    if metric in SOURCE_PRESERVED_NOT_RECOMPUTED:
        return (
            "FORMULA_NOT_RECONSTRUCTABLE",
            "This metric is preserved from the paper, but the exact formula or normalization needed to recompute it was not recovered.",
            "Recover the original metric definition, normalization constants, and supporting raw fields.",
        )

    if status.startswith("MISSING") or level in {"approach", "correlation"}:
        return (
            "INSUFFICIENT_SOURCE_DATA",
            "The available source data does not include enough repetition-level, cell-level, or supporting metric inputs to reconstruct this value exactly.",
            "Add recovered 45 session rows, supplementary per-cell statistics, or supporting raw metric fields.",
        )

    return (
        "TRUE_MISMATCH",
        "The value is computable from available inputs but does not match and is not explained by rounding or missing source data.",
        "Inspect the source value, formula, and generated output manually.",
    )


def reproducibility_status_for(metric_name: str, category: str) -> str:
    """Map validation categories to reviewer-facing reproducibility statuses."""

    metric = _base_metric(metric_name)
    if metric in SOURCE_PRESERVED_NOT_RECOMPUTED:
        return "FORMULA_NOT_RECONSTRUCTABLE"
    if category == "MATCH":
        return "RECOMPUTED"
    if category == "ROUNDING_DIFFERENCE":
        return "ROUNDING_DIFFERENCE"
    if category == "MISSING_RUBRIC_MAPPING":
        return "MISSING_RUBRIC_MAPPING"
    if category == "TRUE_MISMATCH":
        return "TRUE_MISMATCH"
    if category == "FORMULA_NOT_RECONSTRUCTABLE":
        return "FORMULA_NOT_RECONSTRUCTABLE"
    return "INSUFFICIENT_SOURCE_DATA"


def group_validation_report(validation: pd.DataFrame) -> pd.DataFrame:
    """Add category, explanation, and recommended action columns."""

    grouped = validation.copy()
    if grouped.empty:
        for column in GROUPED_VALIDATION_COLUMNS:
            if column not in grouped.columns:
                grouped[column] = pd.NA
        return grouped[GROUPED_VALIDATION_COLUMNS]

    classified = grouped.apply(classify_validation_row, axis=1, result_type="expand")
    grouped["category"] = classified[0]
    grouped["reproducibility_status"] = [
        reproducibility_status_for(metric, category)
        for metric, category in zip(grouped["metric_name"], grouped["category"], strict=True)
    ]
    grouped["explanation"] = classified[1]
    grouped["recommended_action"] = classified[2]
    return grouped[GROUPED_VALIDATION_COLUMNS]


def needs_additional_inputs(grouped_validation: pd.DataFrame) -> pd.DataFrame:
    """Create a concise checklist of missing inputs needed for reproducibility."""

    rows = []
    for _, row in grouped_validation.iterrows():
        category = row.get("category")
        if category == "MATCH" or category == "ROUNDING_DIFFERENCE":
            continue
        metric = _base_metric(str(row.get("metric_name", "")))
        if category == "MISSING_RUBRIC_MAPPING":
            needed = f"Rubric thresholds and source signals for {metric}"
        elif category == "FORMULA_NOT_RECONSTRUCTABLE" or metric in SOURCE_PRESERVED_NOT_RECOMPUTED:
            needed = f"Exact formula/normalization and supporting inputs for {metric}"
        elif category == "INSUFFICIENT_SOURCE_DATA":
            needed = "Recovered session-level rows, per-cell supplementary statistics, or supporting raw fields"
        else:
            needed = "Manual audit of source value and computation formula"
        rows.append(
            {
                "metric_name": row.get("metric_name"),
                "level": row.get("level"),
                "category": category,
                "needed_input": needed,
                "reason": row.get("explanation"),
            }
        )
    return pd.DataFrame(rows, columns=NEEDS_INPUT_COLUMNS)


def paper_ready_metrics(source: dict[str, Any], grouped_validation: pd.DataFrame) -> pd.DataFrame:
    """Flatten provided source values into a paper-ready table with status notes."""

    status_lookup = {
        row["metric_name"]: row["reproducibility_status"]
        for _, row in grouped_validation.iterrows()
        if pd.notna(row.get("metric_name"))
    }
    note_lookup = {
        row["metric_name"]: row["explanation"]
        for _, row in grouped_validation.iterrows()
        if pd.notna(row.get("metric_name"))
    }

    rows: list[dict[str, Any]] = []
    source_path = "data/source/provided_paper_data.json"

    for approach, metrics in source.get("aggregated_means_per_approach", {}).items():
        for source_metric, value in metrics.items():
            metric = METRIC_ALIASES.get(source_metric, source_metric)
            key = f"{metric}:{approach}"
            rows.append(
                {
                    "level": "approach",
                    "approach": approach,
                    "task_id": pd.NA,
                    "metric_name": metric,
                    "value": value,
                    "source_path": source_path,
                    "reproducibility_status": status_lookup.get(key, "PRESERVED_SOURCE_VALUE"),
                    "note": note_lookup.get(key, "Author-provided approach-level paper value."),
                }
            )

    for source_metric, by_approach in source.get("task_level_values", {}).items():
        metric = SOURCE_TASK_METRICS.get(source_metric, source_metric)
        for approach, by_task in by_approach.items():
            for task_id, value in by_task.items():
                key = f"{metric}:{approach}:{task_id}"
                rows.append(
                    {
                        "level": "cell",
                        "approach": approach,
                        "task_id": task_id,
                        "metric_name": metric,
                        "value": value,
                        "source_path": source_path,
                        "reproducibility_status": status_lookup.get(key, "PRESERVED_SOURCE_VALUE"),
                        "note": note_lookup.get(key, "Author-provided task-level value."),
                    }
                )

    for approach, metrics in source.get("layer_specific_quality", {}).items():
        for metric, value in metrics.items():
            rows.append(
                {
                    "level": "approach_layer",
                    "approach": approach,
                    "task_id": pd.NA,
                    "metric_name": metric,
                    "value": value,
                    "source_path": source_path,
                    "reproducibility_status": "MISSING_RUBRIC_MAPPING",
                    "note": "Layer-specific paper value was provided, but supporting rubric thresholds and source signals were not recovered.",
                }
            )

    for metric, value in source.get("correlations", {}).items():
        rows.append(
            {
                "level": "correlation",
                "approach": pd.NA,
                "task_id": pd.NA,
                "metric_name": metric,
                "value": value,
                "source_path": source_path,
                "reproducibility_status": status_lookup.get(metric, "PRESERVED_SOURCE_VALUE"),
                "note": note_lookup.get(metric, "Author-provided correlation value."),
            }
        )

    return pd.DataFrame(rows, columns=PAPER_READY_COLUMNS)


def reproducibility_overview(grouped_validation: pd.DataFrame) -> pd.DataFrame:
    """Summarize validation categories for reviewer inspection."""

    counts = grouped_validation["category"].value_counts().to_dict()
    rows = []
    for category in VALIDATION_CATEGORIES:
        interpretation, risk, action = CATEGORY_DETAILS[category]
        rows.append(
            {
                "category": category,
                "count": int(counts.get(category, 0)),
                "interpretation": interpretation,
                "reviewer_risk_level": risk,
                "action_needed": action,
            }
        )
    return pd.DataFrame(rows, columns=OVERVIEW_COLUMNS)
