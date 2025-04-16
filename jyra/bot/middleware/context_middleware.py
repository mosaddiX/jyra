"""
Context middleware for Jyra.

This middleware adds conversation context to the bot's handlers.
"""

import logging
from typing import Callable, Dict, Any, Optional

from telegram import Update
from telegram.ext import CallbackContext

from jyra.db.models.user import User
from jyra.db.models.conversation import Conversation

logger = logging.getLogger(__name__)

def context_middleware(func: Callable) -> Callable:
    """
    Middleware to add user and conversation context to bot handlers.
    
    Args:
        func (Callable): The handler function to wrap
        
    Returns:
        Callable: The wrapped handler function with context added
    """
    async def wrapper(update: Update, context: CallbackContext) -> Any:
        # Skip context for updates without a user
        if not update.effective_user:
            return await func(update, context)
            
        user_id = update.effective_user.id
        
        # Get or create user
        user = User.get_or_create(
            telegram_id=user_id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name,
            last_name=update.effective_user.last_name
        )
        
        # Add user to context
        context.user_data["user"] = user
        
        # Get conversation history
        conversation = Conversation.get_recent_for_user(user_id)
        context.user_data["conversation"] = conversation
        
        logger.debug(f"Context middleware: Added user {user_id} and conversation context")
        
        # Proceed with the handler
        return await func(update, context)
        
    return wrapper
