"""
Migration to enhance the roles table with additional columns.
"""

import sqlite3
from jyra.utils.config import DATABASE_PATH
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


def migrate_roles_table():
    """
    Enhance the roles table with additional columns.
    """
    logger.info(f"Enhancing roles table in database at {DATABASE_PATH}")
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if the is_featured column exists
        cursor.execute("PRAGMA table_info(roles)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # Add is_featured column if it doesn't exist
        if "is_featured" not in column_names:
            logger.info("Adding is_featured column to roles table")
            cursor.execute("ALTER TABLE roles ADD COLUMN is_featured BOOLEAN DEFAULT 0")
        
        # Add is_popular column if it doesn't exist
        if "is_popular" not in column_names:
            logger.info("Adding is_popular column to roles table")
            cursor.execute("ALTER TABLE roles ADD COLUMN is_popular BOOLEAN DEFAULT 0")
        
        # Create indexes for the new columns
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_roles_is_featured ON roles (is_featured)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_roles_is_popular ON roles (is_popular)")
        
        conn.commit()
        conn.close()
        
        logger.info("Roles table enhancement complete")
        return True
        
    except Exception as e:
        logger.error(f"Error enhancing roles table: {str(e)}")
        return False


if __name__ == "__main__":
    migrate_roles_table()
