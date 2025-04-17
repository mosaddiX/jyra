"""
Callback handlers for settings menu interactions.
"""

import json
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from jyra.db.models.user import User
from jyra.ui.keyboards import create_settings_keyboard
from jyra.ui.messages import get_settings_message
from jyra.ui.buttons import create_callback_button, create_back_button
from jyra.ui.formatting import bold, italic, code
from jyra.bot.handlers.callbacks.theme_callbacks import handle_theme_callback
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


async def show_settings_profiles(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show the settings profiles menu.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    query = update.callback_query

    # Show settings profiles menu
    await query.message.edit_text(
        f"{bold('Settings Profiles')}\n\nSettings profiles allow you to quickly switch between different configurations.\n\nYou can save your current settings as a custom profile, or load a predefined profile.",
        reply_markup=create_settings_keyboard(show_profiles=True),
        parse_mode='HTML'
    )


async def export_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Export user settings to a file.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    query = update.callback_query
    user_id = update.effective_user.id

    # Get user preferences
    preferences = await User.get_user_preferences(user_id)

    if not preferences:
        await query.message.edit_text(
            f"{bold('Export Settings')}\n\nYou don't have any custom settings to export.",
            reply_markup=create_settings_keyboard(show_profiles=True),
            parse_mode='HTML'
        )
        return

    # Format settings for export
    export_data = {
        "settings_version": "1.0",
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user_id,
        "preferences": preferences
    }

    # Convert to JSON
    export_json = json.dumps(export_data, indent=2)

    # Send as a text file
    await query.message.reply_document(
        document=export_json.encode('utf-8'),
        filename="jyra_settings_export.json",
        caption="Here are your exported settings."
    )

    await query.message.edit_text(
        f"{bold('Export Settings')}\n\nYour settings have been exported successfully!\n\nYou can import these settings later or share them with others.",
        reply_markup=create_settings_keyboard(show_profiles=True),
        parse_mode='HTML'
    )


async def import_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Import user settings from a file.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    query = update.callback_query

    await query.message.edit_text(
        f"{bold('Import Settings')}\n\nTo import settings, please send a settings file (.json) that was previously exported.\n\n{italic('Note: Importing settings will overwrite your current settings.')}",
        reply_markup=create_settings_keyboard(show_profiles=True),
        parse_mode='HTML'
    )

    # Set flag to handle file upload
    context.user_data['settings_import_mode'] = True


async def handle_settings_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str) -> None:
    """
    Handle settings profile operations.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
        callback_data (str): The callback data
    """
    query = update.callback_query
    user_id = update.effective_user.id

    # Save current settings as a profile
    if callback_data == "settings_profile_save":
        # Get current preferences
        preferences = await User.get_user_preferences(user_id)

        if not preferences:
            await query.message.edit_text(
                f"{bold('Save Settings Profile')}\n\nYou don't have any custom settings to save.",
                reply_markup=create_settings_keyboard(show_profiles=True),
                parse_mode='HTML'
            )
            return

        # Save as custom profile
        await User.update_user_preferences(user_id, {"custom_profile": preferences})

        await query.message.edit_text(
            f"{bold('Save Settings Profile')}\n\nYour current settings have been saved as a custom profile!\n\nYou can load this profile later using the 'Custom Profile' button.",
            reply_markup=create_settings_keyboard(show_profiles=True),
            parse_mode='HTML'
        )

    # Load a predefined profile
    elif callback_data.startswith("settings_profile_load_"):
        profile_name = callback_data[len("settings_profile_load_"):]

        # Define predefined profiles
        profiles = {
            "default": {
                "theme": "default",
                "language": "en",
                "length": "medium",
                "formality": "neutral"
            },
            "professional": {
                "theme": "professional",
                "language": "en",
                "length": "medium",
                "formality": "formal"
            },
            "creative": {
                "theme": "colorful",
                "language": "en",
                "length": "long",
                "formality": "casual"
            },
            "business": {
                "theme": "minimal",
                "language": "en",
                "length": "short",
                "formality": "formal"
            },
            "casual": {
                "theme": "playful",
                "language": "en",
                "length": "medium",
                "formality": "casual"
            }
        }

        # Handle custom profile
        if profile_name == "custom":
            # Get saved custom profile
            user_prefs = await User.get_user_preferences(user_id)
            custom_profile = user_prefs.get("custom_profile")

            if not custom_profile:
                await query.message.edit_text(
                    f"{bold('Load Custom Profile')}\n\nYou don't have a saved custom profile yet.\n\nUse the 'Save Current Settings' button to create one.",
                    reply_markup=create_settings_keyboard(show_profiles=True),
                    parse_mode='HTML'
                )
                return

            # Apply custom profile
            success = await User.update_user_preferences(user_id, custom_profile)
        else:
            # Apply predefined profile
            profile = profiles.get(profile_name)

            if not profile:
                await query.message.edit_text(
                    f"{bold('Load Profile')}\n\nUnknown profile: {profile_name}",
                    reply_markup=create_settings_keyboard(show_profiles=True),
                    parse_mode='HTML'
                )
                return

            # Update user preferences
            success = await User.update_user_preferences(user_id, profile)

        if success:
            await query.message.edit_text(
                f"{bold('Load Profile')}\n\nThe {profile_name.capitalize()} profile has been applied successfully!\n\nYour settings have been updated.",
                reply_markup=create_settings_keyboard(show_profiles=True),
                parse_mode='HTML'
            )
        else:
            await query.message.edit_text(
                f"{bold('Load Profile')}\n\nFailed to apply the {profile_name.capitalize()} profile. Please try again.",
                reply_markup=create_settings_keyboard(show_profiles=True),
                parse_mode='HTML'
            )
    else:
        logger.warning(f"Unknown settings profile operation: {callback_data}")
        await query.message.edit_text(
            f"{bold('Settings Profiles')}\n\nUnknown operation. Please try again.",
            reply_markup=create_settings_keyboard(show_profiles=True),
            parse_mode='HTML'
        )


