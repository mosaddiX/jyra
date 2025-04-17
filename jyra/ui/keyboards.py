"""
Keyboard factory functions for Jyra bot.

This module provides functions for creating consistent keyboard layouts
throughout the bot interface.
"""

from typing import List, Dict, Any, Optional
from telegram import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from jyra.ui.buttons import (
    create_callback_button, create_button_row, create_button_grid,
    create_main_menu_keyboard, create_role_selection_keyboard,
    create_settings_keyboard, create_memory_keyboard,
    create_help_keyboard, create_back_button
)

# Re-export button functions for convenience
__all__ = [
    'create_main_menu_keyboard', 'create_role_selection_keyboard',
    'create_settings_keyboard', 'create_memory_keyboard',
    'create_help_keyboard', 'create_back_button',
    'create_reply_keyboard', 'create_conversation_controls'
]


def create_reply_keyboard(buttons: List[str],
                          columns: int = 2,
                          resize_keyboard: bool = True,
                          one_time_keyboard: bool = False) -> ReplyKeyboardMarkup:
    """
    Create a reply keyboard with the given buttons.

    Args:
        buttons: List of button texts
        columns: Number of columns in the keyboard
        resize_keyboard: Whether to resize the keyboard
        one_time_keyboard: Whether the keyboard should disappear after one use

    Returns:
        A ReplyKeyboardMarkup instance
    """
    keyboard_buttons = [KeyboardButton(text=text) for text in buttons]
    keyboard = [keyboard_buttons[i:i+columns]
                for i in range(0, len(keyboard_buttons), columns)]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=resize_keyboard,
        one_time_keyboard=one_time_keyboard
    )


def create_conversation_controls(compact: bool = False) -> InlineKeyboardMarkup:
    """
    Create conversation control buttons.

    Args:
        compact: Whether to use a compact layout with fewer buttons

    Returns:
        An InlineKeyboardMarkup with conversation control buttons
    """
    if compact:
        # Compact layout with just the most essential controls
        keyboard = [
            [
                create_callback_button(
                    "🔄 Regenerate", "conversation_regenerate"),
                create_callback_button("🔍 Explain", "conversation_explain"),
                create_callback_button("🎭 Role", "conversation_switch_role")
            ]
        ]
    else:
        # Full layout with all controls
        keyboard = [
            [
                create_callback_button(
                    "🔄 Regenerate", "conversation_regenerate"),
                create_callback_button("📌 Save", "conversation_save"),
                create_callback_button("🔍 Explain", "conversation_explain")
            ],
            [
                create_callback_button(
                    "🎭 Switch Role", "conversation_switch_role"),
                create_callback_button("📝 Remember", "conversation_remember"),
                create_callback_button(
                    "⏹️ End Topic", "conversation_end_topic")
            ],
            [
                create_callback_button("📂 History", "conversation_history_0"),
                create_callback_button("💬 Continue", "conversation_continue")
            ]
        ]
    return InlineKeyboardMarkup(keyboard)
