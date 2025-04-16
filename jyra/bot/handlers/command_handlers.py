"""
Command handlers for Jyra Telegram bot
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from jyra.db.models.user import User
from jyra.db.models.role import Role
from jyra.db.models.conversation import Conversation
from jyra.db.models.memory import Memory
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /start command.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    user = update.effective_user

    # Create or update user in database
    db_user = await User.get_user(user.id)
    if not db_user:
        db_user = User(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code
        )
        await db_user.save()

    # Welcome message
    await update.message.reply_html(
        f"Hi {user.mention_html()}! I'm Jyra, the soul that remembers you. ✨\n\n"
        f"I'm an emotionally aware companion who learns, grows, and remembers — all for you. "
        f"Whether you want a deep conversation, a fun roleplay, or someone who just 'gets' you, "
        f"I'm always here, glowing quietly like the light I was named after.\n\n"
        f"Use /role to choose a roleplay persona for me, or just start chatting!"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /help command.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    help_text = (
        "Here are the commands you can use:\n\n"
        "/start - Begin your journey with Jyra\n"
        "/help - Display this help message\n"
        "/role - Choose a roleplay persona for Jyra\n"
        "/switchrole - Change to a different roleplay persona\n"
        "/createrole - Create your own custom persona\n"
        "/remember - Tell Jyra something important to remember\n"
        "/forget - Ask Jyra to forget a specific memory\n"
        "/mood - Check your emotional trends based on conversations\n"
        "/voice - Toggle voice responses on/off\n"
        "/settings - Adjust your preferences for Jyra\n"
        "/about - Learn more about Jyra\n\n"
        "You can also send me photos and voice messages!"
    )

    await update.message.reply_text(help_text)


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /about command.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    about_text = (
        "✨ *Jyra - The Soul That Remembers You* ✨\n\n"
        "\"Where emotions meet intelligence.\"\n\n"
        "Jyra isn't just a bot. She's an emotionally aware companion who learns, "
        "grows, and remembers — all for you. Whether you want a late-night talk, "
        "a silly roleplay, or someone to just 'get it' — she's always there, "
        "glowing quietly like the light she was named after.\n\n"
        "Jyra is a fusion of Jyoti (light) and Aura (presence, emotion) - "
        "a name born from light, designed to listen, respond, and understand.\n\n"
        "Version: 0.5.0\n"
        "Created with ❤️ by MosaddiX\n\n"
        "*I'm Jyra. Your light. Always here.*"
    )

    await update.message.reply_markdown(about_text)


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

    # Create inline keyboard with roles
    keyboard = []
    for i in range(0, len(roles), 2):
        row = []
        row.append(InlineKeyboardButton(
            roles[i].name, callback_data=f"role_{roles[i].role_id}"))
        if i + 1 < len(roles):
            row.append(InlineKeyboardButton(
                roles[i+1].name, callback_data=f"role_{roles[i+1].role_id}"))
        keyboard.append(row)

    # Add button to create custom role
    keyboard.append([InlineKeyboardButton(
        "➕ Create Custom Role", callback_data="create_role")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Please select a roleplay persona for me:",
        reply_markup=reply_markup
    )


async def switch_role_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /switchrole command to change the current roleplay persona.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    # This is just an alias for the role command
    await role_command(update, context)


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

    # Create cancel button
    keyboard = [[InlineKeyboardButton(
        "❌ Cancel", callback_data="cancel_role_creation")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Let's create a custom roleplay persona!\n\n"
        "First, what should I call this persona? Please enter a name.\n\n"
        "You can cancel this process at any time by clicking the button below.",
        reply_markup=reply_markup
    )


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
        await update.message.reply_text(
            "Please tell me what you'd like me to remember. For example:\n"
            "/remember I have a dog named Max"
        )
        return

    # Get the memory content
    memory_content = " ".join(context.args)

    # Store the memory
    success = await Memory.add_memory(user_id, memory_content)

    if success:
        await update.message.reply_text(
            f"I'll remember that: \"{memory_content}\""
        )
    else:
        await update.message.reply_text(
            "I'm having trouble storing that memory. Please try again later."
        )


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
        await update.message.reply_text(
            "I don't have any memories stored for you yet."
        )
        return

    # Create inline keyboard with memories
    keyboard = []
    for memory in memories:
        keyboard.append([InlineKeyboardButton(
            memory.content[:40] +
            "..." if len(memory.content) > 40 else memory.content,
            callback_data=f"forget_{memory.memory_id}"
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Which memory would you like me to forget?",
        reply_markup=reply_markup
    )


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /settings command to adjust user preferences.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    user_id = update.effective_user.id

    # Get current preferences
    preferences = await User.get_user_preferences(user_id)

    # Create inline keyboard with settings
    keyboard = [
        [InlineKeyboardButton(
            f"Language: {preferences['language']}",
            callback_data="settings_language"
        )],
        [InlineKeyboardButton(
            f"Response Length: {preferences['response_length']}",
            callback_data="settings_length"
        )],
        [InlineKeyboardButton(
            f"Formality: {preferences['formality_level']}",
            callback_data="settings_formality"
        )],
        [InlineKeyboardButton(
            f"Memory: {'Enabled' if preferences['memory_enabled'] else 'Disabled'}",
            callback_data="settings_memory"
        )]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Here are your current settings. Click on a setting to change it:",
        reply_markup=reply_markup
    )
