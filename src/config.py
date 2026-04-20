"""Configuration constants and path handling for the reconstructed package."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


APPROACHES = ("Manual", "Full-AI", "Hybrid")
TASKS = ("T1", "T2", "T3", "T4", "T5")
REPETITIONS = (1, 2, 3)

RAW_NUMERIC_METRICS = (
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
)

RUBRIC_METRICS = (
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
)

LAYER_QUALITY_METRICS = (
    "HTML",
    "CSS",
    "Front-End Logic",
    "Backend",
)

SOURCE_PRESERVED_NOT_RECOMPUTED = (
    "tdi",
)

VALIDATION_CATEGORIES = (
    "MATCH",
    "INSUFFICIENT_SOURCE_DATA",
    "MISSING_RUBRIC_MAPPING",
    "ROUNDING_DIFFERENCE",
    "FORMULA_NOT_RECONSTRUCTABLE",
    "TRUE_MISMATCH",
)

DERIVED_METRICS = (
    "tdi",
    "cfr",
    "productivity",
    "stability",
    "risk_score",
    "rework_ratio",
    "layer_imbalance_score",
)

METRIC_ALIASES = {
    "development_time_min": "dev_time_min",
    "average_cc": "cc_avg",
    "test_coverage_pct": "coverage_pct",
    "performance_score_1_to_5": "perf_score",
    "scalability_score_1_to_5": "scalability_score",
}

SOURCE_TASK_METRICS = {
    "development_time_min": "dev_time_min",
    "maintainability_index": "maintainability_index",
    "bugs_pre_release": "bugs_pre_release",
    "security_issues": "security_issues",
    "rework_ratio": "rework_ratio",
}


@dataclass(frozen=True)
class PathConfig:
    """Repository path layout.

    Defaults assume commands are run from the repository root. Passing a
    different root makes the code easy to test from temporary directories.
    """

    root: Path = Path(".")

    @property
    def data_raw(self) -> Path:
        return self.root / "data" / "raw"

    @property
    def data_source(self) -> Path:
        return self.root / "data" / "source"

    @property
    def data_processed(self) -> Path:
        return self.root / "data" / "processed"

    @property
    def raw_measurements(self) -> Path:
        return self.data_raw / "raw_measurements.csv"

    @property
    def provided_paper_data(self) -> Path:
        return self.data_source / "provided_paper_data.json"

    @property
    def rubric_mappings(self) -> Path:
        return self.data_raw / "rubric_mappings.csv"

    @property
    def session_manifest(self) -> Path:
        return self.data_raw / "session_manifest.csv"

    @property
    def reconstructed_measurements(self) -> Path:
        return self.data_processed / "reconstructed_measurements.csv"

    @property
    def per_cell_summary(self) -> Path:
        return self.data_processed / "per_cell_summary.csv"

    @property
    def per_approach_summary(self) -> Path:
        return self.data_processed / "per_approach_summary.csv"

    @property
    def validation_report(self) -> Path:
        return self.data_processed / "validation_report.csv"

    @property
    def validation_report_grouped(self) -> Path:
        return self.data_processed / "validation_report_grouped.csv"

    @property
    def needs_additional_inputs(self) -> Path:
        return self.data_processed / "needs_additional_inputs.csv"

    @property
    def paper_ready_metrics(self) -> Path:
        return self.data_processed / "paper_ready_metrics.csv"

    @property
    def reproducibility_overview(self) -> Path:
        return self.data_processed / "reproducibility_overview.csv"

    @property
    def reports_tables(self) -> Path:
        return self.root / "reports" / "tables"

    @property
    def reports_figures(self) -> Path:
        return self.root / "reports" / "figures"
