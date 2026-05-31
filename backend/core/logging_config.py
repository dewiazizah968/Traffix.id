"""Centralized logging configuration for Traffix backend."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILE_MAX_BYTES = 5 * 1024 * 1024
LOG_FILE_BACKUP_COUNT = 3
LOGGER_NAMES = (
    "system",
    "api",
    "ml",
    "simulation",
    "recommendation",
    "weather",
)

_LOGGING_CONFIGURED = False


class ColorFormatter(logging.Formatter):
    """Console formatter that colorizes log levels when ANSI is supported."""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log records with a colored level name.

        Args:
            record: Log record emitted by Python logging.

        Returns:
            Formatted log line.
        """
        original_levelname = record.levelname
        color = self.COLORS.get(original_levelname, "")
        if color:
            record.levelname = f"{color}{original_levelname}{self.RESET}"
        try:
            return super().format(record)
        finally:
            record.levelname = original_levelname


def _backend_root() -> Path:
    """Return the backend project root directory.

    Returns:
        Absolute path to the backend root.
    """
    return Path(__file__).resolve().parents[1]


def _build_formatter() -> logging.Formatter:
    """Create the shared log formatter.

    Returns:
        Configured logging formatter.
    """
    return logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)


def _build_console_formatter() -> logging.Formatter:
    """Create the console log formatter.

    Returns:
        Color formatter for TTY streams, otherwise the plain formatter.
    """
    if sys.stderr.isatty():
        return ColorFormatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)
    return _build_formatter()


def setup_logging(log_level: str = "INFO") -> None:
    """Configure console and rotating file logging for Traffix.

    Args:
        log_level: Minimum log level name.
    """
    global _LOGGING_CONFIGURED

    if _LOGGING_CONFIGURED:
        return

    logs_dir = _backend_root() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    file_formatter = _build_formatter()
    console_formatter = _build_console_formatter()
    level = getattr(logging, log_level.upper(), logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)

    file_handler = RotatingFileHandler(
        filename=logs_dir / "traffix.log",
        maxBytes=LOG_FILE_MAX_BYTES,
        backupCount=LOG_FILE_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(file_formatter)

    for logger_name in LOGGER_NAMES:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.handlers.clear()
        logger.propagate = False
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    _LOGGING_CONFIGURED = True
