"""
Consolidation-related commands for Jyra bot.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

from jyra.ai.consolidation.memory_consolidator import memory_consolidator
from jyra.db.models.memory import Memory
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


async def cmd_consolidate_memories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Automatically consolidate related memories.

    Usage: /consolidate_memories [max_consolidations]

    Examples:
    /consolidate_memories - Consolidate memories with default settings
    /consolidate_memories 5 - Consolidate up to 5 groups of memories
    """
    user_id = update.effective_user.id

    # Parse arguments
    max_consolidations = 3  # Default

    if context.args:
        try:
            max_consolidations = int(context.args[0])
            if max_consolidations < 1:
                max_consolidations = 1
            elif max_consolidations > 10:
                max_consolidations = 10
        except ValueError:
            await update.message.reply_text(
                "Invalid argument. Usage: /consolidate_memories [max_consolidations]")
            return

    # Send a message to indicate the process has started
    message = await update.message.reply_text(
        "Analyzing your memories for consolidation... This may take a moment.")

    try:
        # Run auto consolidation
        result = await memory_consolidator.run_auto_consolidation(
            user_id=user_id,
            max_consolidations=max_consolidations
        )

        if result["success"]:
            if result["consolidated_count"] > 0:
                # Create a message with the results
                response = f"✅ Successfully consolidated {result['consolidated_count']} groups of memories.\n\n"

                # Add information about the new memories
                if "consolidated_memory_ids" in result and result["consolidated_memory_ids"]:
                    response += "New consolidated memories:\n"
                    for i, memory_id in enumerate(result["consolidated_memory_ids"], 1):
                        memory = await Memory.get_memory_by_id(user_id, memory_id)
                        if memory:
                            content = memory.content[:50] + "..." if len(
                                memory.content) > 50 else memory.content
                            response += f"{i}. {content}\n"

                # Add a button to view consolidated memories
                keyboard = [[
                    InlineKeyboardButton(
                        "View Consolidated Memories",
                        callback_data=f"view_consolidated_{user_id}"
                    )
                ]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await message.edit_text(response, reply_markup=reply_markup)
            else:
                await message.edit_text(
                    "No memories were consolidated. Your memories may already be well-organized, "
                    "or there may not be enough related memories to consolidate.")
        else:
            await message.edit_text(f"❌ Error during consolidation: {result['message']}")

    except Exception as e:
        logger.error(f"Error consolidating memories: {str(e)}")
        await message.edit_text(f"❌ Error consolidating memories: {str(e)}")


async def cmd_show_consolidation_candidates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show groups of memories that are candidates for consolidation.

    Usage: /show_consolidation_candidates [min_similarity]

    Examples:
    /show_consolidation_candidates - Show candidates with default similarity threshold
    /show_consolidation_candidates 0.8 - Show candidates with higher similarity threshold
    """
    user_id = update.effective_user.id

    # Parse arguments
    min_similarity = 0.75  # Default

    if context.args:
        try:
            min_similarity = float(context.args[0])
            if min_similarity < 0.5:
                min_similarity = 0.5
            elif min_similarity > 0.95:
                min_similarity = 0.95
        except ValueError:
            await update.message.reply_text(
                "Invalid argument. Usage: /show_consolidation_candidates [min_similarity]")
            return

    # Send a message to indicate the process has started
    message = await update.message.reply_text(
        "Analyzing your memories for potential consolidation... This may take a moment.")

    try:
        # Identify consolidation candidates
        candidates = await memory_consolidator.identify_consolidation_candidates(
            user_id=user_id,
            min_similarity=min_similarity
        )

        if not candidates:
            await message.edit_text(
                "No consolidation candidates found. Your memories may already be well-organized, "
                "or there may not be enough related memories to consolidate.")
            return

        # Create a message with the candidates
        response = f"Found {len(candidates)} groups of related memories that could be consolidated:\n\n"

        # Show the first 3 groups (to avoid message length limits)
        for i, cluster in enumerate(candidates[:3], 1):
            response += f"Group {i}:\n"
            for j, memory in enumerate(cluster, 1):
                content = memory.content[:50] + \
                    "..." if len(memory.content) > 50 else memory.content
                response += f"  {j}. {content}\n"
            response += "\n"

        if len(candidates) > 3:
            response += f"... and {len(candidates) - 3} more groups.\n\n"

        response += "Use /consolidate_memories to automatically consolidate these groups."

        await message.edit_text(response)

    except Exception as e:
        logger.error(f"Error showing consolidation candidates: {str(e)}")
        await message.edit_text(f"❌ Error showing consolidation candidates: {str(e)}")


async def handle_consolidation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback queries for consolidation options.
    """
    query = update.callback_query
    await query.answer()

    # Get the callback data
    data = query.data

    # Handle view consolidated memories
    if data.startswith("view_consolidated_"):
        user_id = int(data.split("_")[-1])

        # Check if the user is authorized
        if user_id != update.effective_user.id:
            await query.edit_message_text(
                "You are not authorized to view these memories.")
            return

        # Get all recent memories
        memories = await Memory.get_memories(
            user_id=user_id,
            min_importance=1,
            limit=50,
            sort_by="recency"
        )

        # Filter to only include memories with source="consolidation"
        memories = [m for m in memories if m.source == "consolidation"][:10]

        if not memories:
            await query.edit_message_text(
                "No consolidated memories found.")
            return

        # Create a message with the consolidated memories
        response = "Your consolidated memories:\n\n"

        for i, memory in enumerate(memories, 1):
            content = memory.content[:100] + \
                "..." if len(memory.content) > 100 else memory.content
            response += f"{i}. {content}\n\n"

        # Add a button to show more details
        keyboard = [[
            InlineKeyboardButton(
                "Show More Details",
                callback_data=f"consolidation_details_{user_id}"
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(response, reply_markup=reply_markup)

    # Handle consolidation details
    elif data.startswith("consolidation_details_"):
        user_id = int(data.split("_")[-1])

        # Check if the user is authorized
        if user_id != update.effective_user.id:
            await query.edit_message_text(
                "You are not authorized to view these details.")
            return

        # Get all recent memories
        memories = await Memory.get_memories(
            user_id=user_id,
            min_importance=1,
            limit=50,
            sort_by="recency"
        )

        # Filter to only include memories with source="consolidation"
        memories = [m for m in memories if m.source == "consolidation"][:5]

        if not memories:
            await query.edit_message_text(
                "No consolidated memories found.")
            return

        # Create a message with detailed information
        response = "Consolidated Memory Details:\n\n"

        for memory in memories:
            response += f"ID: {memory.memory_id}\n"
            response += f"Content: {memory.content[:100]}...\n"
            response += f"Category: {memory.category}\n"
            response += f"Importance: {memory.importance}\n"
            response += f"Created: {memory.created_at}\n"
            if memory.tags:
                response += f"Tags: {', '.join(memory.tags)}\n"
            response += "\n"

        # Add a button to go back
        keyboard = [[
            InlineKeyboardButton(
                "« Back to Consolidated Memories",
                callback_data=f"view_consolidated_{user_id}"
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(response, reply_markup=reply_markup)


def register_consolidation_commands(application) -> None:
    """
    Register consolidation-related commands.

    Args:
        application: The telegram application
    """
    application.add_handler(CommandHandler(
        "consolidate_memories", cmd_consolidate_memories))
    application.add_handler(CommandHandler(
        "show_consolidation_candidates", cmd_show_consolidation_candidates))
