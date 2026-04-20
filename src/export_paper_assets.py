"""Export paper-ready tables and per-task figures from preserved/reconstructed data.

This module produces line-chart figures per task (T1-T5) across the three
approaches, which matches how the figures are referenced in the paper. The
original approach-level bar charts have been replaced by per-task trends
because the paper's narrative depends on task-by-task comparison.
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd

from src.config import METRIC_ALIASES, PathConfig, SOURCE_TASK_METRICS
from src.utils.io import load_json, read_csv, write_csv
from src.utils.logging_utils import setup_logging
from src.utils.paths import ensure_repo_structure

LOGGER = logging.getLogger(__name__)


APPROACH_ORDER = ["Manual", "Full-AI", "Hybrid"]
TASK_ORDER = ["T1", "T2", "T3", "T4", "T5"]
COLORS = {"Manual": "#1f77b4", "Full-AI": "#d62728", "Hybrid": "#2ca02c"}
MARKERS = {"Manual": "o", "Full-AI": "s", "Hybrid": "^"}

# Per-task critical security findings reported in the paper (Full-AI only).
CRITICAL_FULL_AI = {"T1": 0, "T2": 1, "T3": 3, "T4": 5, "T5": 2}


def _approach_metrics(source: dict[str, Any], paper_ready: pd.DataFrame) -> pd.DataFrame:
    """Approach-level paper table from preserved source values."""

    status = paper_ready[paper_ready["level"] == "approach"][
        ["approach", "metric_name", "reproducibility_status", "note"]
    ]
    rows = []
    for approach, metrics in source.get("aggregated_means_per_approach", {}).items():
        for source_metric, value in metrics.items():
            metric = METRIC_ALIASES.get(source_metric, source_metric)
            rows.append({"approach": approach, "metric_name": metric, "value": value})
    table = pd.DataFrame(rows)
    if not table.empty:
        table = table.merge(status, on=["approach", "metric_name"], how="left")
    return table


def _task_metrics(source: dict[str, Any], paper_ready: pd.DataFrame) -> pd.DataFrame:
    """Task-level table from values directly provided in the source."""

    status = paper_ready[paper_ready["level"] == "cell"][
        ["approach", "task_id", "metric_name", "reproducibility_status", "note"]
    ]
    rows = []
    for source_metric, by_approach in source.get("task_level_values", {}).items():
        metric = SOURCE_TASK_METRICS.get(source_metric, source_metric)
        for approach, by_task in by_approach.items():
            for task_id, value in by_task.items():
                rows.append(
                    {
                        "approach": approach,
                        "task_id": task_id,
                        "metric_name": metric,
                        "value": value,
                    }
                )
    table = pd.DataFrame(rows)
    if not table.empty:
        table = table.merge(
            status, on=["approach", "task_id", "metric_name"], how="left"
        )
    return table


def _layer_quality(source: dict[str, Any]) -> pd.DataFrame:
    """Layer quality values preserved from the source JSON."""

    frame = pd.DataFrame(source.get("layer_specific_quality", {})).T
    if frame.empty:
        return pd.DataFrame(columns=["approach", "layer", "value"])
    frame.index.name = "approach"
    return frame.reset_index().melt(
        id_vars="approach", var_name="layer", value_name="value"
    )


def _get_task_series(source: dict[str, Any], metric_key: str) -> dict[str, list[float]]:
    """Return {approach: [T1..T5 values]} for a task-level metric."""
    tasks = source.get("task_level_values", {})
    if metric_key not in tasks:
        return {}
    result = {}
    for approach in APPROACH_ORDER:
        if approach in tasks[metric_key]:
            result[approach] = [tasks[metric_key][approach][t] for t in TASK_ORDER]
    return result


def _plot_task_lines(
    source: dict[str, Any],
    metric_key: str,
    title: str,
    ylabel: str,
    path: Path,
    integer_ticks: bool = False,
) -> None:
    """Per-task line chart across approaches."""

    series = _get_task_series(source, metric_key)
    if not series:
        LOGGER.warning("No task-level data for %s; skipping figure.", metric_key)
        return
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for approach in APPROACH_ORDER:
        if approach in series:
            ax.plot(
                TASK_ORDER,
                series[approach],
                marker=MARKERS[approach],
                markersize=8,
                linewidth=2.2,
                label=approach,
                color=COLORS[approach],
            )
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_xlabel("Task", fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.legend(loc="best", frameon=True, framealpha=0.95)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    if integer_ticks:
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _plot_security_bars(source: dict[str, Any], path: Path) -> None:
    """Grouped bar chart for per-task security issues, critical portion hatched."""

    sec_series = _get_task_series(source, "security_issues")
    if not sec_series:
        return
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    x = list(range(len(TASK_ORDER)))
    width = 0.27
    for i, approach in enumerate(APPROACH_ORDER):
        if approach in sec_series:
            offsets = [xi + (i - 1) * width for xi in x]
            ax.bar(
                offsets,
                sec_series[approach],
                width,
                label=approach,
                color=COLORS[approach],
            )
            if approach == "Full-AI":
                crit_values = [CRITICAL_FULL_AI[t] for t in TASK_ORDER]
                ax.bar(
                    offsets,
                    crit_values,
                    width,
                    color="none",
                    edgecolor="black",
                    hatch="///",
                    linewidth=0.8,
                )
    ax.set_title(
        "Security Issues per Task (Critical Portion Hatched)",
        fontsize=13,
        fontweight="bold",
    )
    ax.set_xlabel("Task", fontsize=11)
    ax.set_ylabel("Issue Count", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(TASK_ORDER)
    handles, _ = ax.get_legend_handles_labels()
    crit_patch = mpatches.Patch(
        facecolor="white", edgecolor="black", hatch="///", label="Critical (Full-AI)"
    )
    ax.legend(
        handles=handles + [crit_patch], loc="upper left", frameon=True, framealpha=0.95
    )
    ax.grid(True, alpha=0.3, linestyle="--", axis="y")
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _plot_layer_quality(source: dict[str, Any], path: Path) -> None:
    """Grouped bar chart for layer-specific quality."""

    layer_data = source.get("layer_specific_quality", {})
    if not layer_data:
        return
    all_layers = set()
    for approach_layers in layer_data.values():
        all_layers.update(approach_layers.keys())
    layers = sorted(all_layers)
    fig, ax = plt.subplots(figsize=(10, 5))
    x = list(range(len(layers)))
    width = 0.27
    for i, approach in enumerate(APPROACH_ORDER):
        if approach in layer_data:
            values = [layer_data[approach].get(layer, 0) for layer in layers]
            offsets = [xi + (i - 1) * width for xi in x]
            ax.bar(
                offsets, values, width, label=approach, color=COLORS[approach]
            )
    ax.set_title("Layer-Specific Quality by Approach", fontsize=13, fontweight="bold")
    ax.set_xlabel("Layer-Specific Metric", fontsize=11)
    ax.set_ylabel("Score", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(layers, rotation=35, ha="right", fontsize=9)
    ax.legend(loc="best", frameon=True, framealpha=0.95)
    ax.grid(True, alpha=0.3, linestyle="--", axis="y")
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _write_summary(path: Path, overview: pd.DataFrame) -> None:
    """Plain-text explanation of exported assets."""

    lines = [
        "Paper assets summary",
        "",
        "This export uses preserved source values when full recomputation is unavailable.",
        "No values are fabricated, smoothed, or forced to match.",
        "",
        "Tables:",
        "- table1_ready.csv: preserved approach-level paper metrics with reproducibility status.",
        "- table2_ready.csv: directly provided task-level values with reproducibility status.",
        "- table3_ready.csv: validation category overview for reviewer inspection.",
        "",
        "Figures (per-task where task-level data is available):",
        "- figure1_development_time.png: development time trend per task, per approach.",
        "- figure2_maintainability_index.png: maintainability index per task, per approach.",
        "- figure3_pre_release_bugs.png: pre-release bugs per task, per approach.",
        "- figure4_security_issues.png: security issues per task with critical portion hatched.",
        "- figure5_rework_ratio.png: rework ratio per task, per approach.",
        "- figure6_layer_quality.png: preserved layer-specific quality values; rubric mappings are missing.",
        "",
        "Validation overview:",
    ]
    for _, row in overview.iterrows():
        lines.append(
            f"- {row['category']}: {row['count']} ({row['interpretation']}; risk={row['reviewer_risk_level']})"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_assets(root: Path) -> None:
    """Export all paper-ready tables, figures, and summary text."""

    paths = PathConfig(root=root)
    ensure_repo_structure(root)
    paths.reports_tables.mkdir(parents=True, exist_ok=True)
    paths.reports_figures.mkdir(parents=True, exist_ok=True)

    source = load_json(paths.provided_paper_data)
    if not isinstance(source, dict):
        raise FileNotFoundError(f"Missing or invalid source data: {paths.provided_paper_data}")

    paper_ready = read_csv(paths.paper_ready_metrics)
    overview = read_csv(paths.reproducibility_overview)
    if paper_ready.empty or overview.empty:
        raise FileNotFoundError("Run src.run_pipeline before exporting paper assets.")

    approach_table = _approach_metrics(source, paper_ready)
    task_table = _task_metrics(source, paper_ready)
    layer_table = _layer_quality(source)

    write_csv(approach_table, paths.reports_tables / "table1_ready.csv")
    write_csv(task_table, paths.reports_tables / "table2_ready.csv")
    write_csv(overview, paths.reports_tables / "table3_ready.csv")

    # Per-task line charts using task-level source data.
    _plot_task_lines(
        source,
        "development_time_min",
        "Development Time per Task",
        "Minutes",
        paths.reports_figures / "figure1_development_time.png",
    )
    _plot_task_lines(
        source,
        "maintainability_index",
        "Maintainability Index per Task",
        "Maintainability Index",
        paths.reports_figures / "figure2_maintainability_index.png",
    )
    _plot_task_lines(
        source,
        "bugs_pre_release",
        "Pre-Release Bugs per Task",
        "Bug Count",
        paths.reports_figures / "figure3_pre_release_bugs.png",
        integer_ticks=True,
    )
    _plot_security_bars(source, paths.reports_figures / "figure4_security_issues.png")
    _plot_task_lines(
        source,
        "rework_ratio",
        "Rework Ratio per Task",
        "Rework Ratio",
        paths.reports_figures / "figure5_rework_ratio.png",
    )
    _plot_layer_quality(source, paths.reports_figures / "figure6_layer_quality.png")

    _write_summary(root / "reports" / "paper_assets_summary.txt", overview)
    LOGGER.info("Exported paper-ready tables and per-task figures.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export paper-ready tables and figures.")
    parser.add_argument("--root", type=Path, default=Path("."), help="Repository root.")
    args = parser.parse_args()
    setup_logging()
    export_assets(args.root)


if __name__ == "__main__":
    main()