async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle settings-related callback queries.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    user_id = update.effective_user.id

    # Handle theme-related callbacks
    if callback_data == "settings_theme" or callback_data.startswith("set_theme_"):
        await handle_theme_callback(update, context)
        return

    # Handle settings profiles
    if callback_data == "settings_profiles":
        await show_settings_profiles(update, context)
        return

    # Handle settings export
    elif callback_data == "settings_export":
        await export_settings(update, context)
        return

    # Handle settings import
    elif callback_data == "settings_import":
        await import_settings(update, context)
        return

    # Handle settings profile operations
    elif callback_data.startswith("settings_profile_"):
        await handle_settings_profile(update, context, callback_data)
        return

    # Extract the settings category from the callback data
    if callback_data.startswith("settings_"):
        category = callback_data[9:]  # Remove "settings_" prefix

        # Get settings message for the selected category
        settings_text = get_settings_message(category)

        if category == "profile":
            # Profile settings
            keyboard = InlineKeyboardMarkup([
                [
                    create_callback_button("🌐 Language", "settings_language")
                ],
                [
                    create_callback_button(
                        "⬅️ Back to Settings", "settings_main")
                ]
            ])

        elif category == "language":
            # Language settings
            keyboard = InlineKeyboardMarkup([
                [
                    create_callback_button("🇺🇸 English", "set_language_en"),
                    create_callback_button("🇪🇸 Spanish", "set_language_es")
                ],
                [
                    create_callback_button("🇫🇷 French", "set_language_fr"),
                    create_callback_button("🇩🇪 German", "set_language_de")
                ],
                [
                    create_callback_button(
                        "⬅️ Back to Profile", "settings_profile")
                ]
            ])

        elif category == "roles":
            # Role settings
            keyboard = InlineKeyboardMarkup([
                [
                    create_callback_button(
                        "⭐ Favorite Roles", "settings_favorite_roles")
                ],
                [
                    create_callback_button(
                        "🗑️ Delete Custom Roles", "settings_delete_roles")
                ],
                [
                    create_callback_button(
                        "⬅️ Back to Settings", "settings_main")
                ]
            ])

        elif category == "chat":
            # Chat settings
            keyboard = InlineKeyboardMarkup([
                [
                    create_callback_button(
                        "📏 Response Length", "settings_response_length")
                ],
                [
                    create_callback_button(
                        "👔 Formality Level", "settings_formality")
                ],
                [
                    create_callback_button(
                        "🎨 Theme", "settings_theme")
                ],
                [
                    create_callback_button(
                        "⬅️ Back to Settings", "settings_main")
                ]
            ])

        elif category == "response_length":
            # Response length settings
            keyboard = InlineKeyboardMarkup([
                [
                    create_callback_button("📝 Short", "set_length_short"),
                    create_callback_button("📄 Medium", "set_length_medium"),
                    create_callback_button("📜 Long", "set_length_long")
                ],
                [
                    create_callback_button(
                        "⬅️ Back to Chat Settings", "settings_chat")
                ]
            ])

        elif category == "formality":
            # Formality settings
            keyboard = InlineKeyboardMarkup([
                [
                    create_callback_button("😊 Casual", "set_formality_casual"),
                    create_callback_button(
                        "😐 Neutral", "set_formality_neutral"),
                    create_callback_button("🧐 Formal", "set_formality_formal")
                ],
                [
                    create_callback_button(
                        "⬅️ Back to Chat Settings", "settings_chat")
                ]
            ])

        elif category == "notifications":
            settings_text = "<b>🔔 Notifications Settings</b>\n\nNotification preferences are coming soon!"
            keyboard = InlineKeyboardMarkup([
                [create_callback_button(
                    "⬅️ Back to Settings", "settings_main")]
            ])

        elif category == "privacy":
            settings_text = "<b>🔒 Privacy Settings</b>\n\nPrivacy controls are coming soon!"
            keyboard = InlineKeyboardMarkup([
                [create_callback_button(
                    "⬅️ Back to Settings", "settings_main")]
            ])

        elif category == "advanced":
            settings_text = "<b>⚙️ Advanced Settings</b>\n\nAdvanced options are coming soon!"
            keyboard = InlineKeyboardMarkup([
                [create_callback_button(
                    "⬅️ Back to Settings", "settings_main")]
            ])

        elif category == "main":
            # Main settings menu
            keyboard = create_settings_keyboard()

        else:
            # Unknown category, show main settings
            settings_text = get_settings_message("main")
            keyboard = create_settings_keyboard()

        # Update the message
        await query.message.edit_text(
            settings_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    # Handle setting changes
    elif callback_data.startswith("set_"):
        parts = callback_data.split("_")
        if len(parts) >= 3:
            setting_type = parts[1]
            setting_value = parts[2]

            # Update user preference
            success = await User.update_user_preferences(user_id, {setting_type: setting_value})

            if success:
                # Show confirmation and return to appropriate settings menu
                if setting_type == "language":
                    await query.message.edit_text(
                        f"Language updated to {setting_value.upper()}!",
                        reply_markup=InlineKeyboardMarkup([[
                            create_callback_button(
                                "⬅️ Back to Language Settings", "settings_language")
                        ]])
                    )

                elif setting_type == "length":
                    await query.message.edit_text(
                        f"Response length updated to {setting_value}!",
                        reply_markup=InlineKeyboardMarkup([[
                            create_callback_button(
                                "⬅️ Back to Response Length Settings", "settings_response_length")
                        ]])
                    )

                elif setting_type == "formality":
                    await query.message.edit_text(
                        f"Formality level updated to {setting_value}!",
                        reply_markup=InlineKeyboardMarkup([[
                            create_callback_button(
                                "⬅️ Back to Formality Settings", "settings_formality")
                        ]])
                    )
            else:
                # Show error
                await query.message.edit_text(
                    "Sorry, I couldn't update your settings. Please try again.",
                    reply_markup=create_back_button("settings_main")
                )

    else:
        logger.warning(f"Unknown settings callback: {callback_data}")
        await query.message.edit_text(
            "Sorry, I don't recognize that settings option. Please try again.",
            reply_markup=create_settings_keyboard()
        )
