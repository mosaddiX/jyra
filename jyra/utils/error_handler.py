"""
Centralized error handling for Jyra bot.

This module provides a centralized error handling system for the Jyra bot.
It includes functions for handling different types of errors, logging them,
and providing appropriate user-friendly messages.
"""

import traceback
from typing import Callable, Any, Optional, Dict, Type, Union
from functools import wraps
import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from jyra.utils.exceptions import (
    JyraException, DatabaseException, APIException,
    UserInputException, ConfigException, FeatureException,
    PermissionException
)
from jyra.utils.logger import setup_logger
from jyra.ui.visual_feedback import (
    show_error_message, stop_loading_indicator
)

logger = setup_logger(__name__)

# Error response templates
ERROR_RESPONSES = {
    DatabaseException: "I'm having trouble accessing my memory right now. Please try again later.",
    APIException: "I'm having trouble connecting to my AI brain. Please try again in a moment.",
    UserInputException: "I couldn't understand that input. Could you try again?",
    ConfigException: "There's a configuration issue with my system. Please contact support.",
    FeatureException: "That feature isn't available right now. Please try something else.",
    PermissionException: "You don't have permission to do that. Please try something else.",
    JyraException: "Something went wrong. Please try again or contact support.",
    Exception: "An unexpected error occurred. Please try again later."
}

# Technical details visibility level
# 0 = No technical details
# 1 = Basic error message
# 2 = Detailed error message with exception type
# 3 = Full traceback (only for development)
TECHNICAL_DETAIL_LEVEL = 1


async def handle_error(
    exception: Exception,
    update: Optional[Update] = None,
    context: Optional[ContextTypes.DEFAULT_TYPE] = None
) -> str:
    """
    Handle an exception and return an appropriate user-friendly message.

    Args:
        exception: The exception to handle
        update: The update object (optional)
        context: The context object (optional)

    Returns:
        A user-friendly error message
    """
    # Get exception details
    exc_type = type(exception)
    exc_message = str(exception)
    exc_traceback = traceback.format_exc()

    # Log the error
    logger.error(f"Error: {exc_type.__name__}: {exc_message}")
    if TECHNICAL_DETAIL_LEVEL >= 3:
        logger.error(f"Traceback: {exc_traceback}")

    # Find the most specific error response
    response = ERROR_RESPONSES.get(Exception)
    for exc_class, resp in ERROR_RESPONSES.items():
        if isinstance(exception, exc_class) and exc_class != Exception:
            response = resp
            break

    # Add technical details if configured
    details = None
    if TECHNICAL_DETAIL_LEVEL >= 1:
        details = exc_message
    if TECHNICAL_DETAIL_LEVEL >= 2:
        details = f"{exc_type.__name__}: {exc_message}"

    # Stop any loading indicators
    if context:
        try:
            await stop_loading_indicator(context, False, "Error occurred")
        except Exception as e:
            logger.error(f"Error stopping loading indicator: {e}")

    # Show error message to user if update and context are provided
    if update and context:
        try:
            await show_error_message(update, context, response, details)
        except Exception as e:
            logger.error(f"Error showing error message: {e}")

    return response


def handle_exceptions(func: Callable) -> Callable:
    """
    Decorator to handle exceptions in functions.

    This decorator can be used with different types of functions:
    - Telegram handler functions (with update and context)
    - Database methods (with or without arguments)
    - Other async functions

    Args:
        func: The function to decorate

    Returns:
        The decorated function
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Check if this is a Telegram handler (first two args are update and context)
            if len(args) >= 2 and isinstance(args[0], Update) and isinstance(args[1], ContextTypes.DEFAULT_TYPE):
                update, context = args[0], args[1]
                await handle_error(e, update, context)
            else:
                # For non-Telegram functions, just log the error
                await handle_error(e)
            # Return None to prevent further processing
            return None

    return wrapper


def handle_background_exceptions(func: Callable) -> Callable:
    """
    Decorator to handle exceptions in background tasks.

    Args:
        func: The function to decorate

    Returns:
        The decorated function
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            await handle_error(e)
            # Return None to prevent further processing
            return None

    return wrapper


def run_in_background(func: Callable) -> Callable:
    """
    Decorator to run a function in the background.

    Args:
        func: The function to decorate

    Returns:
        The decorated function
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> asyncio.Task:
        # Create a background task
        task = asyncio.create_task(
            handle_background_exceptions(func)(*args, **kwargs)
        )
        return task

    return wrapper


def set_technical_detail_level(level: int) -> None:
    """
    Set the technical detail level for error messages.

    Args:
        level: The detail level (0-3)
    """
    global TECHNICAL_DETAIL_LEVEL
    if 0 <= level <= 3:
        TECHNICAL_DETAIL_LEVEL = level
    else:
        raise ValueError("Technical detail level must be between 0 and 3")
