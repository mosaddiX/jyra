"""
Handler for the /settings command.
"""

from telegram import Update
from telegram.ext import ContextTypes

from jyra.db.models.user import User
from jyra.ui.keyboards import create_settings_keyboard
from jyra.ui.messages import get_settings_message
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /settings command to adjust user preferences.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    user_id = update.effective_user.id

    # Get current preferences
    preferences = await User.get_user_preferences(user_id)
    
    # Store preferences in context for callback handlers
    context.user_data["preferences"] = preferences
    
    # Get settings message
    settings_text = get_settings_message("main")
    
    # Create settings keyboard
    keyboard = create_settings_keyboard()
    
    await update.message.reply_html(
        settings_text,
        reply_markup=keyboard
    )
