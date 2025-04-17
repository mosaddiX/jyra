"""
Callback handlers for help menu interactions.
"""

from telegram import Update
from telegram.ext import ContextTypes

from jyra.ui.keyboards import create_help_keyboard
from jyra.ui.messages import get_help_message
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)

async def handle_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle help-related callback queries.
    
    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    # Extract the help category from the callback data
    if callback_data.startswith("help_"):
        category = callback_data[5:]  # Remove "help_" prefix
        
        # List of valid help categories (update as needed)
        valid_categories = ["basic", "roleplay", "memory", "settings", "advanced"]
        if category not in valid_categories:
            await query.message.edit_text(
                "Sorry, I don't recognize that help category. Please try again.",
                reply_markup=create_help_keyboard()
            )
            return

        # Stub for unimplemented categories
        if category == "advanced":
            help_text = "<b>Advanced Help</b>\n\nAdvanced help topics are coming soon!"
        else:
            # Get help message for the selected category
            help_text = get_help_message(category)
        
        # Create help keyboard
        keyboard = create_help_keyboard()
        
        # Update the message
        await query.message.edit_text(
            help_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    else:
        logger.warning(f"Unknown help callback: {callback_data}")
        await query.message.edit_text(
            "Sorry, I don't recognize that help category. Please try again.",
            reply_markup=create_help_keyboard()
        )
