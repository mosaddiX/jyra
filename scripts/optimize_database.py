#!/usr/bin/env python
"""
Database optimization script for Jyra.

This script optimizes the SQLite database by running VACUUM and ANALYZE commands,
and provides statistics about the database.
"""

import os
import sys
import argparse
import asyncio
import sqlite3
from pathlib import Path

# Add the parent directory to the path so we can import jyra modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jyra.utils.config import DATABASE_PATH
from jyra.utils.logger import setup_logger
from jyra.db.connection import optimize_database, get_pool_stats, close_all_connections

# Set up logging
logger = setup_logger(__name__)


async def get_database_stats():
    """
    Get statistics about the database.
    
    Returns:
        Dict with database statistics
    """
    try:
        # Create a new connection
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get database size
        db_size = os.path.getsize(DATABASE_PATH)
        
        # Get table counts
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
        
        table_stats = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_stats[table] = count
        
        # Close the connection
        conn.close()
        
        # Get connection pool stats
        pool_stats = await get_pool_stats()
        
        return {
            "database_path": DATABASE_PATH,
            "database_size_bytes": db_size,
            "database_size_mb": db_size / (1024 * 1024),
            "tables": table_stats,
            "connection_pool": pool_stats
        }
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        return {"error": str(e)}


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Optimize the Jyra database")
    parser.add_argument("--stats-only", action="store_true", help="Only show database statistics without optimizing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    
    args = parser.parse_args()
    
    # Get database stats before optimization
    print("Getting database statistics...")
    before_stats = await get_database_stats()
    
    # Print database stats
    print("\nDatabase Statistics:")
    print(f"  Path: {before_stats['database_path']}")
    print(f"  Size: {before_stats['database_size_mb']:.2f} MB")
    print("\nTable Counts:")
    for table, count in before_stats['tables'].items():
        print(f"  {table}: {count} rows")
    
    if args.verbose:
        print("\nConnection Pool Statistics:")
        for key, value in before_stats['connection_pool'].items():
            print(f"  {key}: {value}")
    
    # If stats-only flag is set, exit here
    if args.stats_only:
        return
    
    # Optimize the database
    print("\nOptimizing database...")
    success = await optimize_database()
    
    if success:
        print("Database optimization completed successfully.")
        
        # Get database stats after optimization
        print("\nGetting updated database statistics...")
        after_stats = await get_database_stats()
        
        # Print size difference
        before_size = before_stats['database_size_mb']
        after_size = after_stats['database_size_mb']
        size_diff = before_size - after_size
        
        print(f"\nBefore optimization: {before_size:.2f} MB")
        print(f"After optimization: {after_size:.2f} MB")
        
        if size_diff > 0:
            print(f"Space saved: {size_diff:.2f} MB ({(size_diff / before_size) * 100:.1f}%)")
        else:
            print(f"Size change: {-size_diff:.2f} MB (database grew slightly)")
    else:
        print("Database optimization failed. Check the logs for details.")


if __name__ == "__main__":
    asyncio.run(main())
