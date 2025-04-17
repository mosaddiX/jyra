"""
Visualization-related commands for Jyra bot.
"""

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

from jyra.ai.visualization.memory_visualizer import memory_visualizer
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


async def cmd_visualize_memories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Generate and send a visualization of the user's memories.

    Usage: /visualize_memories [max_memories] [min_importance]

    Examples:
    /visualize_memories - Generate visualization with default settings
    /visualize_memories 20 - Generate visualization with max 20 memories
    /visualize_memories 20 2 - Generate visualization with max 20 memories and min importance 2
    """
    user_id = update.effective_user.id

    # Parse arguments
    max_memories = 30  # Default
    min_importance = 1  # Default

    if context.args:
        try:
            max_memories = int(context.args[0])
            if len(context.args) > 1:
                min_importance = int(context.args[1])
        except ValueError:
            await update.message.reply_text(
                "Invalid arguments. Usage: /visualize_memories [max_memories] [min_importance]")
            return

    # Send a message to indicate the process has started
    message = await update.message.reply_text(
        "Generating memory visualization... This may take a moment.")

    try:
        # Generate the visualization
        image_path = await memory_visualizer.generate_memory_graph(
            user_id=user_id,
            max_memories=max_memories,
            min_importance=min_importance,
            include_tags=True,
            include_categories=True,
            similarity_threshold=0.6
        )

        if not os.path.exists(image_path):
            await message.edit_text("❌ Failed to generate visualization.")
            return

        # Create keyboard with options
        keyboard = [
            [
                InlineKeyboardButton(
                    "More Memories", callback_data=f"viz_more_{user_id}"),
                InlineKeyboardButton("Higher Similarity",
                                     callback_data=f"viz_sim_{user_id}")
            ],
            [
                InlineKeyboardButton(
                    "Tags Only", callback_data=f"viz_tags_{user_id}"),
                InlineKeyboardButton(
                    "Categories Only", callback_data=f"viz_cats_{user_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the image
        with open(image_path, 'rb') as image_file:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=image_file,
                caption=f"Memory visualization with {max_memories} memories (min importance: {min_importance})",
                reply_markup=reply_markup
            )

        # Delete the processing message
        await message.delete()

    except Exception as e:
        logger.error(f"Error generating visualization: {str(e)}")
        await message.edit_text(f"❌ Error generating visualization: {str(e)}")


async def handle_visualization_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback queries for visualization options.
    """
    query = update.callback_query
    await query.answer()

    # Get the callback data
    data = query.data
    user_id = int(data.split('_')[-1])

    # Check if the user is authorized
    if user_id != update.effective_user.id:
        await query.edit_message_caption(
            caption="You are not authorized to modify this visualization.")
        return

    # Default parameters
    max_memories = 30
    min_importance = 1
    include_tags = True
    include_categories = True
    similarity_threshold = 0.6

    # Process the callback data
    if data.startswith("viz_more"):
        max_memories = 50
        caption = "Memory visualization with more memories (50)"
    elif data.startswith("viz_sim"):
        similarity_threshold = 0.75
        caption = "Memory visualization with higher similarity threshold (0.75)"
    elif data.startswith("viz_tags"):
        include_categories = False
        caption = "Memory visualization with tags only"
    elif data.startswith("viz_cats"):
        include_tags = False
        caption = "Memory visualization with categories only"
    else:
        await query.edit_message_caption(
            caption="Invalid visualization option.")
        return

    try:
        # Generate the new visualization
        image_path = await memory_visualizer.generate_memory_graph(
            user_id=user_id,
            max_memories=max_memories,
            min_importance=min_importance,
            include_tags=include_tags,
            include_categories=include_categories,
            similarity_threshold=similarity_threshold
        )

        if not os.path.exists(image_path):
            await query.edit_message_caption(
                caption="❌ Failed to generate visualization.")
            return

        # Create keyboard with options
        keyboard = [
            [
                InlineKeyboardButton(
                    "More Memories", callback_data=f"viz_more_{user_id}"),
                InlineKeyboardButton("Higher Similarity",
                                     callback_data=f"viz_sim_{user_id}")
            ],
            [
                InlineKeyboardButton(
                    "Tags Only", callback_data=f"viz_tags_{user_id}"),
                InlineKeyboardButton(
                    "Categories Only", callback_data=f"viz_cats_{user_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the new image
        with open(image_path, 'rb') as image_file:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=image_file,
                caption=caption,
                reply_markup=reply_markup
            )

    except Exception as e:
        logger.error(f"Error generating visualization: {str(e)}")
        await query.edit_message_caption(
            caption=f"❌ Error generating visualization: {str(e)}")


async def cmd_memory_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Generate and send a comprehensive memory dashboard for the user.

    Usage: /memory_dashboard

    This command generates a web-based dashboard with multiple visualizations
    of the user's memories, including a memory graph, category distribution,
    and importance histogram.
    """
    user_id = update.effective_user.id

    # Send a message to indicate the process has started
    message = await update.message.reply_text(
        "Generating memory dashboard... This may take a moment.")

    try:
        # Generate the dashboard
        dashboard_path = await memory_visualizer.generate_memory_dashboard(user_id=user_id)

        if not dashboard_path or not os.path.exists(dashboard_path):
            await message.edit_text("❌ Failed to generate memory dashboard.")
            return

        # Create a message with the dashboard link
        dashboard_url = f"file://{os.path.abspath(dashboard_path)}"

        # Send the dashboard path
        await message.edit_text(
            f"✅ Memory dashboard generated!\n\n"
            f"Dashboard saved to: {dashboard_path}\n\n"
            f"Open this file in your web browser to view the dashboard."
        )

        # Generate and send the category distribution as a preview
        category_path = await memory_visualizer.generate_category_distribution(user_id=user_id)
        if category_path and os.path.exists(category_path):
            with open(category_path, 'rb') as image_file:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=image_file,
                    caption="Memory Category Distribution (preview of dashboard)"
                )

    except Exception as e:
        logger.error(f"Error generating memory dashboard: {str(e)}")
        await message.edit_text(f"❌ Error generating memory dashboard: {str(e)}")


def register_visualization_commands(application) -> None:
    """
    Register visualization-related commands.

    Args:
        application: The telegram application
    """
    application.add_handler(CommandHandler(
        "visualize_memories", cmd_visualize_memories))
    application.add_handler(CommandHandler(
        "memory_dashboard", cmd_memory_dashboard))
