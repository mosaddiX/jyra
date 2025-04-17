"""
Callback handlers for memory management menu interactions.
"""

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from jyra.ui.buttons import create_memory_keyboard, create_memory_category_keyboard, create_callback_button
from jyra.ui.keyboards import create_main_menu_keyboard
from jyra.ui.messages import get_error_message, format_message
from jyra.ui.formatting import bold, italic, emoji_prefix
from jyra.db.models.user import User
from jyra.db.models.memory import Memory
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


async def handle_memory_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle memory-related callback queries.
    """
    query = update.callback_query
    await query.answer()
    callback_data = query.data
    user_id = update.effective_user.id

    # Main memory menu
    if callback_data == "memory_main":
        await query.message.edit_text(
            f"{bold('Memory Management')}\n\nManage your memories and help me remember important information about you.",
            reply_markup=create_memory_keyboard(),
            parse_mode='HTML'
        )
        return

    # Add Memory
    elif callback_data == "memory_add":
        await query.message.edit_text(
            f"{bold('Add Memory')}\n\nWhat would you like me to remember?\n\nSend your memory as a message.",
            reply_markup=create_memory_keyboard(),
            parse_mode='HTML'
        )
        context.user_data['memory_add_mode'] = True
        context.user_data['memory_category'] = 'general'  # Default category
        context.user_data['memory_importance'] = 1  # Default importance
        return

    # Add Memory to specific category
    elif callback_data.startswith("memory_add_to_"):
        category = callback_data[len("memory_add_to_"):]
        await query.message.edit_text(
            f"{bold(f'Add Memory to {category.capitalize()}')}\n\nWhat would you like me to remember in the {
                category} category?\n\nSend your memory as a message.",
            reply_markup=InlineKeyboardMarkup([[
                create_callback_button(
                    "⬅️ Back", f"memory_category_{category}")
            ]]),
            parse_mode='HTML'
        )
        context.user_data['memory_add_mode'] = True
        context.user_data['memory_category'] = category
        context.user_data['memory_importance'] = 1  # Default importance
        return

    # Search Memory
    elif callback_data == "memory_search":
        await query.message.edit_text(
            f"{bold('Search Memories')}\n\nWhat would you like to search for in your memories?\n\nSend your search query as a message.",
            reply_markup=create_memory_keyboard(),
            parse_mode='HTML'
        )
        context.user_data['memory_search_mode'] = True
        # Search all categories
        context.user_data['memory_search_category'] = None
        return

    # Search in specific category
    elif callback_data.startswith("memory_search_in_"):
        category = callback_data[len("memory_search_in_"):]
        await query.message.edit_text(
            f"{bold(f'Search in {category.capitalize()}')}\n\nWhat would you like to search for in your {
                category} memories?\n\nSend your search query as a message.",
            reply_markup=InlineKeyboardMarkup([[
                create_callback_button(
                    "⬅️ Back", f"memory_category_{category}")
            ]]),
            parse_mode='HTML'
        )
        context.user_data['memory_search_mode'] = True
        context.user_data['memory_search_category'] = category
        return

    # Browse Categories
    elif callback_data == "memory_categories":
        await query.message.edit_text(
            f"{bold('Memory Categories')}\n\nBrowse your memories by category:\n",
            reply_markup=create_memory_keyboard(show_categories=True),
            parse_mode='HTML'
        )
        return

    # Memory Map (placeholder)
    elif callback_data == "memory_map":
        await query.message.edit_text(
            f"{bold('Memory Map')}\n\n🗺️ Memory Map is coming soon! You'll be able to view a visual map of your memories and how they connect.",
            reply_markup=create_memory_keyboard(),
            parse_mode='HTML'
        )
        return

    # Recent Memories
    elif callback_data == "memory_recent":
        # Get recent memories across all categories
        memories = await Memory.get_memories(user_id, limit=10)
        if not memories:
            await query.message.edit_text(
                f"{bold('Recent Memories')}\n\nYou don't have any memories yet. Use the 'Add Memory' button to create some!",
                reply_markup=create_memory_keyboard(),
                parse_mode='HTML'
            )
        else:
            # Format memories with timestamps
            memory_list = []
            for i, memory in enumerate(memories):
                created_at = memory.created_at.split(
                    ' ')[0] if memory.created_at else 'Unknown date'
                memory_list.append(f"{i+1}. [{created_at}] {memory.content}")

            text = f"{bold('Recent Memories')}\n\n" + "\n\n".join(memory_list)

            # Add pagination if needed
            keyboard = [[
                create_callback_button("⬅️ Back to Memory Menu", "memory_main")
            ]]

            await query.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        return

    # Important Memories
    elif callback_data == "memory_important":
        # Get important memories (importance >= 4)
        memories = await Memory.get_memories(user_id, min_importance=4)
        if not memories:
            await query.message.edit_text(
                f"{bold('Important Memories')}\n\nYou don't have any high-importance memories yet.",
                reply_markup=create_memory_keyboard(),
                parse_mode='HTML'
            )
        else:
            # Format memories with importance level
            memory_list = []
            for memory in memories:
                stars = '⭐' * memory.importance
                memory_list.append(f"{stars} {memory.content}")

            text = f"{bold('Important Memories')}\n\n" + \
                "\n\n".join(memory_list)

            await query.message.edit_text(
                text,
                reply_markup=create_memory_keyboard(),
                parse_mode='HTML'
            )
        return

    # Memory Category
    elif callback_data.startswith("memory_category_"):
        category = callback_data[len("memory_category_"):]
        # Validate category
        valid_categories = [
            "personal", "preferences", "facts", "work", "interests",
            "relationships", "places", "events", "education", "food",
            "finance", "hobbies", "general"
        ]

        if category not in valid_categories:
            await query.message.edit_text(
                f"Unknown memory category: '{category}'.",
                reply_markup=create_memory_keyboard(show_categories=True),
                parse_mode='HTML'
            )
            return

        # Fetch user memories in this category
        memories = await Memory.get_memories(user_id, category=category, limit=10)
        has_memories = len(memories) > 0

        # Create category-specific keyboard
        keyboard = create_memory_category_keyboard(category, has_memories)

        if not has_memories:
            await query.message.edit_text(
                f"{bold(f'{category.capitalize()} Memories')
                   }\n\nNo memories found in this category yet. Add some using the button below!",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        else:
            # Format memories with importance indicators
            memory_list = []
            for memory in memories:
                importance = '⭐' * memory.importance if memory.importance > 0 else ''
                memory_list.append(f"{importance} {memory.content}")

            text = f"{bold(f'{category.capitalize()} Memories')
                      }\n\n" + "\n\n".join(memory_list)

            await query.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        return

    # View all memories in a category
    elif callback_data.startswith("memory_view_all_"):
        category = callback_data[len("memory_view_all_"):]
        # Get all memories in this category
        memories = await Memory.get_memories(user_id, category=category)

        if not memories:
            await query.message.edit_text(
                f"{bold(f'All {category.capitalize()} Memories')
                   }\n\nNo memories found in this category.",
                reply_markup=create_memory_category_keyboard(category, False),
                parse_mode='HTML'
            )
        else:
            # Format memories with IDs for potential deletion
            memory_list = []
            for memory in memories:
                memory_list.append(
                    f"ID: {memory.memory_id} - {memory.content}")

            text = f"{bold(f'All {category.capitalize()} Memories')
                      }\n\n" + "\n\n".join(memory_list)

            # Add delete instructions
            text += f"\n\n{italic('To delete a memory, use /forget followed by the memory ID.')}"
            await query.message.edit_text(
                text,
                reply_markup=create_memory_category_keyboard(category),
                parse_mode='HTML'
            )
        return

    # View memories by importance in a category
    elif callback_data.startswith("memory_importance_"):
        category = callback_data[len("memory_importance_"):]
        # Create importance selection keyboard
        keyboard = []
        for i in range(5, 0, -1):
            stars = '⭐' * i
            keyboard.append([create_callback_button(
                f"{stars} Importance {i}", f"memory_importance_level_{category}_{i}")])

        keyboard.append([create_callback_button(
            "⬅️ Back", f"memory_category_{category}")])

        await query.message.edit_text(
            f"{bold(f'Browse {category.capitalize()} Memories by Importance')
               }\n\nSelect an importance level:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return

    # View memories with specific importance level
    elif callback_data.startswith("memory_importance_level_"):
        parts = callback_data[len("memory_importance_level_"):].split('_')
        if len(parts) != 2:
            await query.message.edit_text(
                "Invalid importance level selection.",
                reply_markup=create_memory_keyboard(),
                parse_mode='HTML'
            )
            return

        category, importance = parts[0], int(parts[1])

        # Get memories with the specified importance
        memories = await Memory.get_memories(
            user_id,
            category=category,
            min_importance=importance,
            max_importance=importance
        )

        if not memories:
            await query.message.edit_text(
                f"{bold(f'{category.capitalize()} Memories - Importance {importance}')
                   }\n\nNo memories found with this importance level.",
                reply_markup=InlineKeyboardMarkup([[
                    create_callback_button(
                        "⬅️ Back", f"memory_importance_{category}")
                ]]),
                parse_mode='HTML'
            )
        else:
            # Format memories
            memory_list = []
            for memory in memories:
                memory_list.append(
                    f"ID: {memory.memory_id} - {memory.content}")

            text = f"{bold(f'{category.capitalize()} Memories - Importance {importance}')
                      }\n\n" + "\n\n".join(memory_list)

            await query.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup([[
                    create_callback_button(
                        "⬅️ Back", f"memory_importance_{category}")
                ]]),
                parse_mode='HTML'
            )
        return

    # Export Memories
    elif callback_data == "memory_export":
        # Get all memories
        memories = await Memory.get_memories(user_id)

        if not memories:
            await query.message.edit_text(
                f"{bold('Export Memories')}\n\nYou don't have any memories to export.",
                reply_markup=create_memory_keyboard(),
                parse_mode='HTML'
            )
            return

        # Format memories for export
        export_text = "# Exported Memories\n\n"

        # Group by category
        categories = {}
        for memory in memories:
            if memory.category not in categories:
                categories[memory.category] = []
            categories[memory.category].append(memory)

        # Format each category
        for category, category_memories in categories.items():
            export_text += f"## {category.capitalize()}\n\n"
            for memory in category_memories:
                stars = '⭐' * memory.importance if memory.importance > 0 else ''
                date = memory.created_at.split(
                    ' ')[0] if memory.created_at else 'Unknown date'
                export_text += f"- {stars} [{date}] {memory.content}\n"
            export_text += "\n"

        # Send as a text file
        await query.message.reply_document(
            document=export_text.encode('utf-8'),
            filename="memories_export.md",
            caption="Here are your exported memories."
        )

        await query.message.edit_text(
            f"{bold('Export Memories')}\n\nYour memories have been exported successfully!",
            reply_markup=create_memory_keyboard(),
            parse_mode='HTML'
        )
        return

    # Export memories from a specific category
    elif callback_data.startswith("memory_export_"):
        category = callback_data[len("memory_export_"):]
        # Get memories in this category
        memories = await Memory.get_memories(user_id, category=category)

        if not memories:
            await query.message.edit_text(
                f"{bold(f'Export {category.capitalize()} Memories')
                   }\n\nNo memories found in this category to export.",
                reply_markup=create_memory_category_keyboard(category, False),
                parse_mode='HTML'
            )
            return

        # Format memories for export
        export_text = f"# Exported {category.capitalize()} Memories\n\n"

        for memory in memories:
            stars = '⭐' * memory.importance if memory.importance > 0 else ''
            date = memory.created_at.split(
                ' ')[0] if memory.created_at else 'Unknown date'
            export_text += f"- {stars} [{date}] {memory.content}\n"

        # Send as a text file
        await query.message.reply_document(
            document=export_text.encode('utf-8'),
            filename=f"{category}_memories_export.md",
            caption=f"Here are your exported {category} memories."
        )

        await query.message.edit_text(
            f"{bold(f'Export {category.capitalize()} Memories')}\n\nYour {
                category} memories have been exported successfully!",
            reply_markup=create_memory_category_keyboard(category),
            parse_mode='HTML'
        )
        return

    # Import Memories (placeholder)
    elif callback_data == "memory_import":
        await query.message.edit_text(
            f"{bold('Import Memories')}\n\nTo import memories, please send a text file with one memory per line.\n\n{italic('Format: Category|Importance|Memory Content')}\n\nExample:\npersonal|3|I like chocolate\npreferences|4|I prefer window seats on flights",
            reply_markup=create_memory_keyboard(),
            parse_mode='HTML'
        )
        context.user_data['memory_import_mode'] = True
        return

    # View memories by date in a category
    elif callback_data.startswith("memory_date_"):
        category = callback_data[len("memory_date_"):]
        # Get memories in this category
        memories = await Memory.get_memories(user_id, category=category)

        if not memories:
            await query.message.edit_text(
                f"{bold(f'{category.capitalize()} Memories by Date')
                   }\n\nNo memories found in this category.",
                reply_markup=create_memory_category_keyboard(category, False),
                parse_mode='HTML'
            )
            return

        # Sort memories by date
        memories.sort(
            key=lambda m: m.created_at if m.created_at else "0000-00-00")

        # Group memories by month/year
        date_groups = {}
        for memory in memories:
            date_str = memory.created_at.split(
                ' ')[0] if memory.created_at else 'Unknown date'
            if date_str != 'Unknown date':
                # Extract year and month
                year_month = date_str[:7]  # YYYY-MM
                if year_month not in date_groups:
                    date_groups[year_month] = []
                date_groups[year_month].append(memory)
            else:
                if 'Unknown date' not in date_groups:
                    date_groups['Unknown date'] = []
                date_groups['Unknown date'].append(memory)

        # Format memories by date group
        text = f"{bold(f'{category.capitalize()} Memories by Date')}\n\n"

        for date_group, group_memories in sorted(date_groups.items(), reverse=True):
            if date_group != 'Unknown date':
                # Format date as Month Year
                import datetime
                try:
                    date_obj = datetime.datetime.strptime(date_group, "%Y-%m")
                    formatted_date = date_obj.strftime("%B %Y")
                except:
                    formatted_date = date_group
            else:
                formatted_date = date_group

            text += f"{bold(formatted_date)}\n"
            for memory in group_memories:
                stars = '⭐' * memory.importance if memory.importance > 0 else ''
                text += f"- {stars} {memory.content}\n"
            text += "\n"

        await query.message.edit_text(
            text,
            reply_markup=create_memory_category_keyboard(category),
            parse_mode='HTML'
        )
        return

    # Back to Menu
    elif callback_data == "menu_main":
        await query.message.edit_text(
            "What would you like to do?",
            reply_markup=create_main_menu_keyboard()
        )
        return

    # Unknown memory callback
    else:
        logger.warning(f"Unknown memory callback: {callback_data}")
        await query.message.edit_text(
            get_error_message("Unknown memory action."),
            reply_markup=create_memory_keyboard(),
            parse_mode='HTML'
        )
        return
