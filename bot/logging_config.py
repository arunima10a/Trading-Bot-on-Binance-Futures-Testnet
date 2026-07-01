"""Application logging configuration"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# shared log format
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_NOISY_LOGGERS = ("urllib3", "binance", "asyncio")


def configure_logging(
    log_dir: str | Path = "logs",
    log_file: str = "trading_bot.log",
    console_level: int = logging.INFO,
    max_bytes: int = 1_000_000,
    backup_count: int = 5,
) -> None:
    
    """Configure application logging."""
    
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)  # let handlers decide what to emit

    # Removing existing handlers to avoid duplicates
    for handler in list(root.handlers):
        root.removeHandler(handler)

    # File logging
    file_handler = RotatingFileHandler(
        log_path / log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # Console logging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    for noisy in _NOISY_LOGGERS:
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)