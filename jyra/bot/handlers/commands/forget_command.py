"""
Handler for the /forget command.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from jyra.db.models.memory import Memory
from jyra.ui.buttons import create_callback_button, create_main_menu_keyboard
from jyra.ui.formatting import bold, italic, emoji_prefix
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)

async def forget_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /forget command to remove stored information.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    user_id = update.effective_user.id

    # Get user memories
    memories = await Memory.get_memories(user_id)

    if not memories:
        # Create a visually appealing message
        message = f"""
{bold("No Memories Found")} 🔍

I don't have any memories stored for you yet.

You can create memories using the {bold("/remember")} command:
/remember I have a dog named Max
"""
        
        # Create button to add memory
        keyboard = InlineKeyboardMarkup([
            [
                create_callback_button("📝 Add Memory", "memory_add")
            ],
            [
                create_callback_button("⬅️ Back to Menu", "menu_main")
            ]
        ])
        
        await update.message.reply_html(
            message,
            reply_markup=keyboard
        )
        return

    # Group memories by category
    memories_by_category = {}
    for memory in memories:
        category = memory.category
        if category not in memories_by_category:
            memories_by_category[category] = []
        memories_by_category[category].append(memory)
    
    # Create a visually appealing message
    message = f"""
{bold("Memory Management")} 🧠

Select a memory to forget:

{italic("Note: This action cannot be undone.")}
"""
    
    # Create inline keyboard with categorized memories
    keyboard = []
    
    # Add category buttons if there are multiple categories
    if len(memories_by_category) > 1:
        category_row = []
        for category in memories_by_category:
            category_row.append(
                create_callback_button(
                    f"{get_category_emoji(category)} {category.capitalize()}", 
                    f"memory_category_{category}"
                )
            )
            # Create rows of 2 buttons each
            if len(category_row) == 2:
                keyboard.append(category_row)
                category_row = []
        
        # Add any remaining category buttons
        if category_row:
            keyboard.append(category_row)
    
    # Add memory buttons (limit to 10 for usability)
    memory_count = 0
    for memory in memories[:10]:
        truncated_content = memory.content[:40] + "..." if len(memory.content) > 40 else memory.content
        keyboard.append([
            create_callback_button(
                f"{get_category_emoji(memory.category)} {truncated_content}", 
                f"forget_{memory.memory_id}"
            )
        ])
        memory_count += 1
    
    # Add "More Memories" button if there are more than 10
    if len(memories) > 10:
        keyboard.append([
            create_callback_button(
                f"🔄 Show More ({len(memories) - memory_count} more)", 
                "memory_more"
            )
        ])
    
    # Add back button
    keyboard.append([
        create_callback_button("⬅️ Back to Menu", "menu_main")
    ])
    
    await update.message.reply_html(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def get_category_emoji(category: str) -> str:
    """
    Get an emoji for a memory category.
    
    Args:
        category: The memory category
        
    Returns:
        An emoji representing the category
    """
    category_emojis = {
        "personal": "👤",
        "preferences": "❤️",
        "facts": "🌐",
        "work": "💼",
        "hobbies": "🎨",
        "general": "📝"
    }
    
    return category_emojis.get(category.lower(), "📝")
