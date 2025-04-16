#!/usr/bin/env python
"""
Script to update the database schema for the enhanced memory system.
"""

from jyra.utils.config import DATABASE_PATH
import sqlite3
import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

# Now we can import from jyra

# Set up logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def update_memory_schema():
    """Update the database schema for the enhanced memory system."""
    try:
        # Check if database exists
        if not os.path.exists(DATABASE_PATH):
            logger.error(f"Database not found at {DATABASE_PATH}")
            return False

        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Check if memories table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='memories'")
        if not cursor.fetchone():
            logger.error("Memories table not found in database")
            conn.close()
            return False

        # Get current columns in memories table
        cursor.execute("PRAGMA table_info(memories)")
        columns = [column[1] for column in cursor.fetchall()]

        # Add new columns if they don't exist
        new_columns = {
            "category": "TEXT DEFAULT 'general'",
            "source": "TEXT DEFAULT 'explicit'",
            "context": "TEXT",
            "last_accessed": "TIMESTAMP"
        }

        for column, definition in new_columns.items():
            if column not in columns:
                logger.info(f"Adding column '{column}' to memories table")
                cursor.execute(
                    f"ALTER TABLE memories ADD COLUMN {column} {definition}")

        # Create memory_summaries table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_summaries (
            summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            summary TEXT,
            category TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        """)

        # Create indexes if they don't exist
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_category ON memories (category)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_source ON memories (source)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_memory_summaries_user_id ON memory_summaries (user_id)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_memory_summaries_category ON memory_summaries (category)")

        # Commit changes
        conn.commit()
        conn.close()

        logger.info("Memory schema updated successfully")
        return True

    except Exception as e:
        logger.error(f"Error updating memory schema: {str(e)}")
        return False


if __name__ == "__main__":
    # Create scripts directory if it doesn't exist
    Path("scripts").mkdir(exist_ok=True)

    # Update memory schema
    success = update_memory_schema()

    if success:
        print("✅ Memory schema updated successfully")
    else:
        print("❌ Error updating memory schema")
