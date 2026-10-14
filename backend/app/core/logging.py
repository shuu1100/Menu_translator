"""Structured logging configuration with automatic redaction of base64 payloads."""

import logging
import re
import sys
from typing import Any, Dict


# Pattern to match raw base64 data URIs or base64 strings
BASE64_IMAGE_PATTERN = re.compile(
    r"(data:image\/[a-zA-Z0-9\+\-\.]+;base64,)[A-Za-z0-9+/=]{30,}",
    re.IGNORECASE,
)
GENERIC_BASE64_LONG_PATTERN = re.compile(
    r"(?:\'|\")?(?:[A-Za-z0-9+/]{80,}={0,2})(?:\'|\")?"
)


class Base64RedactionFilter(logging.Filter):
    """Filter that strips out base64 image strings and oversized base64 blobs from log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            # Redact data:image base64 URIs
            record.msg = BASE64_IMAGE_PATTERN.sub(
                r"\1[REDACTED_BASE64_IMAGE_PAYLOAD]",
                record.msg,
            )
            # Redact standalone very long base64 blocks to prevent token bloat/secrets leakage
            record.msg = GENERIC_BASE64_LONG_PATTERN.sub(
                "[REDACTED_BINARY_PAYLOAD]",
                record.msg,
            )
        return True


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure root and application loggers."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Format with timestamp, level, logger name, and message
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(Base64RedactionFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(handler)

    # Set specific log levels for third-party chatty libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logger = logging.getLogger("menu_translator")
    logger.setLevel(log_level)
    return logger


def get_logger(name: str = "menu_translator") -> logging.Logger:
    """Return a configured logger with standard application formatting."""
    return logging.getLogger(name)

