"""Utility helpers for safe file operations (Dateimanagement)."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Optional

DEFAULT_ENCODING = "utf-8"


def atomic_write_text(
    target_path: Path,
    content: str,
    *,
    encoding: str = DEFAULT_ENCODING,
    logger: Optional[logging.Logger] = None,
) -> bool:
    """Write ``content`` atomically to ``target_path``.

    The file is written to a temporary location within the same folder first and
    then moved into place.  This protects against partial writes when the
    process is interrupted.  Returns ``True`` on success.
    """

    target_path.parent.mkdir(parents=True, exist_ok=True)
    handle: Optional[tempfile.NamedTemporaryFile] = None
    temp_name: Optional[str] = None

    try:
        handle = tempfile.NamedTemporaryFile(
            "w",
            encoding=encoding,
            dir=str(target_path.parent),
            delete=False,
        )
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
        temp_name = handle.name
    except Exception as error:  # pragma: no cover - extremely unlikely edge case
        if logger is not None:
            logger.error("Temporäre Datei konnte nicht geschrieben werden: %s", error)
        return False
    finally:
        if handle is not None:
            handle.close()

    try:
        os.replace(temp_name, target_path)
    except OSError as error:
        if logger is not None:
            logger.error("Datei konnte nicht ersetzt werden (%s): %s", target_path, error)
        if temp_name and Path(temp_name).exists():
            Path(temp_name).unlink(missing_ok=True)
        return False

    return True


def atomic_write_json(
    target_path: Path,
    payload: Any,
    *,
    encoding: str = DEFAULT_ENCODING,
    logger: Optional[logging.Logger] = None,
) -> bool:
    """Serialise ``payload`` as JSON and write it atomically to ``target_path``."""

    try:
        content = json.dumps(payload, indent=2, ensure_ascii=False)
    except (TypeError, ValueError) as error:
        if logger is not None:
            logger.error("JSON konnte nicht serialisiert werden: %s", error)
        return False

    return atomic_write_text(target_path, content, encoding=encoding, logger=logger)


__all__ = ["atomic_write_json", "atomic_write_text"]

