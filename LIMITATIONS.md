# Limitations

## Missing 45 Session-Level Raw Rows

**What is missing:** The original repetition-level dataset for all 45 sessions is unavailable.

**Why it matters:** Full reproduction of per-session metrics, repetition variance, and some approach-level aggregates requires the session-level rows.

**Effect on reproducibility:** The repository does not invent those rows. It reconstructs only task/approach values directly supported by the provided source data and marks blocked approach-level values as `INSUFFICIENT_SOURCE_DATA`.

## Missing Rubric Mapping Thresholds

**What is missing:** The explicit rubric threshold tables and source-signal mappings for rubric-based metrics were not recovered.

**Why it matters:** Scores such as performance, scalability, and layer-specific quality cannot be independently recomputed without those mappings.

**Effect on reproducibility:** Rubric-derived values are preserved from the source data and labeled `MISSING_RUBRIC_MAPPING`.

## TDI Formula Or Normalization Not Recovered

**What is missing:** The exact TDI formula, normalization constants, or supporting fields used in the original study were not recovered.

**Why it matters:** A plausible formula can produce values that are numerically incompatible with the paper. Recomputing TDI without the original definition would be misleading.

**Effect on reproducibility:** TDI is preserved as an author-provided paper value and labeled `FORMULA_NOT_RECONSTRUCTABLE` / `INSUFFICIENT_SOURCE_DATA`. The pipeline does not compute a replacement value.

## Correlation Source Granularity Is Insufficient

**What is missing:** The full source matrix used for the reported correlations is unavailable for several required metrics, including LOC, average complexity, code smells, critical security findings, coverage, and post-integration bugs.

**Why it matters:** Correlations depend on the unit of analysis and source matrix. They cannot be verified from aggregate values alone.

**Effect on reproducibility:** Reported correlations are preserved from the original study and labeled `INSUFFICIENT_SOURCE_DATA` when they cannot be recomputed.

## Approach-Level Versus Task-Level Aggregation Limits

**What is missing:** Supplementary per-cell means/stds and session-level repetitions are unavailable for some metrics.

**Why it matters:** Some approach-level paper values may have been computed from repetition-level data or supplementary cells rather than from the task-level values currently available.

**Effect on reproducibility:** The pipeline reports these cases transparently as `INSUFFICIENT_SOURCE_DATA` rather than forcing task-level aggregates to match paper-level values.
