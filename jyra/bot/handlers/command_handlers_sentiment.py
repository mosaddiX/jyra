"""
Command handlers for Jyra Telegram bot with sentiment analysis
"""

from jyra.bot.handlers.command_handlers import (
    start_command, help_command, about_command, role_command,
    switch_role_command, create_role_command, remember_command,
    forget_command, settings_command
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import matplotlib.pyplot as plt
import io
from collections import Counter

from jyra.db.models.user import User
from jyra.db.models.role import Role
from jyra.db.models.conversation import Conversation
from jyra.db.models.memory import Memory
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)

# Import all existing command handlers

# Update help_command to include mood command


async def help_command_with_mood(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /help command with mood command included.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    help_text = (
        "Here are the commands you can use:\n\n"
        "🤖 *Core Commands*\n"
        "/start - Begin your journey with Jyra\n"
        "/help - Display this help message\n"
        "/about - Learn more about Jyra\n\n"
        "🎭 *Roleplay Commands*\n"
        "/role - Choose a roleplay persona for Jyra\n"
        "/switchrole - Change to a different roleplay persona\n"
        "/createrole - Create your own custom persona\n\n"
        "🧠 *Memory Commands*\n"
        "/remember - Tell Jyra something important to remember\n"
        "/forget - Ask Jyra to forget a specific memory\n\n"
        "🔧 *Settings Commands*\n"
        "/voice - Toggle voice responses on/off\n"
        "/settings - Adjust your preferences for Jyra\n\n"
        "📊 *Analysis Commands*\n"
        "/mood - Check your emotional trends based on conversations\n\n"
        "🌐 *Community Commands*\n"
        "/feedback - Share your feedback about Jyra\n"
        "/featurerequest - Suggest a new feature for Jyra\n"
        "/support - Create a support ticket for help\n"
        "/ticketstatus - Check the status of your support tickets\n\n"
        "You can also send me photos and voice messages!"
    )

    await update.message.reply_markdown(help_text)


async def mood_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /mood command to show emotional trends.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    user_id = update.effective_user.id

    # Check if we have sentiment history
    sentiment_history = context.user_data.get("sentiment_history", [])

    if not sentiment_history:
        await update.message.reply_text(
            "I haven't analyzed enough of our conversations yet to determine your emotional trends. "
            "Let's chat a bit more, and I'll be able to provide insights soon!"
        )
        return

    # Get the most recent sentiment
    current_sentiment = sentiment_history[-1]

    # Count emotions in history
    emotions = [s["primary_emotion"] for s in sentiment_history]
    emotion_counts = Counter(emotions)
    most_common_emotion = emotion_counts.most_common(
        1)[0][0] if emotion_counts else "neutral"

    # Calculate average intensity
    avg_intensity = sum(s["intensity"]
                        for s in sentiment_history) / len(sentiment_history)

    # Create a text summary
    summary = (
        f"📊 *Your Emotional Trends*\n\n"
        f"Current mood: {current_sentiment['primary_emotion']} (intensity: {current_sentiment['intensity']}/5)\n"
        f"Most frequent emotion: {most_common_emotion}\n"
        f"Average emotional intensity: {avg_intensity:.1f}/5\n\n"
    )

    if current_sentiment["explanation"]:
        summary += f"*Current mood analysis*: {current_sentiment['explanation']}\n\n"

    # Add emotion distribution
    summary += "*Recent emotion distribution*:\n"
    for emotion, count in emotion_counts.most_common():
        percentage = (count / len(sentiment_history)) * 100
        summary += f"- {emotion}: {percentage:.1f}% ({count} occurrences)\n"

    # Send the summary
    await update.message.reply_markdown(summary)

    # If we have enough data, create and send a visualization
    if len(sentiment_history) >= 3:
        await send_mood_visualization(update, sentiment_history)


async def send_mood_visualization(update: Update, sentiment_history: list) -> None:
    """
    Create and send a visualization of mood trends.

    Args:
        update (Update): The update object
        sentiment_history (list): List of sentiment analysis results
    """
    try:
        # Create a simple bar chart of emotions
        emotions = [s["primary_emotion"] for s in sentiment_history]
        emotion_counts = Counter(emotions)

        # Create the plot
        plt.figure(figsize=(10, 6))

        # Bar chart of emotions
        emotions = list(emotion_counts.keys())
        counts = list(emotion_counts.values())

        # Sort by count
        sorted_data = sorted(zip(emotions, counts),
                             key=lambda x: x[1], reverse=True)
        emotions = [item[0] for item in sorted_data]
        counts = [item[1] for item in sorted_data]

        plt.bar(emotions, counts, color='skyblue')
        plt.title('Your Emotional Distribution')
        plt.xlabel('Emotion')
        plt.ylabel('Frequency')
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save the plot to a buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)

        # Send the image
        await update.message.reply_photo(buf, caption="Your emotional distribution from our recent conversations.")

        # Close the plot to free memory
        plt.close()

    except Exception as e:
        logger.error(f"Error creating mood visualization: {str(e)}")
        # If visualization fails, just continue without sending an image
