"""
Handler for the /mood command.
"""

import io
import matplotlib.pyplot as plt
from collections import Counter
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from jyra.ui.buttons import create_callback_button, create_main_menu_keyboard
from jyra.ui.formatting import bold, italic, emoji_prefix
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)

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
        # Create a visually appealing message
        message = f"""
{bold("Mood Analysis")} 📊

I haven't analyzed enough of our conversations yet to determine your emotional trends.

Let's chat a bit more, and I'll be able to provide insights soon!

{italic("Tip: The more we chat, the more accurate my analysis will be.")}
"""
        
        # Create buttons
        keyboard = InlineKeyboardMarkup([
            [
                create_callback_button("💬 Start Chatting", "start_chat")
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

    # Count emotions
    emotion_counts = Counter([entry["primary_emotion"] for entry in sentiment_history])
    
    # Get the most common emotion
    most_common_emotion, most_common_count = emotion_counts.most_common(1)[0]
    
    # Calculate average intensity
    total_intensity = sum([entry["intensity"] for entry in sentiment_history])
    avg_intensity = total_intensity / len(sentiment_history)
    
    # Create a pie chart of emotions
    plt.figure(figsize=(8, 6))
    plt.pie(
        emotion_counts.values(), 
        labels=emotion_counts.keys(),
        autopct='%1.1f%%',
        startangle=90,
        colors=['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC', '#C2C2F0', '#99CCCC']
    )
    plt.axis('equal')
    plt.title('Your Emotional Trends', fontsize=16, pad=20)
    
    # Save the chart to a buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    
    # Create a visually appealing message
    message = f"""
{bold("Mood Analysis Results")} 📊

Based on our recent conversations, here's what I've observed about your emotional patterns:

{emoji_prefix("🔍", bold("Primary Emotion:"))} {most_common_emotion.capitalize()} ({most_common_count} occurrences)
{emoji_prefix("⚡", bold("Average Intensity:"))} {avg_intensity:.1f}/5

{italic("This analysis is based on our last")} {len(sentiment_history)} {italic("interactions.")}
"""
    
    # Create buttons
    keyboard = InlineKeyboardMarkup([
        [
            create_callback_button("📊 Detailed Analysis", "mood_detailed")
        ],
        [
            create_callback_button("🔄 Refresh Analysis", "mood_refresh")
        ],
        [
            create_callback_button("⬅️ Back to Menu", "menu_main")
        ]
    ])
    
    # Send the chart and message
    await update.message.reply_photo(
        buf,
        caption=message,
        parse_mode='HTML',
        reply_markup=keyboard
    )
