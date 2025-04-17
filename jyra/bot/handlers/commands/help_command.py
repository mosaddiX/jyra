"""
Handler for the /help command.
"""

from telegram import Update
from telegram.ext import ContextTypes

from jyra.ui.keyboards import create_help_keyboard
from jyra.ui.messages import get_help_message
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /help command.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    # Get help message for main category
    help_text = get_help_message("main")
    
    # Create help keyboard
    keyboard = create_help_keyboard()
    
    # Send help message with keyboard
    await update.message.reply_html(
        help_text,
        reply_markup=keyboard
    )
