"""
Register handlers for Jyra bot.
"""

from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from jyra.bot.handlers.command_handlers import (
    start_command, help_command, about_command, role_command,
    switch_role_command, create_role_command, remember_command,
    forget_command, settings_command
)
from jyra.bot.handlers.callback_handlers import handle_callback_query
from jyra.bot.handlers.enhanced_message_handler import handle_message
from jyra.bot.commands.memory_commands import cmd_generate_embeddings, cmd_search_memories
from jyra.bot.commands.visualization_commands import cmd_visualize_memories
from jyra.bot.commands.consolidation_commands import cmd_consolidate_memories, cmd_show_consolidation_candidates
from jyra.bot.commands.decay_commands import cmd_decay_memories, cmd_show_decay_candidates
# Web visualization commands removed
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_command_handlers(application: Application) -> None:
    """
    Register command handlers.

    Args:
        application (Application): The telegram application
    """
    # Basic commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))

    # Role commands
    application.add_handler(CommandHandler("role", role_command))
    application.add_handler(CommandHandler("switchrole", switch_role_command))
    application.add_handler(CommandHandler("createrole", create_role_command))

    # Memory commands
    application.add_handler(CommandHandler("remember", remember_command))
    application.add_handler(CommandHandler("forget", forget_command))
    application.add_handler(CommandHandler(
        "generate_embeddings", cmd_generate_embeddings))
    application.add_handler(CommandHandler(
        "search_memories", cmd_search_memories))
    application.add_handler(CommandHandler(
        "visualize_memories", cmd_visualize_memories))

    # Consolidation commands
    application.add_handler(CommandHandler(
        "consolidate_memories", cmd_consolidate_memories))
    application.add_handler(CommandHandler(
        "show_consolidation_candidates", cmd_show_consolidation_candidates))

    # Decay commands
    application.add_handler(CommandHandler(
        "decay_memories", cmd_decay_memories))
    application.add_handler(CommandHandler(
        "show_decay_candidates", cmd_show_decay_candidates))

    # Web visualization commands removed

    # Settings commands
    application.add_handler(CommandHandler("settings", settings_command))

    logger.info("Command handlers registered")


def register_callback_handlers(application: Application) -> None:
    """
    Register callback query handlers.

    Args:
        application (Application): The telegram application
    """
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    logger.info("Callback handlers registered")


def register_message_handlers(application: Application) -> None:
    """
    Register message handlers.

    Args:
        application (Application): The telegram application
    """
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Message handlers registered")
