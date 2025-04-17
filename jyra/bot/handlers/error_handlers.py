"""
Error handlers for Jyra Telegram bot.

This module provides error handling for the Telegram bot, using the centralized
error handling system defined in jyra.utils.error_handler.
"""

import html
import traceback
import json
from typing import Optional

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from jyra.utils.config import ADMIN_USER_IDS
from jyra.utils.logger import setup_logger
from jyra.utils.error_handler import handle_error

logger = setup_logger(__name__)


async def error_handler(update: Optional[Update], context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle errors in the bot.

    This function is registered as the global error handler for the Telegram bot.
    It uses the centralized error handling system to process errors and send
    appropriate messages to users and admins.

    Args:
        update (Optional[Update]): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    # Get the exception
    exception = context.error

    # Use the centralized error handler to handle the error
    await handle_error(exception, update, context)

    # Additional admin notification with detailed information
    if ADMIN_USER_IDS:
        # Extract the error stack trace
        tb_list = traceback.format_exception(
            None, exception, exception.__traceback__)
        tb_string = "".join(tb_list)

        # Build the message for admins
        update_str = update.to_dict() if isinstance(update, Update) else str(update)
        message = (
            f"An exception occurred while processing an update:\n\n"
            f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}</pre>\n\n"
            f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
            f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
            f"<pre>{html.escape(tb_string)}</pre>"
        )

        # Send error message to admins
        for admin_id in ADMIN_USER_IDS:
            try:
                # First 4000 characters of the message (Telegram message limit)
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=message[:4000],
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                logger.error(
                    f"Failed to send error message to admin {admin_id}: {e}")
