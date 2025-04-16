"""
Response caching for AI models
"""

import json
import hashlib
import os
import time
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


class ResponseCache:
    """
    Cache for AI model responses to reduce API calls.
    """

    def __init__(self, cache_dir: str = "data/cache", max_age_seconds: int = 3600):
        """
        Initialize the response cache.

        Args:
            cache_dir (str): Directory to store cache files
            max_age_seconds (int): Maximum age of cache entries in seconds
        """
        self.cache_dir = Path(cache_dir)
        self.max_age_seconds = max_age_seconds

        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized response cache in {cache_dir}")

    def _generate_cache_key(self, prompt: str, role_context: Dict[str, Any], conversation_history: Optional[list] = None) -> str:
        """
        Generate a cache key for the given parameters.

        Args:
            prompt (str): The user's message
            role_context (Dict[str, Any]): Context about the current role
            conversation_history (Optional[list]): Previous messages

        Returns:
            str: Cache key
        """
        # Create a dictionary with all parameters
        cache_data = {
            "prompt": prompt,
            "role_context": role_context,
            "conversation_history": conversation_history or []
        }

        # Convert to JSON and hash
        cache_json = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_json.encode()).hexdigest()

    def get(self, prompt: str, role_context: Dict[str, Any], conversation_history: Optional[list] = None) -> Optional[str]:
        """
        Get a cached response if available.

        Args:
            prompt (str): The user's message
            role_context (Dict[str, Any]): Context about the current role
            conversation_history (Optional[list]): Previous messages

        Returns:
            Optional[str]: Cached response or None if not found
        """
        cache_key = self._generate_cache_key(
            prompt, role_context, conversation_history)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            # Read cache file
            with open(cache_file, "r") as f:
                cache_data = json.load(f)

            # Check if cache is expired
            if time.time() - cache_data["timestamp"] > self.max_age_seconds:
                logger.info(f"Cache expired for key {cache_key}")
                return None

            logger.info(f"Cache hit for key {cache_key}")
            return cache_data["response"]
        except Exception as e:
            logger.error(f"Error reading cache: {str(e)}")
            return None

    def set(self, prompt: str, role_context: Dict[str, Any], conversation_history: Optional[list], response: str) -> None:
        """
        Cache a response.

        Args:
            prompt (str): The user's message
            role_context (Dict[str, Any]): Context about the current role
            conversation_history (Optional[list]): Previous messages
            response (str): The response to cache
        """
        cache_key = self._generate_cache_key(
            prompt, role_context, conversation_history)
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            # Create cache data
            cache_data = {
                "prompt": prompt,
                "response": response,
                "timestamp": time.time()
            }

            # Write cache file
            with open(cache_file, "w") as f:
                json.dump(cache_data, f)

            logger.info(f"Cached response for key {cache_key}")
        except Exception as e:
            logger.error(f"Error writing cache: {str(e)}")

    def clear(self, max_age_seconds: Optional[int] = None) -> int:
        """
        Clear expired cache entries.

        Args:
            max_age_seconds (Optional[int]): Maximum age of cache entries to keep

        Returns:
            int: Number of cache entries cleared
        """
        if max_age_seconds is None:
            max_age_seconds = self.max_age_seconds

        cleared_count = 0
        current_time = time.time()

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                # Read cache file
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)

                # Check if cache is expired
                if current_time - cache_data["timestamp"] > max_age_seconds:
                    # Remove expired cache file
                    os.remove(cache_file)
                    cleared_count += 1
            except Exception as e:
                logger.error(f"Error clearing cache: {str(e)}")

        logger.info(f"Cleared {cleared_count} expired cache entries")
        return cleared_count
