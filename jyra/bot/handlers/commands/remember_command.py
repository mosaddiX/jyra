"""
Handler for the /remember command.
"""

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from jyra.db.models.memory import Memory
from jyra.ui.buttons import create_callback_button, create_main_menu_keyboard
from jyra.ui.formatting import bold, italic, emoji_prefix
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)

async def remember_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /remember command to store important information.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    user_id = update.effective_user.id

    # Check if there's text after the command
    if not context.args:
        # Create a visually appealing help message
        message = f"""
{bold("Memory Creation")} 🧠

Please tell me what you'd like me to remember by adding text after the command.

{emoji_prefix("📝", bold("Example:"))}
/remember I have a dog named Max

{emoji_prefix("💡", bold("Tip:"))}
You can also categorize your memory by adding #category at the beginning:
/remember #personal I have a dog named Max
/remember #preferences I prefer tea over coffee
/remember #facts My birthday is on May 15th
"""
        
        # Create memory management buttons
        keyboard = InlineKeyboardMarkup([
            [
                create_callback_button("📋 View Memories", "memory_view"),
                create_callback_button("🔍 Search Memories", "memory_search")
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

    # Get the memory content
    memory_content = " ".join(context.args)
    
    # Check for category tag
    category = "general"
    if memory_content.startswith("#"):
        parts = memory_content.split(" ", 1)
        if len(parts) > 1:
            category_tag = parts[0][1:]  # Remove the # symbol
            memory_content = parts[1]
            
            # Map common categories
            category_map = {
                "personal": "personal",
                "preference": "preferences",
                "preferences": "preferences",
                "fact": "facts",
                "facts": "facts",
                "work": "work",
                "hobby": "hobbies",
                "hobbies": "hobbies"
            }
            
            category = category_map.get(category_tag.lower(), category_tag)

    # Store the memory
    success = await Memory.add_memory(
        user_id, 
        memory_content, 
        category=category, 
        importance=3,  # Default importance
        source="explicit"
    )

    if success:
        # Create a visually appealing confirmation message
        message = f"""
{bold("Memory Stored")} ✅

I'll remember that:
{italic(memory_content)}

{emoji_prefix("🏷️", bold("Category:"))} {category.capitalize()}
{emoji_prefix("⭐", bold("Importance:"))} Medium

You can view or manage your memories using the buttons below.
"""
        
        # Create memory management buttons
        keyboard = InlineKeyboardMarkup([
            [
                create_callback_button("📋 View Memories", "memory_view"),
                create_callback_button("🔍 Search Memories", "memory_search")
            ],
            [
                create_callback_button("⬅️ Back to Menu", "menu_main")
            ]
        ])
        
        await update.message.reply_html(
            message,
            reply_markup=keyboard
        )
    else:
        # Error message
        message = f"""
{bold("Memory Storage Failed")} ❌

I'm having trouble storing that memory. Please try again later.

{italic("If this problem persists, please contact support.")}
"""
        
        await update.message.reply_html(
            message,
            reply_markup=create_main_menu_keyboard()
        )
