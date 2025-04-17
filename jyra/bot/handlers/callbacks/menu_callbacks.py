"""
Callback handlers for menu interactions.
"""

from telegram import Update
from telegram.ext import ContextTypes

from jyra.ui.keyboards import (
    create_main_menu_keyboard, create_role_selection_keyboard,
    create_settings_keyboard, create_memory_keyboard,
    create_help_keyboard
)
from jyra.ui.messages import (
    get_help_message, get_settings_message
)
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)

async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle menu-related callback queries.
    
    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    if callback_data == "menu_main":
        # Main menu
        keyboard = create_main_menu_keyboard()
        await query.message.edit_text(
            "What would you like to do?",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    elif callback_data == "menu_roles":
        # Roles menu - delegate to role callback handler
        from jyra.bot.handlers.callbacks.role_callbacks import handle_roles_menu
        await handle_roles_menu(update, context)
    
    elif callback_data == "menu_memory":
        # Memory menu
        keyboard = create_memory_keyboard()
        await query.message.edit_text(
            "Memory Management",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    elif callback_data == "menu_settings":
        # Settings menu
        settings_text = get_settings_message("main")
        keyboard = create_settings_keyboard()
        await query.message.edit_text(
            settings_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    elif callback_data == "menu_help":
        # Help menu
        help_text = get_help_message("main")
        keyboard = create_help_keyboard()
        await query.message.edit_text(
            help_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    else:
        logger.warning(f"Unknown menu callback: {callback_data}")
        await query.message.edit_text(
            "Sorry, I don't recognize that option. Please try again.",
            reply_markup=create_main_menu_keyboard()
        )
