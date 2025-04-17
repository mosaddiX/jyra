"""
Memory maintenance tasks for Jyra.

This module contains tasks for maintaining the memory system.
"""

import asyncio
from typing import List, Dict, Any, Optional

from jyra.ai.memory_manager import memory_manager
from jyra.ai.decay.memory_decay import memory_decay
from jyra.db.models.user import User
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


async def run_memory_maintenance_for_all_users():
    """
    Run memory maintenance for all users.

    This includes:
    - Memory consolidation
    - Cleaning up expired memories
    - Updating memory importance based on usage
    """
    try:
        # Get all users
        users = await User.get_all_users()

        if not users:
            logger.info("No users found for memory maintenance")
            return

        logger.info(f"Running memory maintenance for {len(users)} users")

        for user in users:
            try:
                # Run memory maintenance for this user
                results = await memory_manager.run_memory_maintenance(user.user_id)

                if results.get("consolidated_memories", 0) > 0:
                    logger.info(
                        f"Consolidated {results['consolidated_memories']} memories for user {user.user_id}")

                # Apply memory decay
                decay_results = await memory_decay.apply_decay_to_user_memories(
                    user_id=user.user_id,
                    decay_factor=0.9,  # Default decay factor
                    min_age_days=30,   # Default minimum age
                    max_decay_per_run=5  # Limit per maintenance run
                )

                if decay_results.get("decayed_count", 0) > 0:
                    logger.info(
                        f"Decayed {decay_results['decayed_count']} memories for user {user.user_id}")

            except Exception as e:
                logger.error(
                    f"Error running memory maintenance for user {user.user_id}: {str(e)}")
                continue

        logger.info("Memory maintenance completed for all users")

    except Exception as e:
        logger.error(f"Error running memory maintenance: {str(e)}")


async def schedule_memory_maintenance(interval_hours: int = 24):
    """
    Schedule memory maintenance to run periodically.

    Args:
        interval_hours (int): Interval in hours between maintenance runs
    """
    while True:
        try:
            # Run maintenance
            await run_memory_maintenance_for_all_users()

            # Wait for the next interval
            await asyncio.sleep(interval_hours * 3600)

        except Exception as e:
            logger.error(f"Error in memory maintenance scheduler: {str(e)}")
            # Wait a bit before retrying
            await asyncio.sleep(3600)


def start_memory_maintenance_scheduler():
    """
    Start the memory maintenance scheduler in the background.
    """
    # Create a background task for memory maintenance
    # We'll use a separate event loop to avoid conflicts with the main application
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in the main event loop, create a task
            asyncio.create_task(schedule_memory_maintenance())
            logger.info(
                "Memory maintenance scheduler started as background task")
        else:
            # This shouldn't happen, but just in case
            loop.create_task(schedule_memory_maintenance())
            logger.info("Memory maintenance scheduler started")
    except Exception as e:
        logger.error(f"Failed to start memory maintenance scheduler: {str(e)}")
