"""
Message handlers for Jyra Telegram bot with sentiment analysis
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from jyra.db.models.user import User
from jyra.db.models.role import Role
from jyra.db.models.conversation import Conversation
from jyra.db.models.memory import Memory
from jyra.ai.models.gemini_direct import GeminiAI
from jyra.ai.sentiment.sentiment_analyzer import SentimentAnalyzer
from jyra.ai.multimodal.tts_processor import TTSProcessor
from jyra.ai.prompts.prompt_templates import PromptTemplates
from jyra.utils.logger import setup_logger
from jyra.bot.handlers.multimodal_handlers import send_voice_response

logger = setup_logger(__name__)

# Initialize AI model and sentiment analyzer
gemini_ai = GeminiAI()
sentiment_analyzer = SentimentAnalyzer()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle user messages and generate AI responses.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    user_id = update.effective_user.id
    user_message = update.message.text

    # Check if user is in role creation process
    if context.user_data.get("creating_role", False):
        await handle_role_creation(update, context)
        return

    # Check if user is in settings change process
    if context.user_data.get("changing_setting", False):
        await handle_settings_change(update, context)
        return

    # Get user from database
    db_user = await User.get_user(user_id)
    if not db_user:
        # Create new user if not exists
        db_user = User(
            user_id=user_id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name,
            last_name=update.effective_user.last_name,
            language_code=update.effective_user.language_code
        )
        await db_user.save()

    # Update last interaction time
    await db_user.update_last_interaction()

    # Check if user has selected a role
    if not db_user.current_role_id:
        await update.message.reply_text(
            "You haven't selected a roleplay persona for me yet. "
            "Please use /role to choose one!"
        )
        return

    # Get the current role
    role = await Role.get_role(db_user.current_role_id)
    if not role:
        await update.message.reply_text(
            "There seems to be an issue with your selected persona. "
            "Please use /role to choose a new one."
        )
        return

    # Get user preferences
    preferences = await User.get_user_preferences(user_id)

    # Get conversation history
    conversation_history = await Conversation.get_conversation_history(
        user_id,
        role_id=db_user.current_role_id
    )

    # Get user memories if enabled
    user_memories = None
    if preferences["memory_enabled"]:
        # Get important memories (importance >= 3)
        important_memories = await Memory.get_memories(user_id, min_importance=3, limit=5)

        # Get recent memories (any importance)
        recent_memories = await Memory.get_memories(user_id, limit=10)

        # Get category-specific memories based on sentiment
        category = "general"
        if sentiment and "primary_emotion" in sentiment:
            if sentiment["primary_emotion"] in ["happy", "excited", "content"]:
                category = "positive"
            elif sentiment["primary_emotion"] in ["sad", "angry", "frustrated"]:
                category = "emotional"
            elif sentiment["primary_emotion"] in ["curious", "interested"]:
                category = "interests"

        category_memories = await Memory.get_memories(user_id, category=category, limit=3)

        # Combine memories, removing duplicates
        all_memories = {}
        for memory in important_memories + recent_memories + category_memories:
            if memory.memory_id not in all_memories:
                all_memories[memory.memory_id] = memory

        # Convert to list of memory contents
        user_memories = [memory.content for memory in all_memories.values()]

        # Get memory summary if available
        memory_summary = await Memory.get_memory_summary(user_id)
        if memory_summary:
            user_memories.insert(0, f"Summary: {memory_summary}")

    # Send typing action
    await update.message.chat.send_action(action="typing")

    # Analyze sentiment
    sentiment = await sentiment_analyzer.analyze_sentiment(user_message)

    # Store sentiment in user_data for future reference
    if "sentiment_history" not in context.user_data:
        context.user_data["sentiment_history"] = []

    # Add sentiment to history (keep last 10)
    context.user_data["sentiment_history"].append(sentiment)
    if len(context.user_data["sentiment_history"]) > 10:
        context.user_data["sentiment_history"] = context.user_data["sentiment_history"][-10:]

    # Get response adjustments based on sentiment
    adjustments = sentiment_analyzer.get_response_adjustment(sentiment)

    # Log sentiment analysis
    logger.info(
        f"Sentiment detected: {sentiment['primary_emotion']} (intensity: {sentiment['intensity']})")

    # Generate AI response
    try:
        # Convert role to dictionary for the AI
        role_data = role.to_dict()

        # Add sentiment-based guidance to role context
        if "tone_guidance" in adjustments and adjustments["tone_guidance"]:
            role_data["tone_guidance"] = adjustments["tone_guidance"]

        # Adjust temperature based on sentiment
        temperature = adjustments.get("temperature", 0.7)
        if preferences["formality_level"] == "formal":
            # Reduce temperature for formal tone
            temperature = max(0.4, temperature - 0.2)
        elif preferences["formality_level"] == "casual":
            # Increase temperature for casual tone
            temperature = min(0.9, temperature + 0.1)

        # Generate response
        ai_response = await gemini_ai.generate_response(
            prompt=user_message,
            role_context=role_data,
            conversation_history=conversation_history,
            temperature=temperature,
            max_tokens=300 if preferences["response_length"] == "short" else
            800 if preferences["response_length"] == "medium" else 1500
        )

        # Save conversation to database
        await Conversation.add_message(
            user_id=user_id,
            role_id=db_user.current_role_id,
            user_message=user_message,
            bot_response=ai_response
        )

        # Extract memories from user message if memory is enabled
        if preferences["memory_enabled"]:
            # Create context for memory extraction
            user_context = {
                "name": update.effective_user.first_name,
                "current_role": role.name,
                "sentiment": sentiment["primary_emotion"] if sentiment else "neutral"
            }

            # Extract memories asynchronously (don't wait for completion)
            context.application.create_task(
                Memory.extract_memories_from_message(
                    user_id, user_message, user_context)
            )

        # Send response
        await update.message.reply_text(ai_response)

        # Voice responses are temporarily disabled due to timeout issues
        # if preferences.get("voice_responses_enabled", False):
        #     await send_voice_response(update, ai_response, preferences.get("language", "en"))

    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        await update.message.reply_text(
            "I'm having trouble connecting to my AI brain right now. Could you try again in a moment?"
        )


async def handle_role_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the role creation process.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    user_id = update.effective_user.id
    user_message = update.message.text

    step = context.user_data.get("role_creation_step", "name")
    new_role = context.user_data.get("new_role", {})

    # Create cancel button for all steps
    keyboard = [[InlineKeyboardButton(
        "❌ Cancel", callback_data="cancel_role_creation")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if step == "name":
        new_role["name"] = user_message
        context.user_data["role_creation_step"] = "description"
        context.user_data["new_role"] = new_role

        await update.message.reply_text(
            f"Great! The persona will be called \"{user_message}\".\n\n"
            f"Now, please provide a brief description of this persona.",
            reply_markup=reply_markup
        )

    elif step == "description":
        new_role["description"] = user_message
        context.user_data["role_creation_step"] = "personality"
        context.user_data["new_role"] = new_role

        await update.message.reply_text(
            f"Thanks! Now, describe the personality traits of this persona.\n\n"
            f"For example: \"Warm, empathetic, and supportive. Enjoys casual conversation and sharing experiences.\"",
            reply_markup=reply_markup
        )

    elif step == "personality":
        new_role["personality"] = user_message
        context.user_data["role_creation_step"] = "speaking_style"
        context.user_data["new_role"] = new_role

        await update.message.reply_text(
            f"Great! Now, describe how this persona speaks.\n\n"
            f"For example: \"Casual and conversational. Uses everyday language and occasional slang.\"",
            reply_markup=reply_markup
        )

    elif step == "speaking_style":
        new_role["speaking_style"] = user_message
        context.user_data["role_creation_step"] = "knowledge"
        context.user_data["new_role"] = new_role

        await update.message.reply_text(
            f"Almost done! What knowledge areas should this persona have?\n\n"
            f"For example: \"Daily life, popular culture, relationships, casual advice\"",
            reply_markup=reply_markup
        )

    elif step == "knowledge":
        new_role["knowledge_areas"] = user_message
        context.user_data["role_creation_step"] = "behaviors"
        context.user_data["new_role"] = new_role

        await update.message.reply_text(
            f"Last step! What behaviors should this persona exhibit?\n\n"
            f"For example: \"Asks follow-up questions, shares relatable anecdotes, offers encouragement\"",
            reply_markup=reply_markup
        )

    elif step == "behaviors":
        new_role["behaviors"] = user_message

        # Create and save the new role
        role = Role(
            name=new_role["name"],
            description=new_role["description"],
            personality=new_role["personality"],
            speaking_style=new_role["speaking_style"],
            knowledge_areas=new_role["knowledge_areas"],
            behaviors=user_message,
            is_custom=True,
            created_by=user_id
        )

        success = await role.save()

        if success and role.role_id:
            # Set as current role
            db_user = await User.get_user(user_id)
            if db_user:
                await db_user.set_current_role(role.role_id)

            await update.message.reply_text(
                f"Perfect! I've created the \"{new_role['name']}\" persona and set it as active.\n\n"
                f"You can now start chatting with me as this persona!"
            )
        else:
            await update.message.reply_text(
                f"I had trouble creating the new persona. Please try again later."
            )

        # Clear role creation state
        context.user_data["creating_role"] = False
        context.user_data["role_creation_step"] = None
        context.user_data["new_role"] = {}


async def handle_settings_change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the settings change process.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    user_id = update.effective_user.id
    user_message = update.message.text

    setting = context.user_data.get("changing_setting", "")

    if setting == "language":
        # Validate language code
        language = user_message.lower()
        valid_languages = ["en", "es", "fr", "de",
                           "it", "pt", "ru", "ja", "zh", "ar"]

        if language not in valid_languages:
            await update.message.reply_text(
                f"Sorry, I don't recognize that language code. Please enter one of: {', '.join(valid_languages)}"
            )
            return

        # Update preference
        await User.update_user_preferences(user_id, {"language": language})

        await update.message.reply_text(
            f"Language preference updated to {language}."
        )

    elif setting == "response_length":
        # Validate response length
        length = user_message.lower()
        valid_lengths = ["short", "medium", "long"]

        if length not in valid_lengths:
            await update.message.reply_text(
                f"Please choose one of: {', '.join(valid_lengths)}"
            )
            return

        # Update preference
        await User.update_user_preferences(user_id, {"response_length": length})

        await update.message.reply_text(
            f"Response length preference updated to {length}."
        )

    elif setting == "formality":
        # Validate formality level
        formality = user_message.lower()
        valid_formality = ["casual", "neutral", "formal"]

        if formality not in valid_formality:
            await update.message.reply_text(
                f"Please choose one of: {', '.join(valid_formality)}"
            )
            return

        # Update preference
        await User.update_user_preferences(user_id, {"formality_level": formality})

        await update.message.reply_text(
            f"Formality preference updated to {formality}."
        )

    # Clear setting change state
    context.user_data["changing_setting"] = False
