"""Column schemas for source-derived CSV files."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnSpec:
    """A simple column contract used by validation and documentation."""

    name: str
    dtype: str
    description: str
    required: bool = False


RAW_MEASUREMENT_COLUMNS = [
    "session_id",
    "task_id",
    "approach",
    "repetition",
    "dev_time_min",
    "build_time_sec",
    "loc",
    "maintainability_index",
    "cc_avg",
    "cc_max",
    "code_smells",
    "eslint_warnings",
    "coverage_pct",
    "pass_rate_pct",
    "bugs_pre_release",
    "bugs_post_integration",
    "security_issues",
    "critical_security",
    "refactor_delta_loc",
    "integration_success",
    "perf_score",
    "scalability_score",
    "html_structural_clarity",
    "html_semantic_correctness",
    "html_accessibility",
    "css_style_consistency",
    "css_design_system_compliance",
    "css_override_conflicts",
    "fe_logic_correctness",
    "fe_edge_case_coverage",
    "fe_state_coherence",
    "fe_async_handling",
    "be_api_alignment",
    "be_authentication_correctness",
    "be_authorization_accuracy",
    "be_db_consistency",
    "be_validation_robustness",
    "be_security_exposure",
    "notes",
]

MANIFEST_COLUMNS = [
    "session_id",
    "task_id",
    "approach",
    "repetition",
    "source_type",
    "source_note",
    "status",
]

RUBRIC_MAPPING_COLUMNS = [
    "metric_name",
    "source_signals",
    "threshold_rule",
    "score_1",
    "score_2",
    "score_3",
    "score_4",
    "score_5",
    "comments",
]


def missing_columns(columns: list[str], required: list[str]) -> list[str]:
    """Return required columns that are absent from a file."""

    present = set(columns)
    return [column for column in required if column not in present]
