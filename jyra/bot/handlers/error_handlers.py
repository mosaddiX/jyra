"""
Error handlers for Jyra Telegram bot
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

logger = setup_logger(__name__)


async def error_handler(update: Optional[Update], context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle errors in the bot.

    Args:
        update (Optional[Update]): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    # Log the error
    logger.error("Exception while handling an update:", exc_info=context.error)

    # Extract the error stack trace
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__)
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

    # If we have an update, send a message to the user
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "I'm sorry, but I encountered an error while processing your request. "
                "The issue has been reported to my developers."
            )
        except Exception as e:
            logger.error(f"Failed to send error message to user: {e}")
