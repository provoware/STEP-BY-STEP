"""Central logging setup (zentrale Protokollierung) for STEP-BY-STEP."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

LOG_DIR = Path("logs")
DEFAULT_LOG_FILE = LOG_DIR / "tool.log"


def setup_logging(log_file: Path = DEFAULT_LOG_FILE) -> logging.Logger:
    """Configure a root logger with console and file output."""

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("step_by_step")
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.debug("Logging initialised")
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a configured logger; create configuration if needed."""

    root_logger = setup_logging()
    return root_logger if name is None else root_logger.getChild(name)


__all__ = ["get_logger", "setup_logging", "DEFAULT_LOG_FILE"]
