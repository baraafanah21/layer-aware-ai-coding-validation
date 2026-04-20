"""Filesystem helpers for the repository layout."""

from __future__ import annotations

from pathlib import Path


REQUIRED_DIRECTORIES = (
    "src/metrics",
    "src/utils",
    "data/source",
    "data/raw",
    "data/processed",
    "notebooks",
    "reports/tables",
    "reports/figures",
    "artifacts/placeholders",
)


def ensure_repo_structure(root: Path) -> None:
    """Create expected directories if they do not already exist."""

    for relative in REQUIRED_DIRECTORIES:
        (root / relative).mkdir(parents=True, exist_ok=True)


def resolve_optional_path(root: Path, maybe_path: object) -> Path | None:
    """Resolve a manifest path, returning None for blanks and missing values."""

    if maybe_path is None:
        return None
    text = str(maybe_path).strip()
    if not text or text.lower() in {"nan", "none", "<na>"}:
        return None
    path = Path(text)
    return path if path.is_absolute() else root / path
