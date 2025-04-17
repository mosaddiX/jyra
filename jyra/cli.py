#!/usr/bin/env python
"""
Jyra CLI - Command Line Interface for Jyra AI Companion

This module provides a command-line interface for running and managing the Jyra AI Companion.
"""

import argparse
import asyncio
import sys
import os
from pathlib import Path
import nest_asyncio
from dotenv import load_dotenv

from jyra.utils.config import validate_config
from jyra.utils.logger import setup_logger
from jyra.db.models.role import Role
from jyra.db.init_db import init_db
from jyra.bot.handlers.register_handlers import (
    register_command_handlers,
    register_callback_handlers,
    register_message_handlers
)
from jyra.bot.handlers.error_handlers import error_handler
from telegram.ext import Application

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Create necessary directories
Path("logs").mkdir(exist_ok=True)
Path("data").mkdir(exist_ok=True)
Path("data/cache").mkdir(exist_ok=True)
Path("data/visualizations").mkdir(exist_ok=True)
Path("data/web").mkdir(exist_ok=True)

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


async def run_maintenance():
    """Run maintenance tasks."""
    from jyra.ai.memory_manager import memory_manager
    
    print(f"{COLORS['YELLOW']}Running memory maintenance...{COLORS['ENDC']}")
    
    # Get all users
    from jyra.db.models.user import User
    users = await User.get_all_users()
    
    for user in users:
        print(f"{COLORS['YELLOW']}  → Running maintenance for user {user.user_id}...{COLORS['ENDC']}")
        results = await memory_manager.run_memory_maintenance(user.user_id)
        print(f"{COLORS['GREEN']}  ✓ Maintenance complete for user {user.user_id}: {results}{COLORS['ENDC']}")
    
    print(f"{COLORS['GREEN']}All maintenance tasks completed!{COLORS['ENDC']}")


async def run_bot():
    """Run the Jyra bot."""
    from jyra.utils.config import TELEGRAM_BOT_TOKEN
    
    # Display ASCII art
    print(f"{COLORS['BLUE']}{ASCII_ART}{COLORS['ENDC']}")
    print(f"{COLORS['BOLD']}Jyra AI Companion v1.0.0{COLORS['ENDC']}")
    print(f"{COLORS['GREEN']}Created by MosaddiX{COLORS['ENDC']}")
    print("\nInitializing...\n")

    # Validate configuration
    config_errors = validate_config()
    if config_errors:
        for error in config_errors:
            logger.error(f"{COLORS['RED']}Configuration error: {error}{COLORS['ENDC']}")
        logger.error(f"{COLORS['RED']}Please fix the configuration errors and restart the bot.{COLORS['ENDC']}")
        return

    # Setup database
    print(f"{COLORS['YELLOW']}Setting up database...{COLORS['ENDC']}")
    await setup_database()

    # Create the Application
    print(f"{COLORS['YELLOW']}Initializing Telegram bot...{COLORS['ENDC']}")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    print(f"{COLORS['YELLOW']}  → Registering handlers...{COLORS['ENDC']}")
    register_command_handlers(application)
    register_callback_handlers(application)
    register_message_handlers(application)

    # Register error handler
    print(f"{COLORS['YELLOW']}  → Setting up error handling...{COLORS['ENDC']}")
    application.add_error_handler(error_handler)

    # Start the Bot
    print(f"{COLORS['GREEN']}All systems initialized successfully!{COLORS['ENDC']}")
    print(f"{COLORS['BOLD']}Starting Jyra bot...{COLORS['ENDC']}")
    print(f"{COLORS['BLUE']}Bot is now online and ready to chat!{COLORS['ENDC']}")
    print(f"{COLORS['YELLOW']}Press Ctrl+C to stop the bot{COLORS['ENDC']}\n")
    logger.info("Starting Jyra bot...")
    application.run_polling()


async def run_db_init():
    """Initialize the database."""
    print(f"{COLORS['YELLOW']}Initializing database...{COLORS['ENDC']}")
    await setup_database()
    print(f"{COLORS['GREEN']}Database initialization complete!{COLORS['ENDC']}")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Jyra AI Companion CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Bot command
    bot_parser = subparsers.add_parser("bot", help="Run the Jyra bot")
    
    # Maintenance command
    maintenance_parser = subparsers.add_parser("maintenance", help="Run maintenance tasks")
    
    # Database initialization command
    db_init_parser = subparsers.add_parser("db-init", help="Initialize the database")
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")

    args = parser.parse_args()

    if args.command == "bot":
        asyncio.run(run_bot())
    elif args.command == "maintenance":
        asyncio.run(run_maintenance())
    elif args.command == "db-init":
        asyncio.run(run_db_init())
    elif args.command == "version":
        print(f"{COLORS['BLUE']}{ASCII_ART}{COLORS['ENDC']}")
        print(f"{COLORS['BOLD']}Jyra AI Companion v1.0.0{COLORS['ENDC']}")
        print(f"{COLORS['GREEN']}Created by MosaddiX{COLORS['ENDC']}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
