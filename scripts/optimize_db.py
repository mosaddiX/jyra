#!/usr/bin/env python
"""
Database optimization script for Jyra
"""

import os
import sys
import sqlite3
import time
import argparse
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

try:
    from jyra.utils.config import DATABASE_PATH
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

    # Default database path
    DATABASE_PATH = os.path.join('data', 'jyra.db')

logger = setup_logger(__name__)


def optimize_database():
    """
    Optimize the SQLite database.
    """
    logger.info(f"Optimizing database at {DATABASE_PATH}")

    # Check if database exists
    if not os.path.exists(DATABASE_PATH):
        logger.error(f"Database not found at {DATABASE_PATH}")
        return False

    try:
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Get database size before optimization
        cursor.execute("PRAGMA page_count")
        page_count_before = cursor.fetchone()[0]
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        size_before = page_count_before * page_size / 1024 / 1024  # Size in MB

        logger.info(f"Database size before optimization: {size_before:.2f} MB")

        # Start timing
        start_time = time.time()

        # Run VACUUM to rebuild the database file
        logger.info("Running VACUUM...")
        cursor.execute("VACUUM")

        # Run ANALYZE to update statistics
        logger.info("Running ANALYZE...")
        cursor.execute("ANALYZE")

        # Optimize indexes
        logger.info("Optimizing indexes...")
        cursor.execute("PRAGMA optimize")

        # Get database size after optimization
        cursor.execute("PRAGMA page_count")
        page_count_after = cursor.fetchone()[0]
        size_after = page_count_after * page_size / 1024 / 1024  # Size in MB

        # Calculate time taken
        end_time = time.time()
        time_taken = end_time - start_time

        logger.info(f"Database size after optimization: {size_after:.2f} MB")
        logger.info(
            f"Space saved: {size_before - size_after:.2f} MB ({(1 - size_after / size_before) * 100:.2f}%)")
        logger.info(f"Optimization completed in {time_taken:.2f} seconds")

        # Close connection
        conn.close()

        return True
    except Exception as e:
        logger.error(f"Error optimizing database: {str(e)}")
        return False


def cleanup_old_conversations(days=30):
    """
    Clean up old conversations to reduce database size.

    Args:
        days (int): Number of days to keep conversations
    """
    logger.info(f"Cleaning up conversations older than {days} days")

    try:
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Delete old conversations
        cursor.execute(f"""
        DELETE FROM conversations
        WHERE timestamp < datetime('now', '-{days} days')
        """)

        # Get number of deleted rows
        deleted_count = cursor.rowcount

        # Commit changes
        conn.commit()

        logger.info(f"Deleted {deleted_count} old conversation messages")

        # Close connection
        conn.close()

        return deleted_count
    except Exception as e:
        logger.error(f"Error cleaning up old conversations: {str(e)}")
        return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Optimize the Jyra database")
    parser.add_argument("--cleanup", "-c", action="store_true",
                        help="Clean up old conversations")
    parser.add_argument("--days", "-d", type=int, default=30,
                        help="Number of days to keep conversations")

    args = parser.parse_args()

    if args.cleanup:
        cleanup_old_conversations(args.days)

    optimize_database()
