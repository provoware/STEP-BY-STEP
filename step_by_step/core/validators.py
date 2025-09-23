"""Generic validation helpers (Prüfwerkzeuge) used across modules."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


def ensure_unique(values: Iterable[str]) -> bool:
    """Return *True* if all values are unique (einzigartig)."""

    lowered = [value.casefold() for value in values]
    return len(lowered) == len(set(lowered))


def ensure_existing_path(path: Path) -> bool:
    """Return *True* if the provided file exists on disk."""

    return path.exists()


__all__ = ["ensure_unique", "ensure_existing_path"]
