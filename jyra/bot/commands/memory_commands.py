"""
Memory-related commands for Jyra bot.
"""

from jyra.bot.commands.improved_search import improved_search_memories
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from jyra.db.models.memory_semantic import generate_embeddings_for_all_memories
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


async def cmd_generate_embeddings(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Generate embeddings for all memories.

    Usage: /generate_embeddings
    """
    # Send a message to indicate the process has started
    message = await update.message.reply_text("Generating embeddings for all memories... This may take a while.")

    try:
        # Generate embeddings for all memories
        await generate_embeddings_for_all_memories()

        # Update the message to indicate completion
        await message.edit_text("✅ Embeddings generated successfully for all memories!")

    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        await message.edit_text(f"❌ Error generating embeddings: {str(e)}")


async def cmd_search_memories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Search memories using both semantic and keyword search with enhanced options.

    This function delegates to the improved_search_memories implementation.
    """
    await improved_search_memories(update, context)


# Note: Advanced search functionality has been combined into the improved search_memories command
# Use /search_memories with the -b option to use both semantic and keyword search


def register_memory_commands(application) -> None:
    """
    Register memory-related commands.

    Args:
        application: The telegram application
    """
    application.add_handler(CommandHandler(
        "generate_embeddings", cmd_generate_embeddings))
    application.add_handler(CommandHandler(
        "search_memories", cmd_search_memories))
