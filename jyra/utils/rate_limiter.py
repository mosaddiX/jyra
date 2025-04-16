"""
Rate limiting module for Jyra.

This module provides functionality to limit the rate at which users can interact with the bot,
helping to prevent abuse and ensure fair usage of resources.
"""

import time
from collections import defaultdict
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    A rate limiter that restricts the number of requests a user can make within a time window.
    
    Attributes:
        user_requests (Dict[int, list]): Dictionary mapping user IDs to their request timestamps
        window_size (int): Time window in seconds
        max_requests (int): Maximum number of requests allowed in the window
        admin_user_ids (list): List of admin user IDs that bypass rate limiting
    """
    
    def __init__(self, window_size: int = 60, max_requests: int = 20, admin_user_ids: Optional[list] = None):
        """
        Initialize the rate limiter.
        
        Args:
            window_size (int): Time window in seconds (default: 60)
            max_requests (int): Maximum number of requests allowed in the window (default: 20)
            admin_user_ids (list, optional): List of admin user IDs that bypass rate limiting
        """
        self.user_requests = defaultdict(list)
        self.window_size = window_size
        self.max_requests = max_requests
        self.admin_user_ids = admin_user_ids or []
        
    def is_rate_limited(self, user_id: int) -> Tuple[bool, int, int]:
        """
        Check if a user is rate limited.
        
        Args:
            user_id (int): The user ID to check
            
        Returns:
            Tuple[bool, int, int]: A tuple containing:
                - Whether the user is rate limited (True if limited, False otherwise)
                - Number of requests made in the current window
                - Time in seconds until the rate limit resets
        """
        # Admin users bypass rate limiting
        if user_id in self.admin_user_ids:
            return False, 0, 0
            
        current_time = time.time()
        
        # Remove requests outside the current time window
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if current_time - req_time <= self.window_size
        ]
        
        # Count requests in the current window
        request_count = len(self.user_requests[user_id])
        
        # If under the limit, add the current request and allow
        if request_count < self.max_requests:
            self.user_requests[user_id].append(current_time)
            return False, request_count + 1, 0
            
        # Calculate time until oldest request expires
        if self.user_requests[user_id]:
            oldest_request = min(self.user_requests[user_id])
            reset_time = int(oldest_request + self.window_size - current_time) + 1
        else:
            reset_time = 0
            
        logger.warning(f"Rate limit exceeded for user {user_id}. {request_count} requests in {self.window_size}s window.")
        return True, request_count, reset_time
        
    def reset_for_user(self, user_id: int) -> None:
        """
        Reset the rate limit for a specific user.
        
        Args:
            user_id (int): The user ID to reset
        """
        if user_id in self.user_requests:
            del self.user_requests[user_id]
            logger.info(f"Rate limit reset for user {user_id}")
            
    def reset_all(self) -> None:
        """Reset rate limits for all users."""
        self.user_requests.clear()
        logger.info("Rate limits reset for all users")
        
    def update_limits(self, window_size: Optional[int] = None, max_requests: Optional[int] = None) -> None:
        """
        Update the rate limiting parameters.
        
        Args:
            window_size (int, optional): New time window in seconds
            max_requests (int, optional): New maximum number of requests allowed in the window
        """
        if window_size is not None:
            self.window_size = window_size
        if max_requests is not None:
            self.max_requests = max_requests
        logger.info(f"Rate limits updated: {self.max_requests} requests per {self.window_size}s")
