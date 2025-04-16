"""
Configuration utilities for Jyra
"""

import os
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
MAX_CONVERSATION_HISTORY: int = int(
    os.getenv("MAX_CONVERSATION_HISTORY", "10"))
DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "en")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# AI configuration
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

# Database configuration
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/jyra.db")

# Admin configuration
ADMIN_USER_IDS: List[int] = [
    int(id_str) for id_str in os.getenv("ADMIN_USER_IDS", "").split(",") if id_str
]


def validate_config() -> List[str]:
    """
    Validate the configuration and return a list of missing or invalid settings.

    Returns:
        List[str]: List of error messages for missing or invalid settings
    """
    errors = []

    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN is not set")

    if not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY is not set")

    if not DATABASE_PATH:
        errors.append("DATABASE_PATH is not set")

    return errors
