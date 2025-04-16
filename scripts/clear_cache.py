#!/usr/bin/env python
"""
Cache clearing script for Jyra
"""

import os
import sys
import argparse
import shutil
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

try:
    from jyra.ai.cache.response_cache import ResponseCache
    from jyra.ai.models.gemini_direct import GeminiAI
    from jyra.utils.logger import setup_logger
except ImportError:
    # Fallback if jyra module is not available
    import logging

    def setup_logger(name):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger

    # Dummy ResponseCache class for fallback
    class ResponseCache:
        def __init__(self, cache_dir="data/cache", max_age_seconds=3600):
            self.cache_dir = Path(cache_dir)
            self.max_age_seconds = max_age_seconds

    # Dummy GeminiAI class for fallback
    class GeminiAI:
        def __init__(self, use_cache=True):
            self.use_cache = use_cache
            if use_cache:
                self.cache = ResponseCache()

        def clear_cache(self, max_age_seconds=None):
            return 0

logger = setup_logger(__name__)


def clear_cache(max_age_hours=None, force=False):
    """
    Clear the response cache.

    Args:
        max_age_hours (int): Maximum age of cache entries in hours
        force (bool): Whether to force clear all cache entries
    """
    cache_dir = Path("data/cache")

    if force:
        logger.info("Force clearing all cache entries")

        if os.path.exists(cache_dir):
            try:
                # Count files before deletion
                file_count = sum(1 for _ in cache_dir.glob("*.json"))

                # Delete all cache files individually instead of removing the directory
                deleted_count = 0
                for cache_file in cache_dir.glob("*.json"):
                    try:
                        os.remove(cache_file)
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Error deleting {cache_file}: {str(e)}")

                logger.info(f"Deleted {deleted_count} cache entries")
                return deleted_count
            except Exception as e:
                logger.error(f"Error clearing cache: {str(e)}")
                return 0
        else:
            logger.info("Cache directory does not exist, nothing to clear")
            return 0
    else:
        logger.info(f"Clearing cache entries older than {max_age_hours} hours")

        # Initialize the AI model with cache
        model = GeminiAI(use_cache=True)

        # Convert hours to seconds
        max_age_seconds = max_age_hours * 3600 if max_age_hours else None

        # Clear the cache
        cleared_count = model.clear_cache(max_age_seconds)

        logger.info(f"Cleared {cleared_count} cache entries")
        return cleared_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Clear the Jyra response cache")
    parser.add_argument("--age", "-a", type=int,
                        help="Maximum age of cache entries in hours")
    parser.add_argument("--force", "-f", action="store_true",
                        help="Force clear all cache entries")

    args = parser.parse_args()

    clear_cache(args.age, args.force)
