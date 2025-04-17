"""
Handler for the /start command.
"""

from telegram import Update
from telegram.ext import ContextTypes

from jyra.db.models.user import User
from jyra.ui.buttons import create_main_menu_keyboard
from jyra.ui.messages import get_welcome_message
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
    is_new_user = not db_user

    if is_new_user:
        db_user = User(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code
        )
        await db_user.save()

        # Set onboarding state for new users
        context.user_data["onboarding_state"] = "welcome"
        context.user_data["onboarding_step"] = 1

    # Get user's name (first name or username)
    name = user.first_name or user.username or "there"

    # Get welcome message using our template
    welcome_text = get_welcome_message(name, is_new_user)

    # Create main menu keyboard
    keyboard = create_main_menu_keyboard()

    # Send welcome message with menu
    await update.message.reply_html(
        welcome_text,
        reply_markup=keyboard
    )

    # If new user, schedule the first onboarding message
    if is_new_user:
        context.job_queue.run_once(
            send_onboarding_step,
            3,  # 3 second delay
            data={
                "user_id": user.id,
                "chat_id": update.effective_chat.id,
                "step": 1
            }
        )


async def send_onboarding_step(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send an onboarding step message.

    Args:
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    step = job_data["step"]

    # Define onboarding steps
    onboarding_steps = [
        {
            "text": "Let me show you around! First, you can choose different personas for me to adopt using the <b>Roles</b> button.",
            "keyboard": create_main_menu_keyboard()
        },
        {
            "text": "I can also remember important things about you. Use the <b>Memory</b> button or the /remember command to store information.",
            "keyboard": create_main_menu_keyboard()
        },
        {
            "text": "You can customize how I interact with you using the <b>Settings</b> button.",
            "keyboard": create_main_menu_keyboard()
        },
        {
            "text": "If you ever need help, just use the <b>Help</b> button or type /help.",
            "keyboard": create_main_menu_keyboard()
        },
        {
            "text": "That's it for now! Feel free to start chatting with me or explore the features using the buttons below.",
            "keyboard": create_main_menu_keyboard()
        }
    ]

    # Check if we have more steps
    if step <= len(onboarding_steps):
        current_step = onboarding_steps[step-1]

        # Send the onboarding message
        await context.bot.send_message(
            chat_id=chat_id,
            text=current_step["text"],
            reply_markup=current_step["keyboard"],
            parse_mode='HTML'
        )

        # Schedule the next step if there is one
        if step < len(onboarding_steps):
            context.job_queue.run_once(
                send_onboarding_step,
                5,  # 5 second delay between steps
                data={
                    "chat_id": chat_id,
                    "step": step + 1
                }
            )
