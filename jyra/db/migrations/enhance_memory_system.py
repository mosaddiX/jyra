"""
Database migration to enhance the memory system.

This script adds new tables and columns to support enhanced memory features:
- Memory relationships
- Memory tags
- Memory expiration
- Memory confidence levels
- Memory consolidation tracking
"""

import sqlite3
import os
from pathlib import Path

from jyra.utils.config import DATABASE_PATH
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


def migrate_memory_system():
    """
    Enhance the memory system with new tables and columns.
    """
    logger.info(f"Enhancing memory system in database at {DATABASE_PATH}")

    # Connect to database
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Add new columns to memories table
    try:
        # Check if confidence column exists
        cursor.execute("PRAGMA table_info(memories)")
        columns = [column[1] for column in cursor.fetchall()]

        # Add confidence column if it doesn't exist
        if "confidence" not in columns:
            logger.info("Adding confidence column to memories table")
            cursor.execute(
                "ALTER TABLE memories ADD COLUMN confidence REAL DEFAULT 1.0")

        # Add expiration column if it doesn't exist
        if "expires_at" not in columns:
            logger.info("Adding expires_at column to memories table")
            cursor.execute(
                "ALTER TABLE memories ADD COLUMN expires_at TIMESTAMP")

        # Add recall_count column if it doesn't exist
        if "recall_count" not in columns:
            logger.info("Adding recall_count column to memories table")
            cursor.execute(
                "ALTER TABLE memories ADD COLUMN recall_count INTEGER DEFAULT 0")

        # Add last_reinforced column if it doesn't exist
        if "last_reinforced" not in columns:
            logger.info("Adding last_reinforced column to memories table")
            cursor.execute(
                "ALTER TABLE memories ADD COLUMN last_reinforced TIMESTAMP")

        # Add is_consolidated column if it doesn't exist
        if "is_consolidated" not in columns:
            logger.info("Adding is_consolidated column to memories table")
            cursor.execute(
                "ALTER TABLE memories ADD COLUMN is_consolidated BOOLEAN DEFAULT 0")
    except sqlite3.OperationalError as e:
        logger.error(f"Error adding columns to memories table: {str(e)}")

    # Create memory_tags table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memory_tags (
        tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        tag_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        UNIQUE(user_id, tag_name)
    )
    ''')

    # Create memory_tag_associations table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memory_tag_associations (
        memory_id INTEGER,
        tag_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (memory_id, tag_id),
        FOREIGN KEY (memory_id) REFERENCES memories (memory_id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES memory_tags (tag_id) ON DELETE CASCADE
    )
    ''')

    # Create memory_relationships table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memory_relationships (
        relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_memory_id INTEGER,
        target_memory_id INTEGER,
        relationship_type TEXT,
        strength REAL DEFAULT 1.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (source_memory_id) REFERENCES memories (memory_id) ON DELETE CASCADE,
        FOREIGN KEY (target_memory_id) REFERENCES memories (memory_id) ON DELETE CASCADE
    )
    ''')

    # Create memory_consolidation_log table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memory_consolidation_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        source_memories TEXT,
        consolidated_memory_id INTEGER,
        consolidation_type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (consolidated_memory_id) REFERENCES memories (memory_id)
    )
    ''')

    # Create memory_embeddings table for semantic search
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memory_embeddings (
        memory_id INTEGER PRIMARY KEY,
        embedding BLOB NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (memory_id) REFERENCES memories (memory_id) ON DELETE CASCADE
    )
    ''')

    # Create indexes for better performance
    logger.info("Creating indexes for new memory tables...")

    # Indexes for memory_tags table
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_memory_tags_user_id ON memory_tags (user_id)
    ''')

    # Indexes for memory_tag_associations table
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_memory_tag_associations_tag_id ON memory_tag_associations (tag_id)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_memory_tag_associations_memory_id ON memory_tag_associations (memory_id)
    ''')

    # Indexes for memory_relationships table
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_memory_relationships_source ON memory_relationships (source_memory_id)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_memory_relationships_target ON memory_relationships (target_memory_id)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_memory_relationships_type ON memory_relationships (relationship_type)
    ''')

    # Indexes for memory_consolidation_log table
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_memory_consolidation_log_user_id ON memory_consolidation_log (user_id)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_memory_consolidation_log_consolidated_memory_id ON memory_consolidation_log (consolidated_memory_id)
    ''')

    # Indexes for memory_embeddings table
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_memory_embeddings_memory_id ON memory_embeddings (memory_id)
    ''')

    # Add indexes for new columns in memories table
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_memories_confidence ON memories (confidence)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_memories_expires_at ON memories (expires_at)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_memories_recall_count ON memories (recall_count)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_memories_is_consolidated ON memories (is_consolidated)
    ''')

    # Commit changes and close connection
    conn.commit()
    conn.close()

    logger.info("Memory system enhancement complete")


if __name__ == "__main__":
    migrate_memory_system()
