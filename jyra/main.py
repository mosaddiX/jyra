"""
Main entry point for Jyra bot.
"""

import logging
from telegram.ext import Application

from jyra.utils.config import TELEGRAM_BOT_TOKEN, validate_config
from jyra.db.init_db import init_db
from jyra.bot.handlers.register_handlers import register_command_handlers, register_callback_handlers, register_message_handlers
from jyra.bot.handlers.error_handlers import error_handler
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """
    Main function to start the bot.
    """
    # Validate configuration
    config_errors = validate_config()
    if config_errors:
        for error in config_errors:
            logger.error(f"Configuration error: {error}")
        logger.error("Exiting due to configuration errors")
        return

    # Initialize database
    init_db()

    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    register_command_handlers(application)
    register_callback_handlers(application)
    register_message_handlers(application)

    # Register error handler
    application.add_error_handler(error_handler)

    # We'll skip the memory maintenance scheduler for now to avoid event loop issues
    # start_memory_maintenance_scheduler()

    # Start the bot
    logger.info("Starting bot")
    application.run_polling()


if __name__ == "__main__":
    main()
