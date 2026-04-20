from __future__ import annotations

import pandas as pd

from src.metrics.validation import (
    classify_validation_row,
    group_validation_report,
    reproducibility_overview,
    reproducibility_status_for,
)


def _row(metric: str, level: str, status: str, abs_diff: object = pd.NA, rel_diff: object = pd.NA) -> pd.Series:
    return pd.Series(
        {
            "metric_name": metric,
            "level": level,
            "expected_value": 1,
            "computed_value": 1,
            "abs_diff": abs_diff,
            "rel_diff_pct": rel_diff,
            "status": status,
        }
    )


def test_rounding_difference_classification() -> None:
    category, _, _ = classify_validation_row(
        _row("rework_ratio:Manual", "approach", "MISMATCH", abs_diff=0.0004, rel_diff=0.6)
    )

    assert category == "ROUNDING_DIFFERENCE"


def test_tdi_maps_to_formula_not_reconstructable_status() -> None:
    category, _, _ = classify_validation_row(_row("tdi:Manual", "approach", "MISSING_COMPUTED"))

    assert category == "FORMULA_NOT_RECONSTRUCTABLE"
    assert reproducibility_status_for("tdi:Manual", category) == "FORMULA_NOT_RECONSTRUCTABLE"


def test_rubric_mapping_classification() -> None:
    category, _, _ = classify_validation_row(_row("perf_score:Manual", "approach", "MISSING_COMPUTED"))

    assert category == "MISSING_RUBRIC_MAPPING"


def test_true_mismatch_is_reserved_for_unexplained_computable_conflicts() -> None:
    category, _, _ = classify_validation_row(
        _row("dev_time_min:Manual:T1", "cell", "MISMATCH", abs_diff=5, rel_diff=5)
    )

    assert category == "TRUE_MISMATCH"


def test_overview_includes_zero_true_mismatch_rows() -> None:
    validation = pd.DataFrame(
        [
            _row("dev_time_min:Manual:T1", "cell", "MATCH", abs_diff=0, rel_diff=0),
            _row("rework_ratio:Manual", "approach", "MISMATCH", abs_diff=0.0004, rel_diff=0.6),
        ]
    )
    grouped = group_validation_report(validation)
    overview = reproducibility_overview(grouped)

    true_mismatch = overview[overview["category"] == "TRUE_MISMATCH"].iloc[0]
    assert true_mismatch["count"] == 0
