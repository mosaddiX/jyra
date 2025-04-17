"""
Update the database schema to add the voice_responses_enabled column
"""

import sqlite3
import os
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


def update_schema():
    """Update the database schema to add the voice_responses_enabled column"""
    try:
        # Connect to the database
        db_path = os.path.join("data", "jyra.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if the column already exists
        cursor.execute("PRAGMA table_info(user_preferences)")
        columns = [column[1] for column in cursor.fetchall()]

        if "voice_responses_enabled" not in columns:
            # Add the voice_responses_enabled column
            cursor.execute(
                "ALTER TABLE user_preferences ADD COLUMN voice_responses_enabled BOOLEAN DEFAULT 0"
            )
            conn.commit()
            logger.info(
                "Added voice_responses_enabled column to user_preferences table")
        else:
            logger.info("voice_responses_enabled column already exists")

        # Close the connection
        conn.close()

        return True
    except Exception as e:
        logger.error(f"Error updating database schema: {str(e)}")
        return False


if __name__ == "__main__":
    print("Updating database schema...")
    success = update_schema()
    if success:
        print("Database schema updated successfully!")
    else:
        print("Failed to update database schema. Check the logs for details.")
