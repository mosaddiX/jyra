"""
Rate limiting middleware for Jyra.

This middleware applies rate limiting to user interactions with the bot.
"""

import logging
from typing import Callable, Dict, Any, Optional

from telegram import Update
from telegram.ext import CallbackContext

from jyra.utils.rate_limiter import RateLimiter
from jyra.utils.config import get_config

logger = logging.getLogger(__name__)

# Create a global rate limiter instance
admin_user_ids = [int(uid) for uid in get_config("ADMIN_USER_IDS", "").split(",") if uid]
RATE_LIMITER = RateLimiter(
    window_size=int(get_config("RATE_LIMIT_WINDOW", "60")),
    max_requests=int(get_config("RATE_LIMIT_MAX_REQUESTS", "20")),
    admin_user_ids=admin_user_ids
)

def rate_limit_middleware(func: Callable) -> Callable:
    """
    Middleware to apply rate limiting to bot commands and message handlers.
    
    Args:
        func (Callable): The handler function to wrap
        
    Returns:
        Callable: The wrapped handler function with rate limiting applied
    """
    async def wrapper(update: Update, context: CallbackContext) -> Any:
        # Skip rate limiting for updates without a user
        if not update.effective_user:
            return await func(update, context)
            
        user_id = update.effective_user.id
        is_limited, request_count, reset_time = RATE_LIMITER.is_rate_limited(user_id)
        
        if is_limited:
            logger.warning(f"Rate limit applied to user {user_id}. Reset in {reset_time}s.")
            await update.effective_message.reply_text(
                f"⚠️ You're sending messages too quickly. Please wait {reset_time} seconds before trying again."
            )
            return None
            
        # If close to the limit, warn the user
        if request_count >= RATE_LIMITER.max_requests * 0.8:
            logger.info(f"User {user_id} approaching rate limit: {request_count}/{RATE_LIMITER.max_requests}")
            
        # Proceed with the handler
        return await func(update, context)
        
    return wrapper
