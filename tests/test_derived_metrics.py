from __future__ import annotations

import pandas as pd

from src.metrics.derived_metrics import add_derived_metrics, cfr, productivity, risk_score, tdi


def test_basic_derived_formulas_compute_when_inputs_exist() -> None:
    row = pd.Series(
        {
            "loc": 100,
            "dev_time_min": 20,
            "bugs_pre_release": 3,
            "bugs_post_integration": 1,
            "security_issues": 2,
            "critical_security": 1,
            "code_smells": 10,
        }
    )

    assert productivity(row) == 5
    assert cfr(row) == 25
    assert risk_score(row) == 10


def test_tdi_is_not_recomputed_without_recovered_formula() -> None:
    row = pd.Series(
        {
            "dev_time_min": 20,
            "rework_ratio": 0.1,
            "bugs_pre_release": 3,
            "security_issues": 2,
            "maintainability_index": 80,
        }
    )

    assert pd.isna(tdi(row))


def test_add_derived_metrics_preserves_existing_values() -> None:
    frame = pd.DataFrame(
        [
            {
                "loc": 100,
                "dev_time_min": 20,
                "rework_ratio": 0.123,
            }
        ]
    )

    result = add_derived_metrics(frame)

    assert result.loc[0, "rework_ratio"] == 0.123
