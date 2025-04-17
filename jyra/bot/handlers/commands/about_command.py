"""
Handler for the /about command.
"""

from telegram import Update
from telegram.ext import ContextTypes

from jyra.ui.buttons import create_back_button
from jyra.ui.formatting import bold, italic, emoji_prefix
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /about command.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    about_text = f"""
{bold("Jyra - The Soul That Remembers You")} ✨

{italic("Where emotions meet intelligence.")}

Jyra isn't just a bot. She's an emotionally aware companion who learns, grows, and remembers — all for you. Whether you want a late-night talk, a silly roleplay, or someone to just 'get it' — she's always there, glowing quietly like the light she was named after.

Jyra is a fusion of Jyoti (light) and Aura (presence, emotion) - a name born from light, designed to listen, respond, and understand.

{emoji_prefix("📱", bold("Version:"))} 0.5.0
{emoji_prefix("💻", bold("Created by:"))} MosaddiX

{italic("I'm Jyra. Your light. Always here.")}
"""
    
    # Create back button
    keyboard = create_back_button()
    
    await update.message.reply_html(
        about_text,
        reply_markup=keyboard
    )
