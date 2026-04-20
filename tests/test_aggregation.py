from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.metrics.aggregate_metrics import per_approach_summary, per_cell_summary
from src.metrics.direct_metrics import write_raw_reconstruction


def test_reconstruction_does_not_invent_session_rows() -> None:
    source = json.loads(Path("data/source/provided_paper_data.json").read_text())
    raw, manifest = write_raw_reconstruction(source)

    assert len(raw) == 15
    assert len(manifest) == 15
    assert set(raw["repetition"]) == {"MISSING"}
    assert raw["session_id"].isna().all()


def test_approach_aggregation_matches_supported_means() -> None:
    source = json.loads(Path("data/source/provided_paper_data.json").read_text())
    raw, _ = write_raw_reconstruction(source)

    approach = per_approach_summary(raw)
    manual = approach[approach["approach"] == "Manual"].iloc[0]

    assert manual["dev_time_min_mean"] == 291
    assert manual["maintainability_index_mean"] == 76.34
    assert manual["bugs_pre_release_mean"] == 2


def test_cell_summary_contains_one_directly_supported_value_per_cell() -> None:
    source = json.loads(Path("data/source/provided_paper_data.json").read_text())
    raw, _ = write_raw_reconstruction(source)

    cell = per_cell_summary(raw)
    manual_t1 = cell[(cell["approach"] == "Manual") & (cell["task_id"] == "T1")].iloc[0]

    assert manual_t1["dev_time_min_mean"] == 95
    assert manual_t1["dev_time_min_count"] == 1
