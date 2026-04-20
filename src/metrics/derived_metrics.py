"""Derived metric formulas.

All functions return ``pd.NA`` when required inputs are missing. Formulas:

- CFR: ``bugs_post_integration / (bugs_pre_release + bugs_post_integration) * 100``.
- Productivity: ``loc / dev_time_min``.
- Stability: ``pass_rate_pct * integration_success - 5 * bugs_post_integration`` clipped to [0, 100].
- Risk Score: ``security_issues + 5*critical_security + 2*bugs_post_integration + code_smells/10``.
- Rework Ratio: ``abs(refactor_delta_loc) / loc``.
- Layer Imbalance Score: coefficient of variation of layer mean rubric scores.

TDI is preserved from the author-provided source data but is not recomputed
because the exact paper formula/normalization was not recovered.
"""

from __future__ import annotations

import math
from typing import Iterable

import pandas as pd


def _num(row: pd.Series, key: str) -> float | None:
    value = row.get(key)
    if pd.isna(value):
        return None
    return float(value)


def _require(row: pd.Series, keys: Iterable[str]) -> list[float] | None:
    values = [_num(row, key) for key in keys]
    if any(value is None for value in values):
        return None
    return [float(value) for value in values if value is not None]


def rework_ratio(row: pd.Series) -> float | pd._libs.missing.NAType:
    values = _require(row, ["refactor_delta_loc", "loc"])
    if values is None or values[1] == 0:
        return pd.NA
    return abs(values[0]) / values[1]


def productivity(row: pd.Series) -> float | pd._libs.missing.NAType:
    values = _require(row, ["loc", "dev_time_min"])
    if values is None or values[1] == 0:
        return pd.NA
    return values[0] / values[1]


def cfr(row: pd.Series) -> float | pd._libs.missing.NAType:
    values = _require(row, ["bugs_pre_release", "bugs_post_integration"])
    if values is None:
        return pd.NA
    total = values[0] + values[1]
    if total == 0:
        return 0.0
    return 100 * values[1] / total


def stability(row: pd.Series) -> float | pd._libs.missing.NAType:
    values = _require(row, ["pass_rate_pct", "integration_success", "bugs_post_integration"])
    if values is None:
        return pd.NA
    return max(0.0, min(100.0, values[0] * values[1] - 5 * values[2]))


def risk_score(row: pd.Series) -> float | pd._libs.missing.NAType:
    values = _require(row, ["security_issues", "critical_security", "bugs_post_integration", "code_smells"])
    if values is None:
        return pd.NA
    return values[0] + 5 * values[1] + 2 * values[2] + values[3] / 10


def tdi(row: pd.Series) -> float | pd._libs.missing.NAType:
    """Return missing because the exact paper TDI formula was not recovered."""

    return pd.NA


def layer_imbalance_score(row: pd.Series) -> float | pd._libs.missing.NAType:
    groups = [
        ["html_structural_clarity", "html_semantic_correctness", "html_accessibility"],
        ["css_style_consistency", "css_design_system_compliance", "css_override_conflicts"],
        ["fe_logic_correctness", "fe_edge_case_coverage", "fe_state_coherence", "fe_async_handling"],
        [
            "be_api_alignment",
            "be_authentication_correctness",
            "be_authorization_accuracy",
            "be_db_consistency",
            "be_validation_robustness",
            "be_security_exposure",
        ],
    ]
    means: list[float] = []
    for group in groups:
        values = [_num(row, key) for key in group]
        if any(value is None for value in values):
            return pd.NA
        means.append(sum(float(value) for value in values if value is not None) / len(values))
    mean = sum(means) / len(means)
    if mean == 0:
        return pd.NA
    variance = sum((value - mean) ** 2 for value in means) / len(means)
    return math.sqrt(variance) / mean


def add_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived metrics, preserving author-provided derived values."""

    result = df.copy()
    formulas = {
        "rework_ratio": rework_ratio,
        "productivity": productivity,
        "cfr": cfr,
        "stability": stability,
        "risk_score": risk_score,
        "layer_imbalance_score": layer_imbalance_score,
    }
    for metric, formula in formulas.items():
        computed = result.apply(formula, axis=1)
        if metric in result.columns:
            result[metric] = result[metric].where(result[metric].notna(), computed)
        else:
            result[metric] = computed
    return result
