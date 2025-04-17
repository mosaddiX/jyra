"""
Multi-modal message handlers for Jyra Telegram bot
"""

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from jyra.db.models.user import User
from jyra.db.models.role import Role
from jyra.db.models.conversation import Conversation
from jyra.ai.models.gemini_direct import GeminiAI
from jyra.ai.sentiment.sentiment_analyzer import SentimentAnalyzer
from jyra.ai.multimodal.image_processor import ImageProcessor
from jyra.ai.multimodal.speech_processor import SpeechProcessor
from jyra.ai.multimodal.tts_processor import TTSProcessor
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)

# Initialize AI model, sentiment analyzer, and multi-modal processors
gemini_ai = GeminiAI()
sentiment_analyzer = SentimentAnalyzer()
image_processor = ImageProcessor()
speech_processor = SpeechProcessor()
tts_processor = TTSProcessor()


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle photo messages.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    user_id = update.effective_user.id

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

    # Send typing action
    await update.message.chat.send_action(action="typing")

    try:
        # Get the photo file
        photo = update.message.photo[-1]  # Get the largest photo
        photo_file = await photo.get_file()
        photo_url = photo_file.file_path

        # Get caption if any
        caption = update.message.caption or "What do you see in this image?"

        # Download the photo
        photo_path = await image_processor.download_image(photo_url)

        # Process the image
        response = await image_processor.process_image(photo_path, caption)

        # Clean up the downloaded file
        if os.path.exists(photo_path):
            os.remove(photo_path)

        # Analyze sentiment of the response
        sentiment = await sentiment_analyzer.analyze_sentiment(response)

        # Get response adjustments based on sentiment
        adjustments = sentiment_analyzer.get_response_adjustment(sentiment)

        # Convert role to dictionary for the AI
        role_data = role.to_dict()
        # Add sentiment-based guidance to role context
        if "tone_guidance" in adjustments and adjustments["tone_guidance"]:
            role_data["tone_guidance"] = adjustments["tone_guidance"]
        # Generate a more personalized response based on the image analysis
        ai_response = await gemini_ai.generate_response(
            prompt=f"I sent you an image and you described it as: {response}. Please respond in character.",
            role_context=role_data,
            temperature=adjustments.get("temperature", 0.7),
            max_tokens=800
        )

        # Save conversation to database
        await Conversation.add_message(
            user_id=user_id,
            role_id=db_user.current_role_id,
            user_message=f"[IMAGE] {caption if caption else 'User sent an image.'}",
            bot_response=ai_response
        )

        # Send response
        await update.message.reply_text(ai_response)

        # Voice responses are temporarily disabled due to timeout issues
        # if preferences.get("voice_responses_enabled", False):
        #     await send_voice_response(update, ai_response, preferences.get("language", "en"))

    except Exception as e:
        logger.error(f"Error processing photo: {str(e)}")
        await update.message.reply_text(
            "I'm having trouble processing that image. Could you try again later?"
        )


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle voice messages.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    user_id = update.effective_user.id

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

    # Send typing action
    await update.message.chat.send_action(action="typing")

    try:
        # Get the voice file
        voice = update.message.voice
        voice_file = await voice.get_file()
        voice_url = voice_file.file_path

        # Download the voice message
        voice_path = await speech_processor.download_voice(voice_url)

        # Convert speech to text
        result = await speech_processor.speech_to_text(
            voice_path,
            language=preferences.get("language", "en-US")
        )

        # Clean up the downloaded file
        if os.path.exists(voice_path):
            os.remove(voice_path)

        if result["success"]:
            # Process the transcribed text
            user_message = result["text"]

            # Get conversation history
            conversation_history = await Conversation.get_conversation_history(
                user_id,
                role_id=db_user.current_role_id
            )

            # Analyze sentiment
            sentiment = await sentiment_analyzer.analyze_sentiment(user_message)

            # Get response adjustments based on sentiment
            adjustments = sentiment_analyzer.get_response_adjustment(sentiment)

            # Convert role to dictionary for the AI
            role_data = role.to_dict()

            # Add sentiment-based guidance to role context
            if "tone_guidance" in adjustments and adjustments["tone_guidance"]:
                role_data["tone_guidance"] = adjustments["tone_guidance"]

            # Generate response
            ai_response = await gemini_ai.generate_response(
                prompt=user_message,
                role_context=role_data,
                conversation_history=conversation_history,
                temperature=adjustments.get("temperature", 0.7),
                max_tokens=300 if preferences["response_length"] == "short" else
                800 if preferences["response_length"] == "medium" else 1500
            )

            # Save conversation to database
            await Conversation.add_message(
                user_id=user_id,
                role_id=db_user.current_role_id,
                user_message=f"[VOICE] {user_message}",
                bot_response=ai_response
            )

            # Send text response
            await update.message.reply_text(
                f"🎤 I heard: \"{user_message}\"\n\n{ai_response}"
            )

            # Voice responses are temporarily disabled due to timeout issues
            # if preferences.get("voice_responses_enabled", False):
            #     await send_voice_response(update, ai_response, preferences.get("language", "en"))

        else:
            # Speech recognition failed
            await update.message.reply_text(result["error"])

    except Exception as e:
        logger.error(f"Error processing voice message: {str(e)}")
        await update.message.reply_text(
            "I'm having trouble processing that voice message. Could you try again later?"
        )


async def send_voice_response(update: Update, text: str, language: str = "en") -> None:
    """
    Send a voice response.

    Args:
        update (Update): The update object
        text (str): Text to convert to speech
        language (str): Language code for TTS
    """
    try:
        # Send recording action
        await update.message.chat.send_action(action="record_voice")

        # Limit text length to avoid timeouts (max 500 characters)
        if len(text) > 500:
            # Truncate and add a note
            short_text = text[:497] + "..."
            logger.info(
                f"Truncated voice response from {len(text)} to 500 characters")
        else:
            short_text = text

        # Convert text to speech
        result = await tts_processor.text_to_speech(short_text, language)

        if result["success"]:
            # Send the voice message
            with open(result["file_path"], "rb") as audio:
                try:
                    await update.message.reply_voice(audio)
                    logger.info(f"Voice message sent successfully")
                except Exception as e:
                    logger.error(f"Error sending voice message: {str(e)}")

            # Clean up the audio file
            tts_processor.cleanup_file(result["file_path"])
        else:
            logger.error(f"TTS failed: {result['error']}")
    except Exception as e:
        logger.error(f"Error sending voice response: {str(e)}")


async def toggle_voice_responses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Toggle voice responses on/off.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    # Inform the user that voice responses are temporarily disabled
    await update.message.reply_text(
        "Voice responses are temporarily disabled due to technical limitations. \n\n"
        "We're working on improving this feature to provide full-length voice responses in the future. "
        "For now, you can still send voice messages and I'll transcribe them!"
    )
