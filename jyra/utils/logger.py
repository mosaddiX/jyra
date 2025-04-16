"""
Logging utilities for Jyra
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from jyra.utils.config import LOG_LEVEL

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)


def setup_logger(name: str) -> logging.Logger:
    """
    Set up and return a logger with the given name.

    Args:
        name (str): Name of the logger

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # Create a file handler that logs even debug messages
    file_handler = RotatingFileHandler(
        "logs/jyra.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(getattr(logging, LOG_LEVEL))

    # Create console handler with the same log level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL))

    # Create formatter and add it to the handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
