from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUEST_LOG_PATH = PROJECT_ROOT / "log.txt"
ERROR_LOG_PATH = PROJECT_ROOT / "error.txt"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"


def _configure_logger(name: str, path: Path, level: int) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(handler)
    return logger


@lru_cache(maxsize=1)
def get_request_logger() -> logging.Logger:
    return _configure_logger("dl_api.requests", REQUEST_LOG_PATH, logging.INFO)


@lru_cache(maxsize=1)
def get_error_logger() -> logging.Logger:
    return _configure_logger("dl_api.errors", ERROR_LOG_PATH, logging.ERROR)
