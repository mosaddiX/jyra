"""
Updated handlers for Jyra bot.

This module provides updated handlers that use the new UI components.
"""

# Import the new command handlers
from jyra.bot.handlers.commands import (
    start_command, help_command, about_command,
    role_command, switch_role_command, settings_command,
    create_role_command, remember_command, forget_command, mood_command
)

# Import the new callback handlers
from jyra.bot.handlers.callbacks import handle_callback_query

# Import the enhanced message handler
from jyra.bot.handlers.enhanced_message_handler import handle_message

# Re-export the handlers
__all__ = [
    'start_command',
    'help_command',
    'about_command',
    'role_command',
    'switch_role_command',
    'settings_command',
    'create_role_command',
    'remember_command',
    'forget_command',
    'mood_command',
    'handle_callback_query',
    'handle_message'
]
