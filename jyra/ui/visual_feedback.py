"""
Visual feedback utilities for the Jyra bot.

This module provides functions for displaying loading indicators,
error messages, and success/confirmation messages.
"""

from typing import Optional, Dict, Any, Callable, Awaitable
import asyncio
from telegram import Update, Message
from telegram.ext import ContextTypes

from jyra.ui.formatting import bold, italic, emoji_prefix
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)

# Loading indicator animations
LOADING_ANIMATIONS = {
    "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
    "line": ["—", "\\", "|", "/"],
    "pulse": ["□", "■"],
    "bounce": ["⠁", "⠂", "⠄", "⠠", "⠐", "⠈"],
    "moon": ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"],
    "clock": ["🕛", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚"]
}

# Default loading animation
DEFAULT_ANIMATION = "dots"

# Success indicators
SUCCESS_EMOJI = "✅"
ERROR_EMOJI = "❌"
WARNING_EMOJI = "⚠️"
INFO_EMOJI = "ℹ️"


async def show_loading_indicator(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str = "Processing",
    animation_type: str = DEFAULT_ANIMATION,
    duration: float = 0.5
) -> Message:
    """
    Show a loading indicator with an animated spinner.
    
    Args:
        update: The update object
        context: The context object
        text: The text to display with the loading indicator
        animation_type: The type of animation to use
        duration: The duration between animation frames in seconds
        
    Returns:
        The message object for the loading indicator
    """
    animation = LOADING_ANIMATIONS.get(animation_type, LOADING_ANIMATIONS[DEFAULT_ANIMATION])
    
    # Send initial message
    message = await update.message.reply_text(f"{animation[0]} {text}...")
    
    # Store the message in context for later reference
    context.user_data["loading_indicator"] = {
        "message_id": message.message_id,
        "chat_id": message.chat_id,
        "text": text,
        "animation": animation,
        "current_frame": 0,
        "is_running": True
    }
    
    # Start animation in background
    asyncio.create_task(
        _animate_loading_indicator(context, message, text, animation, duration)
    )
    
    return message


async def _animate_loading_indicator(
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    text: str,
    animation: list,
    duration: float
) -> None:
    """
    Animate the loading indicator.
    
    Args:
        context: The context object
        message: The message to animate
        text: The text to display
        animation: The animation frames
        duration: The duration between frames
    """
    frame = 0
    
    try:
        while context.user_data.get("loading_indicator", {}).get("is_running", False):
            frame = (frame + 1) % len(animation)
            await message.edit_text(f"{animation[frame]} {text}...")
            await asyncio.sleep(duration)
    except Exception as e:
        logger.error(f"Error in loading animation: {str(e)}")


async def stop_loading_indicator(
    context: ContextTypes.DEFAULT_TYPE,
    success: bool = True,
    result_text: Optional[str] = None
) -> None:
    """
    Stop the loading indicator and show a result message.
    
    Args:
        context: The context object
        success: Whether the operation was successful
        result_text: The text to display as the result
    """
    loading_data = context.user_data.get("loading_indicator")
    
    if not loading_data:
        return
    
    # Stop the animation
    loading_data["is_running"] = False
    
    # Get the message
    chat_id = loading_data["chat_id"]
    message_id = loading_data["message_id"]
    original_text = loading_data["text"]
    
    # Determine result text
    if result_text is None:
        result_text = f"{original_text} completed" if success else f"{original_text} failed"
    
    # Add emoji
    emoji = SUCCESS_EMOJI if success else ERROR_EMOJI
    
    try:
        # Update the message
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"{emoji} {result_text}"
        )
    except Exception as e:
        logger.error(f"Error stopping loading indicator: {str(e)}")
    
    # Clean up
    context.user_data.pop("loading_indicator", None)


async def with_loading_indicator(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    func: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[Any]],
    loading_text: str = "Processing",
    success_text: str = None,
    error_text: str = None,
    animation_type: str = DEFAULT_ANIMATION
) -> Any:
    """
    Execute a function with a loading indicator.
    
    Args:
        update: The update object
        context: The context object
        func: The async function to execute
        loading_text: The text to display while loading
        success_text: The text to display on success
        error_text: The text to display on error
        animation_type: The type of animation to use
        
    Returns:
        The result of the function
    """
    # Show loading indicator
    await show_loading_indicator(
        update, context, loading_text, animation_type
    )
    
    try:
        # Execute the function
        result = await func(update, context)
        
        # Stop loading indicator with success
        await stop_loading_indicator(
            context, True, success_text
        )
        
        return result
    except Exception as e:
        logger.error(f"Error in function with loading indicator: {str(e)}")
        
        # Stop loading indicator with error
        error_message = error_text or f"Error: {str(e)}"
        await stop_loading_indicator(
            context, False, error_message
        )
        
        # Re-raise the exception
        raise


async def show_success_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    details: Optional[str] = None
) -> Message:
    """
    Show a success message.
    
    Args:
        update: The update object
        context: The context object
        text: The success message text
        details: Optional details to display
        
    Returns:
        The message object
    """
    message = f"{SUCCESS_EMOJI} {bold(text)}"
    
    if details:
        message += f"\n\n{details}"
    
    return await update.message.reply_text(message, parse_mode='HTML')


async def show_error_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    details: Optional[str] = None
) -> Message:
    """
    Show an error message.
    
    Args:
        update: The update object
        context: The context object
        text: The error message text
        details: Optional details to display
        
    Returns:
        The message object
    """
    message = f"{ERROR_EMOJI} {bold(text)}"
    
    if details:
        message += f"\n\n{details}"
    
    return await update.message.reply_text(message, parse_mode='HTML')


async def show_warning_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    details: Optional[str] = None
) -> Message:
    """
    Show a warning message.
    
    Args:
        update: The update object
        context: The context object
        text: The warning message text
        details: Optional details to display
        
    Returns:
        The message object
    """
    message = f"{WARNING_EMOJI} {bold(text)}"
    
    if details:
        message += f"\n\n{details}"
    
    return await update.message.reply_text(message, parse_mode='HTML')


async def show_info_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    details: Optional[str] = None
) -> Message:
    """
    Show an information message.
    
    Args:
        update: The update object
        context: The context object
        text: The information message text
        details: Optional details to display
        
    Returns:
        The message object
    """
    message = f"{INFO_EMOJI} {bold(text)}"
    
    if details:
        message += f"\n\n{details}"
    
    return await update.message.reply_text(message, parse_mode='HTML')


async def show_confirmation_dialog(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    confirm_text: str = "Confirm",
    cancel_text: str = "Cancel",
    confirm_callback: str = "confirm",
    cancel_callback: str = "cancel"
) -> Message:
    """
    Show a confirmation dialog with confirm/cancel buttons.
    
    Args:
        update: The update object
        context: The context object
        text: The confirmation message text
        confirm_text: The text for the confirm button
        cancel_text: The text for the cancel button
        confirm_callback: The callback data for the confirm button
        cancel_callback: The callback data for the cancel button
        
    Returns:
        The message object
    """
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = [
        [
            InlineKeyboardButton(f"✅ {confirm_text}", callback_data=confirm_callback),
            InlineKeyboardButton(f"❌ {cancel_text}", callback_data=cancel_callback)
        ]
    ]
    
    return await update.message.reply_text(
        f"{WARNING_EMOJI} {bold(text)}\n\nPlease confirm or cancel:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
