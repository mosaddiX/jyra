"""
Database connection management for Jyra.

This module provides functions for managing database connections,
with proper error handling and connection pooling.
"""

import sqlite3
import asyncio
from typing import Any, Dict, List, Tuple, Optional, Union, Callable
from functools import wraps
from contextlib import contextmanager

from jyra.utils.config import DATABASE_PATH
from jyra.utils.exceptions import (
    DatabaseConnectionError, DatabaseQueryError, DatabaseIntegrityError
)
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)

# Connection pool size
MAX_CONNECTIONS = 5

# Connection pool
_connection_pool = []
_connection_pool_lock = asyncio.Lock()

# Connection pool statistics
_pool_stats = {
    "created": 0,
    "reused": 0,
    "closed": 0,
    "errors": 0
}


@contextmanager
def get_connection():
    """
    Get a database connection from the pool or create a new one.

    Returns:
        A SQLite connection object

    Raises:
        DatabaseConnectionError: If the connection fails
    """
    connection = None
    try:
        # Try to get a connection from the pool
        if _connection_pool:
            connection = _connection_pool.pop()
            _pool_stats["reused"] += 1
            logger.debug(
                f"Reused database connection from pool. Pool size: {len(_connection_pool)}")
        else:
            # Create a new connection
            try:
                connection = sqlite3.connect(DATABASE_PATH)
                # Enable foreign keys
                connection.execute("PRAGMA foreign_keys = ON")
                # Configure connection
                connection.row_factory = sqlite3.Row
                _pool_stats["created"] += 1
                logger.debug(
                    f"Created new database connection. Total created: {_pool_stats['created']}")
            except sqlite3.Error as e:
                _pool_stats["errors"] += 1
                logger.error(f"Database connection error: {str(e)}")
                raise DatabaseConnectionError(str(e))

        # Yield the connection
        yield connection

        # Return the connection to the pool
        if len(_connection_pool) < MAX_CONNECTIONS:
            _connection_pool.append(connection)
            logger.debug(
                f"Returned connection to pool. Pool size: {len(_connection_pool)}")
        else:
            connection.close()
            _pool_stats["closed"] += 1
            logger.debug(
                f"Closed connection (pool full). Total closed: {_pool_stats['closed']}")
    except Exception as e:
        # Close the connection on error
        if connection:
            connection.close()
            _pool_stats["closed"] += 1
            _pool_stats["errors"] += 1
            logger.debug(
                f"Closed connection due to error. Total errors: {_pool_stats['errors']}")
        raise e


def execute_query(query: str, params: Tuple = (), fetch_all: bool = False) -> Union[List[Dict[str, Any]], Dict[str, Any], int]:
    """
    Execute a SQL query and return the results.

    Args:
        query: The SQL query to execute
        params: The parameters for the query
        fetch_all: Whether to fetch all results or just one

    Returns:
        The query results or the number of affected rows

    Raises:
        DatabaseQueryError: If the query fails
        DatabaseIntegrityError: If there's a database integrity error
    """
    with get_connection() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)

            # Check if this is a SELECT query
            if query.strip().upper().startswith("SELECT"):
                if fetch_all:
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
                else:
                    row = cursor.fetchone()
                    return dict(row) if row else None
            else:
                # For INSERT, UPDATE, DELETE queries
                conn.commit()
                return cursor.rowcount
        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise DatabaseIntegrityError(str(e))
        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseQueryError(query, str(e))


async def execute_query_async(query: str, params: Tuple = (), fetch_all: bool = False) -> Union[List[Dict[str, Any]], Dict[str, Any], int]:
    """
    Execute a SQL query asynchronously and return the results.

    Args:
        query: The SQL query to execute
        params: The parameters for the query
        fetch_all: Whether to fetch all results or just one

    Returns:
        The query results or the number of affected rows

    Raises:
        DatabaseQueryError: If the query fails
        DatabaseIntegrityError: If there's a database integrity error
    """
    # Use a thread pool to execute the query asynchronously
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, execute_query, query, params, fetch_all
    )


def transaction(func: Callable) -> Callable:
    """
    Decorator to execute a function in a database transaction.

    Args:
        func: The function to decorate

    Returns:
        The decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with get_connection() as conn:
            try:
                result = func(conn, *args, **kwargs)
                conn.commit()
                return result
            except Exception as e:
                conn.rollback()
                raise e

    return wrapper


async def async_transaction(func: Callable) -> Callable:
    """
    Decorator to execute an async function in a database transaction.

    Args:
        func: The function to decorate

    Returns:
        The decorated function
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()

        # Define a function to run in the thread pool
        def run_in_transaction():
            with get_connection() as conn:
                try:
                    result = func(conn, *args, **kwargs)
                    conn.commit()
                    return result
                except Exception as e:
                    conn.rollback()
                    raise e

        # Run the function in a thread pool
        return await loop.run_in_executor(None, run_in_transaction)

    return wrapper


def close_all_connections():
    """
    Close all connections in the connection pool.
    """
    global _connection_pool
    closed_count = len(_connection_pool)
    for conn in _connection_pool:
        conn.close()
    _connection_pool = []
    _pool_stats["closed"] += closed_count
    logger.info(
        f"All database connections closed ({closed_count} connections)")


async def get_pool_stats():
    """
    Get statistics about the connection pool.

    Returns:
        Dict with connection pool statistics
    """
    return {
        "current_pool_size": len(_connection_pool),
        "max_pool_size": MAX_CONNECTIONS,
        "connections_created": _pool_stats["created"],
        "connections_reused": _pool_stats["reused"],
        "connections_closed": _pool_stats["closed"],
        "connection_errors": _pool_stats["errors"]
    }


async def optimize_database():
    """
    Optimize the database by running VACUUM and analyzing tables.

    Returns:
        True if successful, False otherwise
    """
    try:
        # First close all connections
        close_all_connections()

        # Create a new connection for optimization
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Run VACUUM to defragment the database
        logger.info("Running VACUUM on database...")
        cursor.execute("VACUUM")

        # Analyze tables for query optimization
        logger.info("Analyzing database tables...")
        cursor.execute("ANALYZE")

        # Close the connection
        conn.close()

        logger.info("Database optimization completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error optimizing database: {str(e)}")
        return False
