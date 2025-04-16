"""
Callback query handlers for Jyra Telegram bot
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from jyra.db.models.user import User
from jyra.db.models.role import Role
from jyra.db.models.memory import Memory
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback queries from inline keyboards.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    query = update.callback_query
    user_id = query.from_user.id

    # Answer the callback query to stop the loading animation
    await query.answer()

    callback_data = query.data

    # Handle role selection
    if callback_data.startswith("role_"):
        role_id = int(callback_data.split("_")[1])
        await handle_role_selection(update, context, role_id)

    # Handle create role button
    elif callback_data == "create_role":
        await handle_create_role_button(update, context)

    # Handle cancel role creation
    elif callback_data == "cancel_role_creation":
        await handle_cancel_role_creation(update, context)

    # Handle forget memory
    elif callback_data.startswith("forget_"):
        memory_id = int(callback_data.split("_")[1])
        await handle_forget_memory(update, context, memory_id)

    # Handle settings
    elif callback_data.startswith("settings_"):
        setting = callback_data.split("_")[1]
        await handle_settings_selection(update, context, setting)


async def handle_role_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, role_id: int) -> None:
    """
    Handle role selection from inline keyboard.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
        role_id (int): The selected role ID
    """
    query = update.callback_query
    user_id = query.from_user.id

    # Get the role
    role = await Role.get_role(role_id)
    if not role:
        await query.edit_message_text(
            "Sorry, I couldn't find that persona. Please try again."
        )
        return

    # Update user's current role
    db_user = await User.get_user(user_id)
    if not db_user:
        db_user = User(
            user_id=user_id,
            username=query.from_user.username,
            first_name=query.from_user.first_name,
            last_name=query.from_user.last_name,
            language_code=query.from_user.language_code
        )
        await db_user.save()

    await db_user.set_current_role(role_id)

    # Confirm selection
    await query.edit_message_text(
        f"Great! I'll now be your {role.name}.\n\n"
        f"{role.description}\n\n"
        f"You can start chatting with me now, or use /switchrole to choose a different persona."
    )


async def handle_create_role_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle create role button from inline keyboard.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    query = update.callback_query

    # Store the state in user_data
    context.user_data["creating_role"] = True
    context.user_data["role_creation_step"] = "name"
    context.user_data["new_role"] = {}

    # Create cancel button
    keyboard = [[InlineKeyboardButton(
        "❌ Cancel", callback_data="cancel_role_creation")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "Let's create a custom roleplay persona!\n\n"
        "First, what should I call this persona? Please enter a name.\n\n"
        "You can cancel this process at any time by clicking the button below.",
        reply_markup=reply_markup
    )


async def handle_cancel_role_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle cancellation of role creation process.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    query = update.callback_query

    # Clear role creation state
    context.user_data["creating_role"] = False
    context.user_data["role_creation_step"] = None
    context.user_data["new_role"] = {}

    await query.edit_message_text(
        "Role creation cancelled. You can use /role to select an existing persona or /createrole to try again."
    )


async def handle_forget_memory(update: Update, context: ContextTypes.DEFAULT_TYPE, memory_id: int) -> None:
    """
    Handle forget memory selection from inline keyboard.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
        memory_id (int): The memory ID to forget
    """
    query = update.callback_query
    user_id = query.from_user.id

    # Delete the memory
    success = await Memory.delete_memory(memory_id, user_id)

    if success:
        await query.edit_message_text(
            "I've forgotten that memory as requested."
        )
    else:
        await query.edit_message_text(
            "I had trouble forgetting that memory. Please try again later."
        )


async def handle_settings_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, setting: str) -> None:
    """
    Handle settings selection from inline keyboard.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
        setting (str): The selected setting
    """
    query = update.callback_query
    user_id = query.from_user.id

    if setting == "language":
        # Show language options
        keyboard = [
            [
                InlineKeyboardButton(
                    "English (en)", callback_data="set_language_en"),
                InlineKeyboardButton(
                    "Español (es)", callback_data="set_language_es")
            ],
            [
                InlineKeyboardButton(
                    "Français (fr)", callback_data="set_language_fr"),
                InlineKeyboardButton(
                    "Deutsch (de)", callback_data="set_language_de")
            ],
            [
                InlineKeyboardButton(
                    "Italiano (it)", callback_data="set_language_it"),
                InlineKeyboardButton(
                    "Português (pt)", callback_data="set_language_pt")
            ],
            [
                InlineKeyboardButton(
                    "Русский (ru)", callback_data="set_language_ru"),
                InlineKeyboardButton(
                    "日本語 (ja)", callback_data="set_language_ja")
            ],
            [
                InlineKeyboardButton(
                    "中文 (zh)", callback_data="set_language_zh"),
                InlineKeyboardButton(
                    "العربية (ar)", callback_data="set_language_ar")
            ],
            [InlineKeyboardButton("« Back to Settings",
                                  callback_data="settings_back")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "Please select your preferred language:",
            reply_markup=reply_markup
        )

    elif setting == "length":
        # Show response length options
        keyboard = [
            [InlineKeyboardButton("Short", callback_data="set_length_short")],
            [InlineKeyboardButton(
                "Medium", callback_data="set_length_medium")],
            [InlineKeyboardButton("Long", callback_data="set_length_long")],
            [InlineKeyboardButton("« Back to Settings",
                                  callback_data="settings_back")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "Please select your preferred response length:",
            reply_markup=reply_markup
        )

    elif setting == "formality":
        # Show formality options
        keyboard = [
            [InlineKeyboardButton(
                "Casual", callback_data="set_formality_casual")],
            [InlineKeyboardButton(
                "Neutral", callback_data="set_formality_neutral")],
            [InlineKeyboardButton(
                "Formal", callback_data="set_formality_formal")],
            [InlineKeyboardButton("« Back to Settings",
                                  callback_data="settings_back")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "Please select your preferred formality level:",
            reply_markup=reply_markup
        )

    elif setting == "memory":
        # Toggle memory setting
        preferences = await User.get_user_preferences(user_id)
        new_memory_setting = not preferences["memory_enabled"]

        await User.update_user_preferences(user_id, {"memory_enabled": new_memory_setting})

        # Update settings menu
        await show_settings_menu(update, context)

    elif setting == "voice":
        # Inform the user that voice responses are temporarily disabled
        await query.edit_message_text(
            "Voice responses are temporarily disabled due to technical limitations. \n\n"
            "We're working on improving this feature to provide full-length voice responses in the future. "
            "For now, you can still send voice messages and I'll transcribe them!\n\n"
            "Press /settings to return to the settings menu."
        )

    elif setting == "back":
        # Show settings menu
        await show_settings_menu(update, context)

    # Handle direct setting changes
    elif setting.startswith("set_"):
        parts = setting.split("_")
        if len(parts) == 3:
            setting_type = parts[1]
            setting_value = parts[2]

            if setting_type == "language":
                await User.update_user_preferences(user_id, {"language": setting_value})
            elif setting_type == "length":
                await User.update_user_preferences(user_id, {"response_length": setting_value})
            elif setting_type == "formality":
                await User.update_user_preferences(user_id, {"formality_level": setting_value})

            # Show updated settings menu
            await show_settings_menu(update, context)


async def show_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show the settings menu.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    query = update.callback_query
    user_id = query.from_user.id

    # Get current preferences
    preferences = await User.get_user_preferences(user_id)

    # Create inline keyboard with settings
    keyboard = [
        [InlineKeyboardButton(
            f"Language: {preferences['language']}",
            callback_data="settings_language"
        )],
        [InlineKeyboardButton(
            f"Response Length: {preferences['response_length']}",
            callback_data="settings_length"
        )],
        [InlineKeyboardButton(
            f"Formality: {preferences['formality_level']}",
            callback_data="settings_formality"
        )],
        [InlineKeyboardButton(
            f"Memory: {'Enabled' if preferences['memory_enabled'] else 'Disabled'}",
            callback_data="settings_memory"
        )],
        [InlineKeyboardButton(
            f"Voice Responses: Temporarily Unavailable",
            callback_data="settings_voice"
        )]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "Here are your current settings. Click on a setting to change it:",
        reply_markup=reply_markup
    )
