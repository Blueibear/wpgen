"""Logging utility for wpgen.

This module provides structured logging capabilities with both JSON and text formats.
Supports console and file output with configurable log levels.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from pythonjsonlogger import jsonlogger
from colorama import Fore, Style, init as colorama_init


# Initialize colorama for cross-platform colored output
colorama_init(autoreset=True)


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
) -> logging.Logger:
    """Setup and configure logger with file and console handlers.

    Args:
        name: Logger name (typically module name)
        log_file: Path to log file (optional)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Log format type ("json" or "text")
        colored_console: Use colored output for console
        console_output: Enable console output

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))

        if format_type == "json":
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

    # File handler
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(getattr(logging, level.upper()))

        if format_type == "json":
            file_format = jsonlogger.JsonFormatter(
                "%(timestamp)s %(level)s %(name)s %(message)s %(pathname)s %(lineno)d",
                rename_fields={"timestamp": "asctime", "level": "levelname"},
            )
        else:
            file_format = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(pathname)s:%(lineno)d]",
                datefmt="%Y-%m-%d %H:%M:%S",
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
