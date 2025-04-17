"""
Handler for the /role command.
"""

from telegram import Update
from telegram.ext import ContextTypes

from jyra.db.models.role import Role
from jyra.ui.buttons import create_role_selection_keyboard
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)

async def role_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /role command to select a roleplay persona.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    user_id = update.effective_user.id

    # Get available roles
    roles = await Role.get_all_roles(include_custom=True, created_by=user_id)

    if not roles:
        # Initialize default roles if none exist
        await Role.initialize_default_roles()
        roles = await Role.get_all_roles(include_custom=True, created_by=user_id)
    
    # Convert roles to list of dictionaries for the keyboard function
    role_dicts = []
    for role in roles:
        role_dict = {
            "role_id": role.role_id,
            "name": role.name,
            "emoji": get_role_emoji(role.name),  # Helper function to get emoji
            "description": role.description,
            "is_custom": role.is_custom
        }
        role_dicts.append(role_dict)
    
    # Create role selection keyboard
    keyboard = create_role_selection_keyboard(role_dicts)
    
    await update.message.reply_text(
        "Please select a roleplay persona for me:",
        reply_markup=keyboard
    )

def get_role_emoji(role_name: str) -> str:
    """
    Get an appropriate emoji for a role based on its name.
    
    Args:
        role_name: The name of the role
        
    Returns:
        An emoji string
    """
    # Map common role names to emojis
    role_emojis = {
        "therapist": "👨‍⚕️",
        "counselor": "🧠",
        "friend": "👫",
        "assistant": "🤖",
        "chef": "👨‍🍳",
        "teacher": "👩‍🏫",
        "coach": "👨‍🏫",
        "mentor": "🧙‍♂️",
        "guide": "🧭",
        "companion": "🌟",
        "advisor": "📚",
        "philosopher": "🧐",
        "scientist": "👨‍🔬",
        "artist": "🎨",
        "poet": "📝",
        "storyteller": "📖",
        "comedian": "🤣",
        "motivator": "💪",
        "historian": "📜",
        "detective": "🕵️",
        "wizard": "🧙‍♂️",
        "alien": "👽"
    }
    
    # Check if the role name contains any of the keys
    role_name_lower = role_name.lower()
    for key, emoji in role_emojis.items():
        if key in role_name_lower:
            return emoji
    
    # Default emoji if no match
    return "🎭"

# Alias for switch_role_command
switch_role_command = role_command
