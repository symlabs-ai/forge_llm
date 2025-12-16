"""
LogService - Structured logging for ForgeLLM.

This is a temporary implementation until forge-base is available.
When forge-base is integrated, replace with ForgeBase's LogService.

Usage:
    from forge_llm.infrastructure.logging import get_logger

    logger = get_logger(__name__)
    logger.info("message", extra_field="value")
"""
import logging
import sys
from typing import Any


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


class LogService:
    """
    Structured logging service (ForgeBase stub).

    This class provides a structured logging interface compatible
    with ForgeBase's LogService. Replace with actual ForgeBase
    implementation when available.
    """

    def __init__(self, name: str) -> None:
        self._logger = get_logger(name)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with structured context."""
        self._logger.info(self._format_message(message, kwargs))

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with structured context."""
        self._logger.debug(self._format_message(message, kwargs))

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with structured context."""
        self._logger.warning(self._format_message(message, kwargs))

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message with structured context."""
        self._logger.error(self._format_message(message, kwargs))

    def _format_message(self, message: str, context: dict[str, Any]) -> str:
        """Format message with structured context."""
        if context:
            ctx_str = " | ".join(f"{k}={v}" for k, v in context.items())
            return f"{message} | {ctx_str}"
        return message
