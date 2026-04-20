# Layer-Aware AI Coding — Reconstructed Validation Package

[![tests](https://github.com/baraafanah21/layer-aware-ai-coding-validation/actions/workflows/tests.yml/badge.svg)](https://github.com/baraafanah21/layer-aware-ai-coding-validation/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Companion repository for the paper **"Beyond Vibe Coding: A Layer-Aware Model for Integrating AI Assistance in Full-Stack Software Development."**

The study compares Manual, Full-AI, and Hybrid development across five full-stack tasks (T1–T5) with three repetitions per task-by-approach cell, for 45 sessions in total.

## What this repository is

A **reconstructed validation package**, not a full raw-data reproduction. After the experimental phase, some files were lost: the 45 session-level rows, the rubric threshold tables, and the original Technical Debt Index (TDI) formula were not fully preserved. The repository therefore:

- keeps every value reported in the paper at the task and approach levels, untouched,
- recomputes the aggregates that can be recomputed from the recovered task-level inputs,
- checks those recomputed values against the paper,
- labels every value with a reproducibility status so the boundary is visible rather than hidden.

**Nothing here is fabricated, smoothed, or forced to match the paper.**

## Current reproducibility status

| Category | Count | Meaning |
|---|---:|---|
| `MATCH` | 82 | Recomputed from available source data and consistent with the paper |
| `INSUFFICIENT_SOURCE_DATA` | 41 | Cannot be recomputed without the missing session-level rows |
| `MISSING_RUBRIC_MAPPING` | 6 | Depends on unrecovered rubric thresholds |
| `ROUNDING_DIFFERENCE` | 3 | Differs only within a small rounding tolerance |
| `FORMULA_NOT_RECONSTRUCTABLE` | 3 | Preserved (e.g., TDI): original formula not recovered |
| `TRUE_MISMATCH` | 0 | Direct contradiction — none currently detected |

## How to run

```bash
python3 -m pip install -r requirements.txt
./run_all.sh     # or: make all
```

Individual steps:

```bash
python3 -m src.run_pipeline --root .
python3 -m src.export_paper_assets --root .
pytest
```

## Repository structure

```
data/
  source/provided_paper_data.json   Preserved author-provided study values
  raw/raw_measurements.csv          Task-level values in the raw schema
  raw/session_manifest.csv          Placeholders documenting missing session artifacts
  raw/rubric_mappings.csv           Rubric template (thresholds marked MISSING)
  processed/                        Validation and reconstruction outputs

src/
  run_pipeline.py                   Validation + reconstruction pipeline
  export_paper_assets.py            Paper-ready tables and per-task figures
  metrics/                          Direct, rubric, derived, and aggregate metrics
  utils/                            I/O, logging, path handling
  config.py                         Metric aliases and paths

tests/                              11 pytest cases — pipeline correctness

reports/
  tables/                           Paper-ready CSV tables
  figures/                          Per-task figures (line charts by approach)

notebooks/
  analysis.ipynb                    Reviewer-oriented audit notebook

.github/workflows/tests.yml         CI on every push

LIMITATIONS.md                      What cannot be reproduced and why
REPRODUCIBILITY_STATEMENT.md        Formal reproducibility statement
PAPER_REPO_ALIGNMENT.md             Manuscript wording that matches this package
SUBMISSION_CHECKLIST.md             Pre-submission checklist
```

## What this repository reproduces

- Preservation of the author-provided source JSON (`data/source/provided_paper_data.json`).
- Task-level values that were recovered directly.
- Approach-level aggregates where the task-level inputs are available and sufficient.
- Per-task figures (development time, maintainability index, pre-release bugs, security issues, rework ratio) and the layer-specific quality chart.
- Validation categories visible per metric and aggregated overall.

## What this repository does not reproduce

- The original 45 session-level raw runs.
- Rubric-based scores whose threshold mappings were not recovered.
- TDI, because the exact formula or normalization used in the original study was not recovered.
- Correlations whose source matrix is unavailable for several required metrics.
- Any metric that requires missing supplementary per-cell statistics or raw tool artifacts.

## Figures

Figures in `reports/figures/` are per-task line charts (and a grouped bar chart for security issues) across the three approaches, matching how the figures are referenced in the paper. They are regenerated from preserved task-level data on every run; the logic lives in `src/export_paper_assets.py`.

## Notes for reviewers

This package is designed to make the reproducibility boundary visible, not to claim a full rerun of the original experiment. The strongest supported results are the task-level values that were recovered and the approach-level aggregates that can be recomputed from them. Metrics depending on missing session rows, unrecovered rubric mappings, unavailable correlation matrices, or the unrecovered TDI formula are preserved with explicit labels rather than silently recomputed.

See `LIMITATIONS.md` for the full list of what is missing and why, and `REPRODUCIBILITY_STATEMENT.md` for the formal statement.

## Citation

If you use this package, please cite the paper and the repository. See `CITATION.cff` for a machine-readable citation.

## License

MIT — see `LICENSE`.
