"""
Handler for the /createrole command.
"""

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from jyra.ui.buttons import create_callback_button, create_back_button
from jyra.ui.formatting import bold, emoji_prefix
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)

async def create_role_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /createrole command to create a custom roleplay persona.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    # Store the state in user_data
    context.user_data["creating_role"] = True
    context.user_data["role_creation_step"] = "name"
    context.user_data["new_role"] = {}
    
    # Create a visually appealing message with instructions
    message = f"""
{bold("Create a Custom Role")} 🎭

Let's create a personalized roleplay persona for me to adopt!

{emoji_prefix("1️⃣", bold("Step 1:"))} Choose a name for your custom role.
{emoji_prefix("2️⃣", bold("Step 2:"))} Provide a description of the role.
{emoji_prefix("3️⃣", bold("Step 3:"))} Define the personality traits.
{emoji_prefix("4️⃣", bold("Step 4:"))} Specify the speaking style.
{emoji_prefix("5️⃣", bold("Step 5:"))} List knowledge areas.

{bold("First, what should I call this persona?")}
Please enter a name for your custom role.
"""
    
    # Create cancel button
    keyboard = InlineKeyboardMarkup([[
        create_callback_button("❌ Cancel", "cancel_role_creation")
    ]])
    
    await update.message.reply_html(
        message,
        reply_markup=keyboard
    )
