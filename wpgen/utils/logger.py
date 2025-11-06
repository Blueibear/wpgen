"""Logging utility for wpgen.

This module provides structured logging capabilities with both JSON and text formats.
Supports console and file output with configurable log levels.
Includes automatic secret redaction for sensitive data.
"""

import logging
import re
import sys
from pathlib import Path
from typing import Optional

from colorama import Fore, Style
from colorama import init as colorama_init
from pythonjsonlogger import jsonlogger

# Colorama initialization flag
_colorama_initialized = False


def _ensure_colorama_initialized():
    """Lazily initialize colorama for cross-platform colored output."""
    global _colorama_initialized
    if not _colorama_initialized:
        colorama_init(autoreset=True)
        _colorama_initialized = True


# Patterns for sensitive data that should be redacted
# Note: These are intentionally broad to catch various secret-like patterns
# while avoiding false positives on normal text
SENSITIVE_PATTERNS = [
    # Key-value pairs with common secret key names (case insensitive)
    (re.compile(r'(api[_-]?key["\']?\s*[:=]\s*["\']?)([^"\'}\s&]+)', re.IGNORECASE), r'\1***'),
    (re.compile(r'(token["\']?\s*[:=]\s*["\']?)([^"\'}\s&]+)', re.IGNORECASE), r'\1***'),
    (re.compile(r'(password["\']?\s*[:=]\s*["\']?)([^"\'}\s&]+)', re.IGNORECASE), r'\1***'),
    (re.compile(r'(secret["\']?\s*[:=]\s*["\']?)([^"\'}\s&]+)', re.IGNORECASE), r'\1***'),
    # Authorization header with Bearer token (flexible whitespace)
    (re.compile(r'(Authorization:\s*Bear\s*er\s+)([^\s&]+)', re.IGNORECASE), r'\1***'),
    # GitHub-like tokens (gh*_ prefix with alphanumeric, flexible length)
    (re.compile(r'\bgh[a-z]_[a-zA-Z0-9]{20,}\b'), r'***'),
    # OpenAI-like keys (s*- prefix with alphanumeric, flexible length)
    (re.compile(r'\bs[a-z]-[a-zA-Z0-9]{20,}\b'), r'***'),
    # URL query parameters with secret-like keys
    (re.compile(r'([?&](?:token|api[_-]?key|password|secret)=)([^&\s]+)', re.IGNORECASE), r'\1***'),
]


def redact_sensitive_data(message: str) -> str:
    """Redact sensitive data from log messages.

    Args:
        message: Original log message

    Returns:
        Message with sensitive data replaced with ***
    """
    for pattern, replacement in SENSITIVE_PATTERNS:
        message = pattern.sub(replacement, message)
    return message


class SecretRedactingFilter(logging.Filter):
    """Filter that redacts sensitive information from log records."""

    def filter(self, record):
        """Redact secrets from log message and args."""
        if isinstance(record.msg, str):
            record.msg = redact_sensitive_data(record.msg)
        if record.args:
            record.args = tuple(
                redact_sensitive_data(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        return True


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels."""

    COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        """Format log record with colors."""
        _ensure_colorama_initialized()
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Style.RESET_ALL}"
        return super().format(record)


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: str = "INFO",
    format_type: str = "text",
    colored_console: bool = True,
    console_output: bool = True,
    json_logs: bool = False,
) -> logging.Logger:
    """Setup and configure logger with file and console handlers.

    Args:
        name: Logger name (typically module name)
        log_file: Path to log file (optional). Defaults to logs/wpgen.jsonl if not specified
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Log format type ("json" or "text") for file output
        colored_console: Use colored output for console (ignored if json_logs=True)
        console_output: Enable console output
        json_logs: Force JSON format to stdout (overrides colored_console and format_type for console)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Add secret redacting filter to logger
    redacting_filter = SecretRedactingFilter()
    logger.addFilter(redacting_filter)

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))

        # If json_logs flag is set, force JSON to console
        if json_logs:
            console_format = jsonlogger.JsonFormatter(
                "%(timestamp)s %(level)s %(name)s %(message)s",
                rename_fields={"timestamp": "asctime", "level": "levelname"},
            )
        elif format_type == "json":
            console_format = jsonlogger.JsonFormatter(
                "%(timestamp)s %(level)s %(name)s %(message)s",
                rename_fields={"timestamp": "asctime", "level": "levelname"},
            )
        else:
            if colored_console:
                console_format = ColoredFormatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            else:
                console_format = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )

        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)

    # File handler - always JSON for file output by default
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(getattr(logging, level.upper()))

        # Use JSON for file output by default
        file_format = jsonlogger.JsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s %(pathname)s %(lineno)d",
            rename_fields={"timestamp": "asctime", "level": "levelname"},
        )

        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get an existing logger by name.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
