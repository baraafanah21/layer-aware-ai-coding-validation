"""Command-line entry point for the reconstructed reproducibility package."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.config import PathConfig
from src.metrics.aggregate_metrics import per_approach_summary, per_cell_summary
from src.metrics.derived_metrics import add_derived_metrics
from src.metrics.direct_metrics import write_raw_reconstruction
from src.metrics.rubric_metrics import apply_rubric_scores, missing_rubric_template
from src.metrics.validation import (
    group_validation_report,
    needs_additional_inputs,
    paper_ready_metrics,
    reproducibility_overview,
    validate_source_against_outputs,
)
from src.schemas import RAW_MEASUREMENT_COLUMNS
from src.utils.io import load_json, read_csv, write_csv
from src.utils.logging_utils import setup_logging
from src.utils.paths import ensure_repo_structure


def run(root: Path) -> None:
    """Reconstruct raw CSVs, compute summaries, and validate source values."""

    logger = setup_logging()
    paths = PathConfig(root=root)
    ensure_repo_structure(root)

    source = load_json(paths.provided_paper_data)
    if not isinstance(source, dict):
        raise FileNotFoundError(f"Missing or invalid source data: {paths.provided_paper_data}")

    logger.info("Reconstructing raw files from author-provided source data")
    raw, manifest = write_raw_reconstruction(source)
    rubrics = missing_rubric_template()
    write_csv(raw[RAW_MEASUREMENT_COLUMNS], paths.raw_measurements)
    write_csv(manifest, paths.session_manifest)
    write_csv(rubrics, paths.rubric_mappings)

    logger.info("Computing derived metrics and summaries")
    measurements = apply_rubric_scores(raw, rubrics)
    measurements = add_derived_metrics(measurements)
    cell_summary = per_cell_summary(measurements)
    approach_summary = per_approach_summary(measurements)
    validation = validate_source_against_outputs(source, cell_summary, approach_summary)

    logger.info("Writing processed outputs")
    write_csv(measurements, paths.reconstructed_measurements)
    write_csv(cell_summary, paths.per_cell_summary)
    write_csv(approach_summary, paths.per_approach_summary)
    write_csv(validation, paths.validation_report)

    logger.info("Classifying validation results")
    validation_from_disk = read_csv(paths.validation_report)
    grouped = group_validation_report(validation_from_disk)
    needs_inputs = needs_additional_inputs(grouped)
    paper_metrics = paper_ready_metrics(source, grouped)
    overview = reproducibility_overview(grouped)
    write_csv(grouped, paths.validation_report_grouped)
    write_csv(needs_inputs, paths.needs_additional_inputs)
    write_csv(paper_metrics, paths.paper_ready_metrics)
    write_csv(overview, paths.reproducibility_overview)

    summary = overview.set_index("category")["count"]
    logger.info("Reproducibility summary:\n%s", summary.to_string())
    print("Reproducibility summary")
    for category, count in summary.items():
        print(f"- {category}: {count}")
    print("- package_type: reconstructed validation package, not full raw reproduction")
    contradiction_count = int(summary.get("TRUE_MISMATCH", 0))
    contradiction_text = "none" if contradiction_count == 0 else str(contradiction_count)
    print(f"- critical_contradictions: {contradiction_text}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the reconstructed reproducibility pipeline.")
    parser.add_argument("--root", type=Path, default=Path("."), help="Repository root.")
    args = parser.parse_args()
    run(args.root)


if __name__ == "__main__":
    main()
