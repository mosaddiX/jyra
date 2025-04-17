"""
Database initialization for Jyra
"""

import os
import sqlite3
from pathlib import Path

from jyra.utils.config import DATABASE_PATH
from jyra.utils.logger import setup_logger
from jyra.db.migrations.enhance_memory_system import migrate_memory_system
from jyra.db.migrations.enhance_roles import migrate_roles_table

logger = setup_logger(__name__)


def init_db():
    """
    Initialize the SQLite database with the required tables.
    """
    # Create data directory if it doesn't exist
    db_path = Path(DATABASE_PATH)
    db_path.parent.mkdir(exist_ok=True)

    logger.info(f"Initializing database at {DATABASE_PATH}")

    # Connect to database (will create it if it doesn't exist)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        language_code TEXT,
        current_role_id INTEGER,
        is_admin BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create roles table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS roles (
        role_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        personality TEXT,
        speaking_style TEXT,
        knowledge_areas TEXT,
        behaviors TEXT,
        is_custom BOOLEAN DEFAULT 0,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create conversations table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS conversations (
        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        role_id INTEGER,
        user_message TEXT,
        bot_response TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (role_id) REFERENCES roles (role_id)
    )
    ''')

    # Create memories table with enhanced features
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memories (
        memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT,
        category TEXT DEFAULT 'general',
        importance INTEGER DEFAULT 1,
        source TEXT DEFAULT 'explicit',
        context TEXT,
        last_accessed TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')

    # Create memory_summaries table for long-term memory
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memory_summaries (
        summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        summary TEXT,
        category TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')

    # Create user_preferences table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_preferences (
        user_id INTEGER PRIMARY KEY,
        language TEXT DEFAULT 'en',
        response_length TEXT DEFAULT 'medium',
        formality_level TEXT DEFAULT 'casual',
        memory_enabled BOOLEAN DEFAULT 1,
        voice_responses_enabled BOOLEAN DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')

    # Create indexes for better performance
    logger.info("Creating database indexes...")

    # Indexes for conversations table
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations (user_id)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_conversations_role_id ON conversations (role_id)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations (timestamp)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_conversations_user_role ON conversations (user_id, role_id)
    ''')

    # Indexes for memories table
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories (user_id)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories (importance)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories (created_at)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_memories_category ON memories (category)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_memories_source ON memories (source)
    ''')

    # Indexes for memory_summaries table
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_memory_summaries_user_id ON memory_summaries (user_id)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_memory_summaries_category ON memory_summaries (category)
    ''')

    # Indexes for roles table
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_roles_created_by ON roles (created_by)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_roles_is_custom ON roles (is_custom)
    ''')

    # Indexes for users table
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_users_last_interaction ON users (last_interaction)
    ''')

    # Commit changes and close connection
    conn.commit()
    conn.close()

    logger.info("Database initialization complete")

    # Run migrations
    logger.info("Running database migrations...")
    migrate_memory_system()
    migrate_roles_table()
    logger.info("Database migrations complete")


if __name__ == "__main__":
    init_db()
