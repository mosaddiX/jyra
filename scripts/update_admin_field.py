#!/usr/bin/env python
"""
Script to update the database schema to add the is_admin field to the users table.
"""

import sqlite3
import os
import logging
from pathlib import Path

# Set up logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database path
DATABASE_PATH = "data/jyra.db"

def update_admin_field():
    """Update the database schema to add the is_admin field to the users table."""
    try:
        # Check if database exists
        if not os.path.exists(DATABASE_PATH):
            logger.error(f"Database not found at {DATABASE_PATH}")
            return False

        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            logger.error("Users table not found in database")
            conn.close()
            return False

        # Get current columns in users table
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]

        # Add is_admin column if it doesn't exist
        if "is_admin" not in columns:
            logger.info("Adding is_admin column to users table")
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")

        # Set admin status for the user ID from environment variable or default to your user ID
        admin_user_id = os.environ.get("ADMIN_USER_ID", "7670016870")  # Default to your user ID
        
        logger.info(f"Setting admin status for user {admin_user_id}")
        cursor.execute(
            "UPDATE users SET is_admin = 1 WHERE user_id = ?",
            (admin_user_id,)
        )

        # Commit changes
        conn.commit()
        conn.close()

        logger.info("Database schema updated successfully")
        return True

    except Exception as e:
        logger.error(f"Error updating database schema: {str(e)}")
        return False


if __name__ == "__main__":
    # Update database schema
    success = update_admin_field()
    
    if success:
        print("✅ Database schema updated successfully")
    else:
        print("❌ Error updating database schema")
