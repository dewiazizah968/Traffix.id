"""Structured logger access helpers for Traffix backend."""

import logging

from core.logging_config import LOGGER_NAMES, setup_logging

setup_logging()


def get_logger(name: str) -> logging.Logger:
    """Return a configured Traffix logger by domain name.

    Args:
        name: Logger domain name.

    Returns:
        Configured Python logger.

    Raises:
        ValueError: If the logger name is not supported.
    """
    if name not in LOGGER_NAMES:
        allowed = ", ".join(LOGGER_NAMES)
        raise ValueError(f"Unsupported logger name '{name}'. Allowed: {allowed}")
    return logging.getLogger(name)
