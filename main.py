#!/usr/bin/env python
"""
Jyra - The Soul That Remembers You
Main entry point for the Jyra Telegram bot
"""

from jyra.utils.config import TELEGRAM_BOT_TOKEN, validate_config
from jyra.utils.logger import setup_logger
from jyra.db.models.role import Role
from jyra.db.init_db import init_db
from jyra.bot.handlers.error_handlers import error_handler
from jyra.bot.handlers.callback_handlers import handle_callback_query
from jyra.bot.handlers.message_handlers_sentiment import handle_message
from jyra.bot.handlers.multimodal_handlers import handle_photo, handle_voice, toggle_voice_responses
from jyra.bot.handlers.command_handlers_sentiment import (
    start_command, help_command_with_mood as help_command, about_command, role_command,
    switch_role_command, create_role_command, remember_command,
    forget_command, settings_command, mood_command
)
from jyra.bot.handlers.simple_community_handlers import register_community_handlers
from jyra.bot.middleware.rate_limit_middleware import rate_limit_middleware
import asyncio
import nest_asyncio
from pathlib import Path
from dotenv import load_dotenv

from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters
)

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()


# Create necessary directories
Path("logs").mkdir(exist_ok=True)
Path("data").mkdir(exist_ok=True)

# Load environment variables
load_dotenv()

# Get logger
logger = setup_logger(__name__)

# ASCII Art for terminal startup
ASCII_ART = """
     ██╗██╗   ██╗██████╗  █████╗
     ██║╚██╗ ██╔╝██╔══██╗██╔══██╗
     ██║ ╚████╔╝ ██████╔╝███████║
██   ██║  ╚██╔╝  ██╔══██╗██╔══██║
╚█████╔╝   ██║   ██║  ██║██║  ██║
 ╚════╝    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝

  The soul that remembers you
"""

# Terminal colors
COLORS = {
    "BLUE": "\033[94m",
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "RED": "\033[91m",
    "ENDC": "\033[0m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m"
}


async def setup_database():
    """Initialize the database and default roles."""
    # Initialize database
    print(f"{COLORS['YELLOW']}  → Creating database schema...{COLORS['ENDC']}")
    init_db()

    # Initialize default roles
    print(f"{COLORS['YELLOW']}  → Setting up default roles...{COLORS['ENDC']}")
    await Role.initialize_default_roles()

    print(f"{COLORS['GREEN']}  ✓ Database setup complete!{COLORS['ENDC']}")
    logger.info("Database setup complete")


def main() -> None:
    """Start the bot."""
    # Display ASCII art
    print(f"{COLORS['BLUE']}{ASCII_ART}{COLORS['ENDC']}")
    print(f"{COLORS['BOLD']}Jyra AI Companion v1.0.0{COLORS['ENDC']}")
    print(f"{COLORS['GREEN']}Created by MosaddiX{COLORS['ENDC']}")
    print("\nInitializing...\n")

    # Validate configuration
    config_errors = validate_config()
    if config_errors:
        for error in config_errors:
            logger.error(
                f"{COLORS['RED']}Configuration error: {error}{COLORS['ENDC']}")
        logger.error(
            f"{COLORS['RED']}Please fix the configuration errors and restart the bot.{COLORS['ENDC']}")
        return

    # Setup database
    print(f"{COLORS['YELLOW']}Setting up database...{COLORS['ENDC']}")
    # Run the async setup_database function in a new event loop
    asyncio.run(setup_database())

    # Create the Application
    print(f"{COLORS['YELLOW']}Initializing Telegram bot...{COLORS['ENDC']}")
    # Create application with default settings
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handlers with rate limiting
    print(
        f"{COLORS['YELLOW']}  → Registering command handlers...{COLORS['ENDC']}")
    application.add_handler(CommandHandler(
        "start", rate_limit_middleware(start_command)))
    application.add_handler(CommandHandler(
        "help", rate_limit_middleware(help_command)))
    application.add_handler(CommandHandler(
        "about", rate_limit_middleware(about_command)))
    application.add_handler(CommandHandler(
        "role", rate_limit_middleware(role_command)))
    application.add_handler(CommandHandler(
        "switchrole", rate_limit_middleware(switch_role_command)))
    application.add_handler(CommandHandler(
        "createrole", rate_limit_middleware(create_role_command)))
    application.add_handler(CommandHandler(
        "remember", rate_limit_middleware(remember_command)))
    application.add_handler(CommandHandler(
        "forget", rate_limit_middleware(forget_command)))
    application.add_handler(CommandHandler(
        "settings", rate_limit_middleware(settings_command)))
    application.add_handler(CommandHandler(
        "mood", rate_limit_middleware(mood_command)))

    # Add callback query handler
    print(
        f"{COLORS['YELLOW']}  → Setting up interactive components...{COLORS['ENDC']}")
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # Add message handlers with rate limiting
    print(
        f"{COLORS['YELLOW']}  → Configuring message processing...{COLORS['ENDC']}")
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, rate_limit_middleware(handle_message)))
    application.add_handler(MessageHandler(
        filters.PHOTO, rate_limit_middleware(handle_photo)))
    application.add_handler(MessageHandler(
        filters.VOICE, rate_limit_middleware(handle_voice)))

    # Add voice toggle command with rate limiting
    application.add_handler(CommandHandler(
        "voice", rate_limit_middleware(toggle_voice_responses)))

    # Register community engagement handlers
    print(
        f"{COLORS['YELLOW']}  → Setting up community engagement features...{COLORS['ENDC']}")
    register_community_handlers(application)

    # Add error handler
    print(f"{COLORS['YELLOW']}  → Setting up error handling...{COLORS['ENDC']}")
    application.add_error_handler(error_handler)

    # Start the Bot
    print(
        f"{COLORS['GREEN']}All systems initialized successfully!{COLORS['ENDC']}")
    print(f"{COLORS['BOLD']}Starting Jyra bot...{COLORS['ENDC']}")
    print(
        f"{COLORS['BLUE']}Bot is now online and ready to chat!{COLORS['ENDC']}")
    print(f"{COLORS['YELLOW']}Press Ctrl+C to stop the bot{COLORS['ENDC']}\n")
    logger.info("Starting Jyra bot...")
    application.run_polling()


if __name__ == '__main__':
    main()
