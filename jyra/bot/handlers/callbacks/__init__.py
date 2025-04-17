"""
Callback handlers for Jyra bot.
"""

from jyra.bot.handlers.callbacks.menu_callbacks import handle_menu_callback
from jyra.bot.handlers.callbacks.help_callbacks import handle_help_callback
from jyra.bot.handlers.callbacks.role_callbacks import handle_role_callback
from jyra.bot.handlers.callbacks.settings_callbacks import handle_settings_callback
from jyra.bot.handlers.callbacks.theme_callbacks import handle_theme_callback
from jyra.bot.handlers.callbacks.conversation_callbacks import handle_conversation_callback
from jyra.bot.handlers.callbacks.memory_callbacks import handle_memory_callback

__all__ = [
    'handle_menu_callback',
    'handle_help_callback',
    'handle_role_callback',
    'handle_settings_callback',
    'handle_theme_callback',
    'handle_memory_callback',
    'handle_callback_query',
    'handle_conversation_callback'
]


async def handle_callback_query(update, context):
    """
    Route callback queries to the appropriate handler.

    Args:
        update: The update object
        context: The context object
    """
    query = update.callback_query
    callback_data = query.data

    # Route to the appropriate handler based on the callback data
    if callback_data.startswith("menu_"):
        await handle_menu_callback(update, context)
    elif callback_data.startswith("help_"):
        await handle_help_callback(update, context)
    elif callback_data.startswith("role_") or callback_data == "create_role":
        await handle_role_callback(update, context)
    elif callback_data.startswith("settings_") or callback_data.startswith("set_"):
        # Theme callbacks are handled within settings_callbacks
        await handle_settings_callback(update, context)
    elif callback_data.startswith("memory_"):
        await handle_memory_callback(update, context)
    elif callback_data.startswith("conversation_") or callback_data.startswith("save_memory_") or callback_data == "cancel_memory":
        # Handle conversation controls and memory extraction
        await handle_conversation_callback(update, context)
    else:
        # Handle other callback types or unknown callbacks
        await query.answer("Unknown callback")
        await query.message.edit_text(
            "Sorry, I don't recognize that option. Please try again.",
            reply_markup=None
        )


async def handle_conversation_callback(update, context):
    """
    Handle conversation-related callbacks.

    Args:
        update: The update object
        context: The context object
    """
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    if callback_data == "conversation_regenerate":
        await query.message.reply_text(
            "🔄 <b>Regenerate</b>\n\nThis feature is coming soon!",
            parse_mode='HTML'
        )
    elif callback_data == "conversation_save":
        await query.message.reply_text(
            "💾 <b>Save Conversation</b>\n\nThis feature is coming soon!",
            parse_mode='HTML'
        )
    elif callback_data == "conversation_explain":
        await query.message.reply_text(
            "💡 <b>Explain Response</b>\n\nThis feature is coming soon!",
            parse_mode='HTML'
        )
    elif callback_data == "conversation_switch_role":
        # Redirect to role selection
        await handle_role_callback(update, context)
    elif callback_data == "conversation_remember":
        await query.message.reply_text(
            "📝 <b>Remember</b>\n\nWhat would you like me to remember?",
            parse_mode='HTML'
        )
    elif callback_data == "conversation_end_topic":
        await query.message.reply_text(
            "🔚 <b>End Topic</b>\n\nTopic ended. What would you like to talk about next?",
            parse_mode='HTML'
        )
    else:
        await query.message.reply_text(
            "❓ <b>Unknown conversation action.</b>\n\nPlease use the menu buttons to continue.",
            parse_mode='HTML'
        )
