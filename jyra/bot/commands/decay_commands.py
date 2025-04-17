"""
Decay-related commands for Jyra bot.
"""

import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

from jyra.utils.config import DATABASE_PATH

from jyra.ai.decay.memory_decay import memory_decay
from jyra.db.models.memory import Memory
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


async def cmd_decay_memories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Apply decay to old, less important memories.

    Usage: /decay_memories [decay_factor] [min_age_days]

    Examples:
    /decay_memories - Apply decay with default settings
    /decay_memories 0.8 - Apply stronger decay (lower importance)
    /decay_memories 0.8 60 - Apply stronger decay to memories older than 60 days
    """
    user_id = update.effective_user.id

    # Parse arguments
    decay_factor = 0.9  # Default
    min_age_days = 30  # Default

    if context.args:
        try:
            decay_factor = float(context.args[0])
            if decay_factor < 0.5:
                decay_factor = 0.5
            elif decay_factor > 0.95:
                decay_factor = 0.95

            if len(context.args) > 1:
                min_age_days = int(context.args[1])
                if min_age_days < 7:
                    min_age_days = 7
        except ValueError:
            await update.message.reply_text(
                "Invalid arguments. Usage: /decay_memories [decay_factor] [min_age_days]")
            return

    # Send a message to indicate the process has started
    message = await update.message.reply_text(
        "Analyzing your memories for decay... This may take a moment.")

    try:
        # Apply decay to memories
        result = await memory_decay.apply_decay_to_user_memories(
            user_id=user_id,
            decay_factor=decay_factor,
            min_age_days=min_age_days
        )

        if result["success"]:
            if result["decayed_count"] > 0:
                # Create a message with the results
                response = f"✅ Successfully decayed {result['decayed_count']} memories.\n\n"

                # Add information about the decayed memories
                if "decayed_memory_ids" in result and result["decayed_memory_ids"]:
                    response += "Decayed memories:\n"
                    for i, memory_id in enumerate(result["decayed_memory_ids"][:5], 1):
                        memory = await Memory.get_memory_by_id(user_id, memory_id)
                        if memory:
                            content = memory.content[:50] + "..." if len(
                                memory.content) > 50 else memory.content
                            response += f"{i}. {content} (now importance: {memory.importance})\n"

                    if len(result["decayed_memory_ids"]) > 5:
                        response += f"...and {len(result['decayed_memory_ids']) - 5} more.\n"

                # Add a button to view decayed memories
                keyboard = [[
                    InlineKeyboardButton(
                        "View Decayed Memories",
                        callback_data=f"view_decayed_{user_id}"
                    )
                ]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await message.edit_text(response, reply_markup=reply_markup)
            else:
                await message.edit_text(
                    "No memories were decayed. Your memories may be too recent, "
                    "or already at minimum importance level.")
        else:
            await message.edit_text(f"❌ Error during decay: {result['message']}")

    except Exception as e:
        logger.error(f"Error decaying memories: {str(e)}")
        await message.edit_text(f"❌ Error decaying memories: {str(e)}")


async def cmd_show_decay_candidates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show memories that are candidates for decay.

    Usage: /show_decay_candidates [min_age_days]

    Examples:
    /show_decay_candidates - Show candidates with default age threshold
    /show_decay_candidates 60 - Show candidates older than 60 days
    """
    user_id = update.effective_user.id

    # Parse arguments
    min_age_days = 30  # Default

    if context.args:
        try:
            min_age_days = int(context.args[0])
            if min_age_days < 7:
                min_age_days = 7
        except ValueError:
            await update.message.reply_text(
                "Invalid argument. Usage: /show_decay_candidates [min_age_days]")
            return

    # Send a message to indicate the process has started
    message = await update.message.reply_text(
        "Analyzing your memories for potential decay... This may take a moment.")

    try:
        # Get decay candidates
        candidates = await memory_decay._get_decay_candidates(
            user_id=user_id,
            min_age_days=min_age_days,
            limit=10
        )

        if not candidates:
            await message.edit_text(
                "No decay candidates found. Your memories may be too recent, "
                "or already at minimum importance level.")
            return

        # Create a message with the candidates
        response = f"Found {len(candidates)} memories that are candidates for decay:\n\n"

        for i, memory in enumerate(candidates, 1):
            content = memory.content[:50] + \
                "..." if len(memory.content) > 50 else memory.content
            created_date = memory.created_at.split(
                ' ')[0] if memory.created_at else "Unknown"
            last_accessed = memory.last_accessed.split(
                ' ')[0] if memory.last_accessed else "Never"

            response += f"{i}. {content}\n"
            response += f"   Importance: {memory.importance}, Created: {created_date}, Last accessed: {last_accessed}\n\n"

        response += "Use /decay_memories to apply decay to these memories."

        await message.edit_text(response)

    except Exception as e:
        logger.error(f"Error showing decay candidates: {str(e)}")
        await message.edit_text(f"❌ Error showing decay candidates: {str(e)}")


async def handle_decay_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback queries for decay options.
    """
    query = update.callback_query
    await query.answer()

    # Get the callback data
    data = query.data

    # Handle view decayed memories
    if data.startswith("view_decayed_"):
        user_id = int(data.split("_")[-1])

        # Check if the user is authorized
        if user_id != update.effective_user.id:
            await query.edit_message_text(
                "You are not authorized to view these memories.")
            return

        # Get recently decayed memories (those with context containing "decayed")
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """SELECT memory_id FROM memories
               WHERE user_id = ? AND context LIKE '%decayed%'
               ORDER BY last_accessed DESC LIMIT 10""",
            (user_id,)
        )

        memory_ids = [row[0] for row in cursor.fetchall()]
        conn.close()

        if not memory_ids:
            await query.edit_message_text(
                "No recently decayed memories found.")
            return

        # Get the memory objects
        memories = []
        for memory_id in memory_ids:
            memory = await Memory.get_memory_by_id(user_id, memory_id)
            if memory:
                memories.append(memory)

        if not memories:
            await query.edit_message_text(
                "No decayed memories found.")
            return

        # Create a message with the decayed memories
        response = "Your recently decayed memories:\n\n"

        for i, memory in enumerate(memories, 1):
            content = memory.content[:100] + \
                "..." if len(memory.content) > 100 else memory.content
            response += f"{i}. {content}\n"
            response += f"   Current importance: {memory.importance}\n\n"

        await query.edit_message_text(response)


def register_decay_commands(application) -> None:
    """
    Register decay-related commands.

    Args:
        application: The telegram application
    """
    application.add_handler(CommandHandler(
        "decay_memories", cmd_decay_memories))
    application.add_handler(CommandHandler(
        "show_decay_candidates", cmd_show_decay_candidates))
