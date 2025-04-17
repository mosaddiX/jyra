"""
Enhanced message handler for Jyra bot.

This module provides an enhanced message handler that uses the new UI components.
"""

from telegram import Update
from telegram.ext import ContextTypes

from jyra.db.models.user import User
from jyra.db.models.role import Role
from jyra.db.models.conversation import Conversation
from jyra.db.models.memory import Memory
from jyra.ai.models.model_manager import model_manager
from jyra.ai.memory_manager import memory_manager
from jyra.ai.sentiment.sentiment_analyzer import SentimentAnalyzer
from jyra.ui.keyboards import create_conversation_controls
from jyra.ui.visual_feedback import show_loading_indicator, stop_loading_indicator, show_error_message
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)

# Initialize sentiment analyzer
sentiment_analyzer = SentimentAnalyzer()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle user messages with enhanced UI.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    user_id = update.effective_user.id
    user_message = update.message.text

    # Get user from database
    user = await User.get_user(user_id)
    if not user:
        # Create user if not exists
        user = User(
            user_id=user_id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name,
            last_name=update.effective_user.last_name,
            language_code=update.effective_user.language_code
        )
        await user.save()

    # Get current role
    role_id = user.current_role_id
    if not role_id:
        # Use default role if none is set
        default_roles = await Role.get_all_roles(include_custom=False)
        if default_roles:
            role_id = default_roles[0].role_id
            user.current_role_id = role_id
            await user.save()

    role = await Role.get_role(role_id) if role_id else None

    # Get role context
    role_context = {
        "name": role.name if role else "AI Assistant",
        "personality": role.personality if role else "Helpful and friendly",
        "speaking_style": role.speaking_style if role else "Conversational",
        "knowledge_areas": role.knowledge_areas if role else "General knowledge",
        "behaviors": role.behaviors if role else "Responds helpfully"
    }

    # Get conversation history
    conversation_history = await Conversation.get_conversation_history(user_id, role_id)

    # Process user message for memory extraction
    user_context = {
        "role": role.name if role else "AI Assistant",
        "recent_messages": [msg["content"] for msg in conversation_history[-3:]] if conversation_history else []
    }

    await memory_manager.process_user_message(user_id, user_message, user_context)

    # Get relevant memories for the current context
    relevant_memories = await memory_manager.get_relevant_memories(
        user_id=user_id,
        context=user_message,
        max_memories=7,
        min_importance=2
    )

    # Format memories for context
    memory_context = await memory_manager.format_memories_for_context(relevant_memories)

    # Show loading indicator
    await show_loading_indicator(
        update, context, "Thinking", animation_type="dots"
    )

    try:
        # Analyze sentiment
        sentiment_result = await sentiment_analyzer.analyze_sentiment(user_message)

        # Store sentiment in user_data
        if "sentiment_history" not in context.user_data:
            context.user_data["sentiment_history"] = []

        context.user_data["sentiment_history"].append(sentiment_result)

        # Generate response with fallback capability
        response_tuple = await model_manager.generate_response(
            prompt=user_message,
            role_context=role_context,
            conversation_history=conversation_history,
            memory_context=memory_context,
            temperature=0.7,
            max_tokens=1000,
            use_fallbacks=True
        )

        # Extract response and model used
        response, model_used = response_tuple
        logger.info(f"Response generated using model: {model_used}")

        # Stop loading indicator
        await stop_loading_indicator(context, True)

        # Store conversation
        await Conversation.add_message(user_id, role_id, user_message, response)

        # Determine if we should use compact controls based on response length
        use_compact = len(response) < 100

        # Create conversation controls
        keyboard = create_conversation_controls(compact=use_compact)

        # Send response with controls
        await update.message.reply_text(
            response,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

        # Store the conversation in user_data for context
        if "conversation_context" not in context.user_data:
            context.user_data["conversation_context"] = {}

        context.user_data["conversation_context"]["last_response"] = response
        context.user_data["conversation_context"]["last_message"] = user_message
        context.user_data["conversation_context"]["current_role_id"] = role_id

    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")

        # Stop loading indicator with error
        await stop_loading_indicator(context, False, "Error generating response")

        # Show error message
        await show_error_message(
            update,
            context,
            "I'm having trouble connecting to my AI brain right now.",
            "Please try again in a moment. If the problem persists, contact support."
        )
